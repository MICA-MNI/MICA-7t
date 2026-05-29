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
from datetime import datetime
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

def create_bidsignore(out_dir):
    bidsignore_path = f"{out_dir}/.bidsignore"
    content = "bids_validator_output.txt\nsub*/ses*/anat/*desc*\n"
    with open(bidsignore_path, 'w') as f:
        f.write(content)

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
    print(f"\n-------------------------------------------")
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


def process_cbig_xls(cbig_xls_path, out_dir, pni_dir=None, sessions=None):
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
        "External Study Identifiers": "MICSID",
        "PSCID": "participant_id",
        "Entity Type": "entity",
        "Participant Status": "status",
        "Date of registration": "registration",
        "Sex": "sex", 
        "Age": "age", 
        "Site": "site", 
        "Diagnosis": "diagnosis"
    })

    # Add sub-
    df["participant_id"] = df["participant_id"].astype(str).apply(lambda x: f"sub-{x}")

    # Reorder
    df = df[["participant_id", "DCCID", "MICSID",
             "sex", "age", "registration", 
             "site", "entity", "status", "diagnosis"]]

    os.makedirs(out_dir, exist_ok=True)
    
    # ------------------------------------------
    # Save TSV
    df.to_csv(os.path.join(out_dir, "participants.tsv"), sep="\t", index=False)

    # Save JSON
    participants_json = {
        "participant_id": {
            "LongName": "Participant Study Code Identifier (PSCI)",
            "Description": "Assigned identification number for a subject (with 'sub-' as prefix)."
        },
        "DCCID": {"LongName": "DCCID", "Description": "Data Coordinating Center Identifier."},
        "MICSID": {"LongName": "MICSID", "Description": "MICA lab Code Identifier."},
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

    # ------------------------------------------
    # PNI symlink + cp
    # ------------------------------------------
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

        print(f"-------------------------------------------")
        print("2. Mapping individual files...")
        sub_map = {
            f"sub-{row['MICSID']}": row["participant_id"]
            for _, row in df.iterrows()
        }

        anat_files: list[tuple[str, str]] = []
        rsync_files: list[str] = []

        # Collect all files first so we have a len() for the progress bar
        all_files = [
            (root, f)
            for root, _, files in os.walk(pni_dir)
            for f in files
        ]

        for root, f in progress_bar(all_files, prefix="  Scanning files"):
            full_path = os.path.join(root, f)
            rel_path  = os.path.relpath(full_path, pni_dir)
            parts     = rel_path.split(os.sep)
            if sessions and (len(parts) < 2 or parts[1].replace("ses-", "") not in sessions):
                continue
            first_part = parts[0]
            if first_part not in sub_map:
                continue
            is_anat      = len(parts) >= 3 and parts[2] == "anat"
            is_func_fmap = len(parts) >= 3 and parts[2] in ("func", "fmap")
            matched = (
                "MP2RAGE"          in f or
                "T1map"            in f or
                "UNIT1"            in f or
                ("acq-fmri_dir-"  in f and "_epi"  in f) or
                ("task-rest_echo-" in f and "_bold" in f)
            )
            if not matched:
                continue
            dst_sub = sub_map[first_part]
            dst_rel_parts = [dst_sub] + parts[1:]
            if is_anat:
                dst_fname = parts[-1].replace(first_part, dst_sub)
                dst_rel_parts[-1] = dst_fname
                anat_files.append((rel_path, os.path.join(*dst_rel_parts)))
            elif is_func_fmap:
                rsync_files.append(rel_path)

        print(f"  - {len(anat_files)} anat files (symlink) | {len(rsync_files)} func/fmap files (rsync)")

        # A: anat = symlinks
        print(f"-------------------------------------------")
        print("3. Creating anat symlinks...")
        symlink_count = 0
        for src_rel, dst_rel in progress_bar(anat_files, prefix="  Symlinking"):
            src_abs = os.path.join(pni_dir, src_rel)
            dst_abs = os.path.join(out_dir,  dst_rel)
            if os.path.islink(dst_abs):
                continue
            os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
            os.symlink(src_abs, dst_abs)
            symlink_count += 1

        print(f"  → Created {symlink_count} symlinks ({len(anat_files) - symlink_count} skipped)")

        # ------------------------------------------
        # B: func & fmap = rsync (skip existing)
        print(f"-------------------------------------------")
        print("4. Rsyncing func/fmap files...")

        # ------------------------------------------
        # Build a renamed file list: rsync from pni_dir but we need the dst sub name.
        # Strategy: rsync each sub separately so we can set the destination path.
        sub_rsync: dict[str, list[str]] = {}
        for rel in rsync_files:
            src_sub = rel.split(os.sep)[0]
            sub_rsync.setdefault(src_sub, []).append(rel)

        rsync_count = 0
        skipped_count = 0
        for src_sub, rels in sub_rsync.items():
            dst_sub = sub_map[src_sub]

            # Filter out files that already exist in the destination (c)
            to_sync: list[str] = []
            for rel in rels:
                parts   = rel.split(os.sep)
                dst_rel = os.path.join(dst_sub, *parts[1:])
                # Rename sub string in filename
                dst_rel_parts        = dst_rel.split(os.sep)
                dst_rel_parts[-1]    = dst_rel_parts[-1].replace(src_sub, dst_sub)
                dst_abs              = os.path.join(out_dir, *dst_rel_parts)

                if os.path.exists(dst_abs):      # (c) skip existing
                    skipped_count += 1
                    continue
                to_sync.append(rel)

            if not to_sync:
                continue

            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
                tmp.write("\n".join(to_sync) + "\n")
                file_list_path = tmp.name

            # rsync into a temp sub-named folder, then rename sub token in filenames
            tmp_sub_dir = os.path.join(out_dir, src_sub)
            subprocess.run(
                [
                    "rsync", "-av", "--progress",
                    "--files-from", file_list_path,
                    pni_dir + "/",
                    out_dir + "/",
                ],
                check=True,
            )
            os.unlink(file_list_path)

            # Rename sub string in path and filenames after rsync
            src_sub_path = os.path.join(out_dir, src_sub)

            # Rename sub string in filenames inside the rsynced tree
            for rel in to_sync:
                parts    = rel.split(os.sep)
                old_path = os.path.join(out_dir, *parts)
                new_parts = [dst_sub] + parts[1:]
                new_parts[-1] = new_parts[-1].replace(src_sub, dst_sub)
                new_path = os.path.join(out_dir, *new_parts)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                os.rename(old_path, new_path)
                rsync_count += 1

            # Clean up the entire src_sub directory tree (not just root)
            if os.path.isdir(src_sub_path):
                shutil.rmtree(src_sub_path) 

        print(f"  → Rsynced {rsync_count} files ({skipped_count} already existed)")

def create_sessions(out_dir):
    print(f"-------------------------------------------")
    print("Creating sessions files...")
    for ses_dir in glob.glob(os.path.join(out_dir, "sub-*", "ses-*")):
        sub, ses = ses_dir.split(os.sep)[-2:]
        sessions_tsv = os.path.join(out_dir, sub, f"{sub}_sessions.tsv")
        pd.DataFrame({"session_id": [ses]}).to_csv(sessions_tsv, sep="\t", index=False)

def create_scans(out_dir):
    print(f"-------------------------------------------")
    print("Creating scans files...")
    fixed_date="2026-10-01T"
    for ses_dir in glob.glob(os.path.join(out_dir, "sub-*", "ses-*")):
        rows = []
        for nii in glob.glob(os.path.join(ses_dir, "**", "*.nii.gz"), recursive=True):
            json_path = nii.replace(".nii.gz", ".json")
            acq_time = "n/a"
            if os.path.exists(json_path):
                acq_time = json.load(open(json_path)).get("AcquisitionTime", "n/a")
                if acq_time != "n/a":
                    acq_time = (datetime.strptime(json.load(open(json_path))["AcquisitionTime"].split(".")[0],"%H:%M:%S").strftime("%H:%M:%S"))
            rows.append({"filename": os.path.relpath(nii, ses_dir), "acq_time": f'{fixed_date}{acq_time}'})
        if not rows:
            continue

        sub, ses = ses_dir.split(os.sep)[-2:]
        pd.DataFrame(rows).to_csv(os.path.join(ses_dir, f"{sub}_{ses}_scans.tsv"), sep="\t", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
        )

    parser.add_argument("--cbig_xls", required=True, help="Pattern to CBIG XLS")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--pni", required=True, help="Path to PNI BIDS dataset")
    parser.add_argument("--ses", nargs="+", default=["01", "a1"], help="Session(s) to process")

    args = parser.parse_args()

    # Timer & beginning
    start_time = time.time()
    print(f"-------------------------------------------")
    print(f"        PNI to CBIG preparation            ")
    print(f"-------------------------------------------")

    # Run main process
    process_cbig_xls(args.cbig_xls, args.out, args.pni, args.ses)

    # Create bidsignore file
    create_bidsignore(args.out)

    # Create scans.tsv file on each subjec/session directory
    create_scans(args.out)

    # Create scans.tsv file on each subjec/session directory
    create_sessions(args.out)

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
    print(f"\n-------------------------------------------")
    print(f"Processing time: {formatted_time} minutes")

