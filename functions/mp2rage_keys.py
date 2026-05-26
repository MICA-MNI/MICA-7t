#!/usr/bin/env python3
"""
mp2rage_bids-patch.py -sub <sub> -ses <ses> -bids <bids_dir>

Patches MP2RAGE BIDS JSON sidecars with required keys missing after dcm2bids.
"""

import argparse, glob, json, os, sys
import nibabel as nib

#-------------------------------------------------------------------------------
# Protocol look-up: {ProtocolName: {EchoTime|None: RepetitionTimeExcitation}} 
# NOTE: EchoSpacing was obtained from the acquisition protocol (sequence card /
#       PDF export from the Siemens scanner), NOT from the DICOM header.
RTE_LUT = {
    "anat-T1w_acq-mp2rage_0.7mm_CSptx":  {None: 0.0078},                       # fixed value
    "anat-T1w_acq-mp2rage_07mm_CSptx": {None: 0.0078},                       # fixed value
    "anat-T1w_acq-mp2rage_05mm_UP": {0.00281: 0.0089, 0.00244: 0.0078},  # echo-time variants
    "anat-T1w_acq-mp2rage_05mm_UP_Repeat": {0.00281: 0.0089, 0.00244: 0.0078},  # echo-time variants
    "cstfl-mp2rage-05mm": {None: 0.0078}  # MUST verify from acquisition protocol
}

#-------------------------------------------------------------------------------
# Orientation: NIfTI axis index for each dimension key
# If ImageOrientationText = sag, example:
# SlicesPerSlab: L-R  (slab dimension, slice direction) = dim1
# ReconMatrixPE: A-P  (phase encode direction)          = dim2
# BaseResolution: H-F  (readout direction)              = dim3
ORI_DIM = {
    "sag": (0, 1, 2),
    "cor": (0, 1, 2),
    "tra": (0, 1, 2),
}
DIM_KEYS     = ["SlicesPerSlab", "ReconMatrixPE", "BaseResolution"]
REQUIRED_KEYS = ["RepetitionTimePreparation", "RepetitionTimeExcitation",
                 "SlicesPerSlab", "NumberShots"]


def patch(json_path: str, nii_path: str) -> None:
    print(f"\n  → {os.path.basename(json_path)}")

    # 1. Load JSON; exit early if all required keys already populated
    with open(json_path) as f:
        d = json.load(f)

    if all(d.get(k) not in (None, "", [], {}) for k in REQUIRED_KEYS):
        print("    [skip] all required keys present"); return

    # 2. RepetitionTimePreparation = RepetitionTime
    if "RepetitionTime" in d:
        d["RepetitionTimePreparation"] = d["RepetitionTime"]
        print(f"    [set]  RepetitionTimePreparation = {d['RepetitionTime']}")

    # 3. RepetitionTimeExcitation from protocol look-up
    protocol, echo_time = d.get("ProtocolName", ""), d.get("EchoTime")
    lut = RTE_LUT.get(protocol)
    if lut:
        rte = lut.get(echo_time) or lut.get(None)
        if rte:
            d["RepetitionTimeExcitation"] = rte
            print(f"    [set]  RepetitionTimeExcitation = {rte} s  (protocol={protocol}, TE={echo_time})")
        else:
            print(f"    [warn] EchoTime={echo_time} not in LUT for {protocol}")
    else:
        print(f"    [warn] ProtocolName '{protocol}' not in look-up table")

    # 4. SlicesPerSlab / ReconMatrixPE / BaseResolution from NIfTI header
    dims = nib.load(nii_path).header.get_data_shape()[:3]
    axes = ORI_DIM.get(d.get("ImageOrientationText", "sag").lower()[:3], (0, 1, 2))

    for key, ax in zip(DIM_KEYS, axes):
        val = d.get(key)
        if val in (None, "", [], {}):           # missing → fill from NIfTI
            d[key] = int(dims[ax])
            print(f"    [set]  {key} = {d[key]}  (NIfTI dim{ax+1})")
        elif val != int(dims[ax]):              # present → cross-check
            print(f"    [warn] {key}: JSON={val}  NIfTI={int(dims[ax])}  → mismatch")

    # 5. NumberShots = [SlicesPerSlab*(PartialFourier-0.5), SlicesPerSlab*0.5]
    slices, pf = d.get("SlicesPerSlab"), d.get("PartialFourier")
    if slices and pf:
        d["NumberShots"] = [slices * (pf - 0.5), slices * 0.5]
        print(f"    [set]  NumberShots = {d['NumberShots']}")
    else:
        print(f"    [warn] cannot compute NumberShots (SlicesPerSlab={slices}, PartialFourier={pf})")

    #-------------------------------------------------------------------------------
    # Save patched JSON
    with open(json_path, "w") as f:
        json.dump(d, f, indent=4)
    print(f'  {d.get("ProtocolName")}_inv-{d.get("InversionTime")}: [saved]')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-sub",  required=True)
    ap.add_argument("-ses",  required=True)
    ap.add_argument("-bids", required=True, dest="bids_dir")
    a = ap.parse_args()

    pattern = os.path.join(a.bids_dir, f"sub-{a.sub}", f"ses-{a.ses}",
                           "anat", "*inv-*MP2RAGE*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"[warn] no MP2RAGE JSON files found: {pattern}"); sys.exit(0)

    print(f"[info] {len(files)} MP2RAGE sidecar(s) found")
    for json_path in files:
        nii_path = json_path.replace(".json", ".nii.gz")
        if not os.path.isfile(nii_path):
            print(f"  [warn] NIfTI missing for {os.path.basename(json_path)} – skipping")
            continue
        patch(json_path, nii_path)

    print("\n[done] MP2RAGE BIDS patching complete.\n")


if __name__ == "__main__":
    main()