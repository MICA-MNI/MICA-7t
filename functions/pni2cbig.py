#!/usr/bin/env python3
"""
Created on April 3, 2026
@author: rcruces

Prepares the files from PNI to CBIG ingestion.
Convert CBIG XLS to BIDS participants files and optionally remap PNI dataset

This script reads a CBIG Excel file, extracts participant metadata from the
"CBIG_data-for ingestion" sheet, and generates BIDS-compliant
`participants.tsv` and `participants.json`. Optionally, it copies imaging data
from an existing PNI BIDS dataset while renaming subject identifiers from
`participant_id` to `PSCID`.

Parameters
----------
--cbig_xls : str
    Glob pattern matching a CBIG `.xls` file (expects a single match).
--out : str
    Output directory for BIDS files.
--pni : str, optional
    Path to a PNI BIDS dataset. If provided, selected files are copied and
    subject IDs are remapped.

Behavior
--------
- Renames columns to BIDS conventions and prefixes `participant_id` with "sub-".
- Selects and orders key participant fields.
- Writes:
    * participants.tsv
    * participants.json
- If `--pni` is set:
    * Copies dataset-level files.
    * Copies anat (*MP2RAGE*, *T1map*, *UNIT1*), fmap (*acq-fmri_dir-*_epi*),
      and func (*task-rest_echo-*_bold*) files across all sessions.
    * Preserves directory structure while replacing subject IDs with PSCID.

Raises
------
FileNotFoundError
    If no XLS file matches the pattern.
ValueError
    If multiple XLS files match the pattern.

Notes
-----
Missing subjects in the PNI dataset are skipped with a warning.

Example
-------
python script.py --cbig_xls "CBIG_data-*.xls" --out ./out --pni /data/pni
"""

import os
import glob
import json
import argparse
import shutil
import subprocess
import pandas as pd
import time
import tempfile
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def progress_bar(iterable, prefix="", length=40):
    total = len(iterable)
    start_time = time.time()

    for i, item in enumerate(iterable, 1):
        elapsed = time.time() - start_time
        percent = i / total

        filled = int(length * percent)
        bar = "█" * filled + "-" * (length - filled)

        eta = (elapsed / i) * (total - i) if i > 0 else 0

        sys.stdout.write(
            f"\r{prefix} |{bar}| {i}/{total} "
            f"[{percent*100:5.1f}%] "
            f"ETA: {eta:6.1f}s"
        )
        sys.stdout.flush()

        yield item

    sys.stdout.write("\n")

def copy_if_exists(src, dst):
    if os.path.exists(src):
        shutil.copy2(src, dst)

def run_bids_validator(bids_dir):
    """
    Run the BIDS validator using deno and save output to file.
    """

    def run_command(command_list):
        try:
            print(f"Running command: {' '.join(command_list)}")
            subprocess.run(command_list, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running command: {e}")

    print("Running BIDS validator ...")

    command = [
        "deno",
        "run",
        "--allow-write",
        "-ERN",
        "jsr:@bids/validator",
        bids_dir,
        "--ignoreWarnings",
        "--outfile",
        f"{bids_dir}/bids_validator_output.txt",
    ]

    run_command(command)


def copy_and_rename_file(src_file, src_sub, dst_sub, out_dir, pni_dir):
    """
    Copy file preserving structure but replacing subject ID in:
    - directory path
    - filename
    """
    rel_path = os.path.relpath(src_file, pni_dir)

    # Replace subject in path + filename
    rel_path_new = rel_path.replace(src_sub, dst_sub)

    dst_file = os.path.join(out_dir, rel_path_new)

    os.makedirs(os.path.dirname(dst_file), exist_ok=True)

    shutil.copy2(src_file, dst_file)


def process_cbig_xls(cbig_xls_path, out_dir, pni_dir=None):
    # Resolve file
    files = glob.glob(cbig_xls_path)
    if len(files) == 0:
        raise FileNotFoundError(f"No file matches pattern: {cbig_xls_path}")
    if len(files) > 1:
        raise ValueError(f"Multiple files match pattern: {files}")

    xls_file = files[0]

    # Read Excel
    df = pd.read_excel(xls_file, sheet_name="CBIG_data-for_ingestion")

    # Rename columns
    df = df.rename(columns={
        "External Study Identifiers": "participant_id",
        "Entity Type": "entity",
        "Participant Status": "status",
        "Date of registration": "registration"
    })

    # Add sub-
    df["participant_id"] = df["participant_id"].astype(str).apply(lambda x: f"sub-{x}")

    # Select columns
    df = df[
        [
            "participant_id",
            "PSCID",
            "DCCID",
            "Sex",
            "Age",
            "registration",
            "Site",
            "entity",
            "status",
            "Diagnosis"
        ]
    ]

    # Rename to lowercase where needed
    df = df.rename(columns={
        "Sex": "sex",
        "Age": "age",
        "Site": "site",
        "Diagnosis": "diagnosis"
    })

    # Reorder
    df = df[
        [
            "participant_id",
            "PSCID",
            "DCCID",
            "sex",
            "age",
            "registration",
            "site",
            "entity",
            "status",
            "diagnosis"
        ]
    ]

    os.makedirs(out_dir, exist_ok=True)

    # Save TSV
    df.to_csv(os.path.join(out_dir, "participants.tsv"), sep="\t", index=False)

    # Save JSON
    participants_json = {
        "participant_id": {
            "LongName": "Participant identification label",
            "Description": "Assigned identification number for a subject (without 'sub-' prefix in source data)."
        },
        "PSCID": {"LongName": "PSCID", "Description": "Participant Study Code Identifier."},
        "DCCID": {"LongName": "DCCID", "Description": "Data Coordinating Center Identifier."},
        "sex": {"LongName": "Sex", "Description": "Biological sex."},
        "age": {"LongName": "Age", "Description": "Age at registration."},
        "registration": {"LongName": "Date of registration", "Description": "Registration date."},
        "site": {"LongName": "Site", "Description": "Collection site."},
        "entity": {"LongName": "Entity Type", "Description": "Entity classification."},
        "status": {"LongName": "Participant Status", "Description": "Participant status."},
        "diagnosis": {"LongName": "Diagnosis", "Description": "Diagnosis group."}
    }

    with open(os.path.join(out_dir, "participants.json"), "w") as f:
        json.dump(participants_json, f, indent=4)

    # =========================
    # PNI COPY LOGIC
    # =========================
    if pni_dir:

        print("1. Copying PNI dataset...")
        for fname in [
            "dataset_description.json",
            "README",
            "CITATION.cff",
            "task-rest_bold.json",
            ".bidsignore",
        ]:
            copy_if_exists(os.path.join(pni_dir, fname), os.path.join(out_dir, fname))

        print("2. Mapping individual files...")
        sub_map = {
            row["participant_id"]: f"sub-{row['PSCID']}"
            for _, row in df.iterrows()
        }

        selected_files: list[str] = []
        files_per_sub: dict[str, list[str]] = {sub: [] for sub in sub_map}

        for root, _, files in os.walk(pni_dir):
            for f in files:
                rel_path  = os.path.relpath(os.path.join(root, f), pni_dir)
                first_part = rel_path.split(os.sep, 1)[0]
                if first_part not in sub_map:
                    continue
                if (
                    "MP2RAGE"          in f or
                    "T1map"            in f or
                    "UNIT1"            in f or
                    ("acq-fmri_dir-"  in f and "_epi"   in f) or
                    ("task-rest_echo-" in f and "_bold"  in f)
                ):
                    selected_files.append(rel_path)
                    files_per_sub[first_part].append(rel_path)

        print(f"  → Selected {len(selected_files)} files across {len(files_per_sub)} subjects")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("\n".join(selected_files) + "\n")
            file_list_path = tmp.name

        subprocess.run(
            [
                "rsync",
                "-av",
                "--progress",
                "--files-from", file_list_path,
                pni_dir + "/",
                out_dir + "/",
            ],
            check=True,
        )
        os.unlink(file_list_path)

        print("3. Renaming subjects...")

        def _rename_subject(src_sub: str, dst_sub: str) -> int:
            src_path = os.path.join(out_dir, src_sub)
            if not os.path.exists(src_path):
                return 0
            dst_path = os.path.join(out_dir, dst_sub)
            os.rename(src_path, dst_path)
            count = 0
            for rel in files_per_sub.get(src_sub, []):
                fname = os.path.basename(rel)
                if src_sub not in fname:
                    continue
                old_fpath = os.path.join(dst_path, *rel.split(os.sep)[1:])
                new_fpath = os.path.join(os.path.dirname(old_fpath), fname.replace(src_sub, dst_sub))
                os.rename(old_fpath, new_fpath)
                count += 1
            return count

        total_renamed = 0
        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
            futures = {
                pool.submit(_rename_subject, src, dst): src
                for src, dst in sub_map.items()
            }
            for fut in progress_bar(list(as_completed(futures)), prefix=f"Subjects"):
                total_renamed += fut.result()

        print(f"Done. Renamed {total_renamed} files across {len(sub_map)} subjects.")    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
        )

    parser.add_argument("--cbig_xls", required=True, help="Pattern to CBIG XLS")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--pni", required=True, help="Path to PNI BIDS dataset")

    args = parser.parse_args()

    # Timer & beginning
    start_time = time.time()
    print(f"-------------------------------------------")
    print(f"        PNI to CBIG preparation            ")
    print(f"-------------------------------------------")

    # Run main process
    process_cbig_xls(args.cbig_xls, args.out, args.pni)

    # Run BIDS validator
    run_bids_validator(args.out)

    # Capture the end time
    end_time = time.time()  # End time in seconds (wall time)

    # Calculate the time difference in seconds
    time_difference = end_time - start_time

    # Convert the time difference to minutes
    time_difference_minutes = time_difference / 60

    # Format the time difference to 3 decimal places
    formatted_time = f"{time_difference_minutes:.3f}"
    print(f"PROCESSING TIME: {formatted_time} minutes")
    


