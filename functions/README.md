# Sorting and BIDS conforming 7T data

## Directory Contents

| **File**               | **Workflow**  | **Description** |
|------------------------|---------------|-----------------|
| `dcm2bids.py`          | PNI           | Python script for converting DICOM data to BIDS format, with BIDS validation. |
| `dcmSort.py`           | PNI           | Python script to sort DICOM files (based on `pydicom`). |
| `7t2bids`              | PNI           | Script to convert 7T MRI data to BIDS format, with BIDS validation. |
| `dcmSort`              | PNI           | DEPRECATED Bash script to sort DICOM files (legacy code). |
| `mp2rage_keys.py`      | PNI           | Patches MP2RAGE BIDS JSON sidecars with required keys missing after dcm2bids. |
| `denoiseNLM`            | micapipe 7T   | Script for applying minc-non local means denoising to MRI data. |
| `post-qc_fastsurfer.sh`| micapipe 7T   | Shell script for post-processing quality control with FreeSurfer. |
| `utilities.sh`         | general       | Shell script with various utility functions for MRI processing. |
| `cbig_workflow.py`     | cbig          | Prepares the files from PNI to CBIG ingestion. |
| `cbig_deidentify.sh`   | cbig          | Defaces and denoises anatomical images/JSON for CBIG ingestion and data release. |

## Script usage

### Integrated workflow from DICOMS to BIDS
```bash
dcm2bids.py --sub SUB --ses SES --dicoms_dir DICOMS_DIR --sorted_dir SORTED_DIR --bids_dir BIDS_DIR
```

### Modular workflow from DICOMS to BIDS
```bash
# Fisrt sort the dicoms
dcmSort <DICOMS_DIR> <SORTED_DIR>

# Then create the BIDS directory (SUB without sub-, SES without ses-)
7t2bids -in <SORTED_DIR> -id <SUB> -ses <SES> -bids <BIDS_DIR>
```

### Denoising with N4 and NLM
```bash
export TMPDIR=<custom temporary directory>
denoiseNLM <NII> <ID> <OUTDIR> [-threads N] [-sigma S] [-beta B]
```

## PNI to C-BIG
Run the `pni2cbig.py` script from the MICA-7 repository to generate the CBIG-compatible dataset structure and participant files.

```bash

# Set the directory to PNI database
pni_dir=/data_/mica3/BIDS_PNI/rawdata
pni_cbig=/host/bb-compx-03/export02/databases/BIDS_PNI/rawdata
xls=/host/bb-compx-03/export02/databases/BIDS_PNI/CBIG_data-2026-03-31T18_16_54.348Z.xls

# Run the script to organize the data
cbig_workflow.py \
	--cbig_xls ${xls} \
	--out ${pni_cbig} \
	--pni ${pni_dir}
```


## Step 2: Deface and replace

Deface and rename all anatomical (anat) files to ensure they comply with CBIG ingestion requirements and subject anonymization standards.

```bash

# Change directory to the CBIG BIDS
cd ${pni_dir}/cbig/bids

# For each subject deface and rename
> Note: keep a log of the subjects refaced at the top `/cbig`.

for subses in sub*/ses*; do
    sub=${subses%%/*}
    ses=${subses##*/}
    echo cbig_deidentify.sh "${sub/sub-}" "${ses/ses-}"
done

```


