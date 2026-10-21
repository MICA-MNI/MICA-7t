#!/usr/bin/env python3
"""Rename the run entities 7t2bids got wrong in an existing BIDS_PNI tree.

Two problems the converter has since been fixed for, applied to sessions it
already converted:

1. acq-me T2starw: the magnitude and its phase were exported under one series
   name and came out as run-1 (part-mag) and run-2 (part-phase) of a single
   acquisition. Each such pair becomes one run, or no run when there is one
   pair (RUN_SEPARATES_MAG_PHASE in details.tsv).
2. A phase file left with dcm2niix's "_ph" suffix, as rec-unwrapped T2starw
   with more than one run was (sub-PNE098 ses-a1): "X_T2starw_ph" becomes
   "X_part-phase_T2starw" and its JSON gains "Units": "rad", as 7t2bids gives
   every phase file.

Each session's scans.tsv is updated to the new names. Nothing is overwritten,
nothing is deleted, and sessions where the files do not look exactly like
these cases are left alone. Without --apply it only prints what it would do.

    patch_pni_runs.py /data_/mica3/BIDS_PNI/rawdata            # dry run
    patch_pni_runs.py /data_/mica3/BIDS_PNI/rawdata --apply

JSON is edited with jq, the tool 7t2bids writes it with, so formatting and
numbers are kept exactly as they are.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

RUN = re.compile(r"_acq-me_(run-\d+)_(echo-\d+_part-(mag|phase))_T2starw\.(nii\.gz|json)$")
LEFTOVER_PH = re.compile(r"^(.*)_T2starw_ph\.(nii\.gz|json)$")


def mag_phase_renames(anat: Path) -> list[tuple[Path, Path]]:
    """acq-me T2starw runs that are magnitude/phase pairs, merged."""
    runs: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for path in anat.iterdir():
        match = RUN.search(path.name)
        if match:
            runs[match.group(1)][match.group(3)].append(path)
    if not runs or len(runs) % 2:
        return []
    ordered = sorted(runs, key=lambda run: int(run.split("-")[1]))
    pairs = [(ordered[i], ordered[i + 1]) for i in range(0, len(ordered), 2)]
    for magnitude, phase in pairs:
        if set(runs[magnitude]) != {"mag"} or set(runs[phase]) != {"phase"}:
            return []
    renames = []
    for index, (magnitude, phase) in enumerate(pairs):
        new_run = "" if len(pairs) == 1 else f"run-{index + 1}_"
        for run in (magnitude, phase):
            for kind in runs[run].values():
                for path in sorted(kind):
                    target = path.with_name(
                        path.name.replace(f"_acq-me_{run}_", f"_acq-me_{new_run}")
                    )
                    if target != path:
                        renames.append((path, target))
    return renames


def leftover_ph_renames(anat: Path) -> list[tuple[Path, Path]]:
    renames = []
    for path in anat.iterdir():
        match = LEFTOVER_PH.match(path.name)
        if match:
            renames.append(
                (path, path.with_name(f"{match.group(1)}_part-phase_T2starw.{match.group(2)}"))
            )
    return renames


def update_scans(session: Path, renames: list[tuple[Path, Path]], apply: bool) -> int:
    scans = next(iter(session.glob("*_scans.tsv")), None)
    if scans is None:
        return 0
    mapping = {
        f"{old.parent.name}/{old.name}": f"{new.parent.name}/{new.name}"
        for old, new in renames
        if old.name.endswith(".nii.gz")
    }
    lines = scans.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = 0
    for index, line in enumerate(lines):
        name, sep, rest = line.partition("\t")
        if name in mapping:
            lines[index] = mapping[name] + sep + rest
            changed += 1
    if apply and changed:
        scans.write_text("".join(lines), encoding="utf-8")
    return changed


def add_units(json_path: Path) -> None:
    result = subprocess.run(
        ["jq", '. + {"Units": "rad"}', str(json_path)], check=True, capture_output=True, text=True
    )
    json_path.write_text(result.stdout, encoding="utf-8")


def main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("rawdata", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(arguments)

    total = 0
    for anat in sorted(args.rawdata.glob("sub-*/ses-*/anat")):
        session = anat.parent
        renames = mag_phase_renames(anat) + leftover_ph_renames(anat)
        if not renames:
            continue
        # Renames run pair by pair, so a target may be a file renamed earlier in the list.
        moving = {old for old, _ in renames}
        clashes = [new for _, new in renames if new.exists() and new not in moving]
        if clashes:
            print(f"SKIP {session}: would overwrite {clashes[0].name}", file=sys.stderr)
            continue
        print(f"## {session.relative_to(args.rawdata)}")
        for old, new in renames:
            print(f"  mv {old.name} -> {new.name}")
            if args.apply:
                old.rename(new)
                if LEFTOVER_PH.match(old.name) and new.name.endswith(".json"):
                    add_units(new)
        lines = update_scans(session, renames, args.apply)
        print(f"  scans.tsv: {lines} line(s)")
        total += len(renames)
    print(f"{'renamed' if args.apply else 'would rename'} {total} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
