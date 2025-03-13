# Sorting and BIDS conforming 7T data

## Directory Contents

| **File**                    | **Description**                                                  |
|-----------------------------|------------------------------------------------------------------|
| `dcm2bids.py`               | Python script for converting DICOM data to BIDS format, with BIDS validation |
| `dcmSort.py`                | Python script to sort DICOM files (based on `pydicom`)           |
| `group_check.py`            | Python script for checking group characteristics or data integrity|
| `7t2bids`                   | Script to convert 7T MRI data to BIDS format, with BIDS validation           |
| `dcmSort`                   | Bash script to sort DICOM files (*legacy code*).                 |
| `denoiseN4`                 | Script for applying N4ITK denoising to MRI data                  |
| `post-qc_fastsurfer.sh`     | Shell script for post-processing quality control with FreeSurfer |
| `utilities.sh`              | Shell script with various utility functions for MRI processing   |

## Script usage

### Integrated workflow from DICOMS to BIDS
```bash
dcm2bids.py --sub SUB --ses SES --dicoms_dir DICOMS_DIR --sorted_dir SORTED_DIR --bids_dir BIDS_DIR
```

### Modular workflow from DICOMS to BIDS
```bash
# Fisrt sort the dicoms
dcmSort DICOMS_DIR SORTED_DIR

# Then create the BIDS directory (SUB without sub-, SES without ses-)
7t2bids -in SORTED_DIR -id SUB -ses SES -bids BIDS_DIR 
```

### Denoising with N4 and NLM
```bash
denoiseN4 NIFTI OUT_NAME OUT_DIRECTORY N_THREADS
```

