#!/usr/bin/env python3
"""Fix the run entities of sessions already in a BIDS_PNI tree.

It applies the rules of rcruces/preproc_reports drafts/2026_bids-eval_runs.py
to existing files, by renaming only. An acquisition family is a set of files
that share every entity except run and part (echo included). For each family
that has run entities:

- RUN_SEPARATES_MAG_PHASE: runs that come in magnitude-then-phase pairs
  (run-1 part-mag or no part, run-2 part-phase) are one acquisition each. The
  pair is merged into one run, or into no run when there is a single pair.
  This covers the acq-me T2starw of the old protocol, and sub-PNA004 ses-a1's
  rest (run-2 magnitude, run-3 phase).
- RUN_SHOULD_BE_OMITTED: a single run loses its run entity.
- RUN_NONCONTIGUOUS: runs are renumbered 1..n in their order.

It also renames phase files left with dcm2niix's "_ph" suffix
(rec-unwrapped_run-?_T2starw_ph in sub-PNE098 ses-a1) to part-phase, adding
"Units": "rad" to their JSON as 7t2bids does for every phase file.

Every file of a renamed stem moves with it (.nii.gz, .json, .bval, .bvec), and
the session's scans.tsv follows. Nothing is overwritten or deleted. A family
that fits none of these shapes is reported and left alone. Without --apply it
only prints what it would do.

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

DATATYPES = ("anat", "func", "fmap", "dwi")
EXTENSIONS = (".nii.gz", ".json", ".bval", ".bvec")
ENTITY = re.compile(r"^([A-Za-z0-9]+)-(.+)$")
LEFTOVER_PH = re.compile(r"^(.*)_T2starw_ph$")


def split(name: str) -> tuple[str, str] | None:
    for extension in EXTENSIONS:
        if name.endswith(extension):
            return name[: -len(extension)], extension
    return None


def entities(stem: str) -> tuple[dict[str, str], str]:
    tokens = stem.split("_")
    found = {}
    for token in tokens[:-1]:
        match = ENTITY.match(token)
        if match:
            found[match.group(1)] = match.group(2)
    return found, tokens[-1]


def family_of(stem: str) -> str | None:
    found, suffix = entities(stem)
    if "sub" not in found:
        return None
    kept = [f"{k}-{v}" for k, v in found.items() if k not in ("sub", "ses", "run", "part")]
    return "_".join(kept + [suffix])


def with_run(stem: str, old: int, new: int | None) -> str:
    return stem.replace(f"_run-{old}_", "_" if new is None else f"_run-{new}_")


def new_runs(stems: set[str]) -> tuple[dict[int, int | None] | None, str]:
    """How the runs of one family should be numbered, and which rule says so."""
    kinds: dict[int, set[str]] = defaultdict(set)
    for stem in stems:
        found, _ = entities(stem)
        if "run" not in found or not found["run"].isdigit():
            return None, ""
        kinds[int(found["run"])].add(found.get("part", "mag"))
    runs = sorted(kinds)
    if len(runs) % 2 == 0 and all(
        kinds[runs[i]] == {"mag"} and kinds[runs[i + 1]] == {"phase"}
        for i in range(0, len(runs), 2)
    ):
        pairs = len(runs) // 2
        mapping = {}
        for index in range(pairs):
            new = None if pairs == 1 else index + 1
            mapping[runs[2 * index]] = new
            mapping[runs[2 * index + 1]] = new
        return mapping, "RUN_SEPARATES_MAG_PHASE"
    if len(runs) == 1:
        return {runs[0]: None}, "RUN_SHOULD_BE_OMITTED"
    if runs != list(range(1, len(runs) + 1)):
        return {run: index + 1 for index, run in enumerate(runs)}, "RUN_NONCONTIGUOUS"
    return {}, ""


def session_renames(session: Path) -> tuple[list[tuple[Path, Path, str]], list[str]]:
    renames: list[tuple[Path, Path, str]] = []
    skipped: list[str] = []
    for datatype in DATATYPES:
        folder = session / datatype
        if not folder.is_dir():
            continue
        files: dict[str, list[Path]] = defaultdict(list)
        for path in folder.iterdir():
            parts = split(path.name)
            if parts:
                files[parts[0]].append(path)

        # Phase files that kept dcm2niix's "_ph" become part-phase first.
        for stem in sorted(files):
            match = LEFTOVER_PH.match(stem)
            if match:
                new_stem = f"{match.group(1)}_part-phase_T2starw"
                for path in files.pop(stem):
                    renames.append((path, folder / (new_stem + split(path.name)[1]), "LEFTOVER_PH"))
                files[new_stem] = []

        families: dict[str, set[str]] = defaultdict(set)
        without_run: set[str] = set()
        for stem in files:
            family = family_of(stem)
            if not family:
                continue
            if "_run-" in stem:
                families[family].add(stem)
            else:
                without_run.add(family)
        planned = {old.name for old, _, _ in renames}
        for family, stems in sorted(families.items()):
            if family in without_run:
                # Some acquisitions of this family carry a run and some do not;
                # which run each should have depends on when it was acquired.
                skipped.append(f"{datatype}/{family}: files with and without run")
                continue
            mapping, rule = new_runs(stems)
            if mapping is None:
                skipped.append(f"{datatype}/{family}: run is not a number")
                continue
            for old_run, new_run in sorted(mapping.items()):
                for stem in sorted(stems):
                    if f"_run-{old_run}_" not in stem or new_run == old_run:
                        continue
                    new_stem = with_run(stem, old_run, new_run)
                    for path in files.get(stem, []):
                        if path.name in planned:
                            continue
                        renames.append((path, folder / (new_stem + split(path.name)[1]), rule))
    return renames, skipped


def update_scans(session: Path, renames: list[tuple[Path, Path, str]], apply: bool) -> int:
    scans = next(iter(session.glob("*_scans.tsv")), None)
    if scans is None:
        return 0
    mapping = {
        f"{old.parent.name}/{old.name}": f"{new.parent.name}/{new.name}"
        for old, new, _ in renames
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
    sessions = 0
    for session in sorted(args.rawdata.glob("sub-*/ses-*")):
        if not session.is_dir():
            continue
        renames, skipped = session_renames(session)
        for reason in skipped:
            print(f"LEAVE {session.relative_to(args.rawdata)} {reason}", file=sys.stderr)
        if not renames:
            continue
        # Runs are renamed lowest first, so a target may be a file moved earlier in the list.
        moving = {old for old, _, _ in renames}
        clashes = [new for _, new, _ in renames if new.exists() and new not in moving]
        if clashes or len({new for _, new, _ in renames}) != len(renames):
            print(f"SKIP {session.relative_to(args.rawdata)}: would overwrite "
                  f"{clashes[0].name if clashes else 'a file it renames'}", file=sys.stderr)
            continue
        print(f"## {session.relative_to(args.rawdata)}")
        for old, new, rule in renames:
            print(f"  {rule}: {old.parent.name}/{old.name} -> {new.name}")
            if args.apply:
                old.rename(new)
                if rule == "LEFTOVER_PH" and new.name.endswith(".json"):
                    add_units(new)
        print(f"  scans.tsv: {update_scans(session, renames, args.apply)} line(s)")
        total += len(renames)
        sessions += 1
    verb = "renamed" if args.apply else "would rename"
    print(f"{verb} {total} file(s) in {sessions} session(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
