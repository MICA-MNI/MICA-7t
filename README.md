# MICA-7t
scripts for 7t sorting a organizing
=======
scripts for 7t sorting, organizing and processing data.

The files from the 7t scan are in `/data/transfer/dicoms`.  

1. The first step is to sort the dicoms to `/data_/mica3/MICA-7T/sorted`
```bash
dcmSort /data/transfer/dicom/pilot3 /data_/mica3/MICA-7T/sorted/sub-pilot3
```
2. From sorted to BIDS
```bash
7t2bids -in /data_/mica3/MICA-7T/sorted/sub-pilot3 -id pilot3 -bids /data_/mica3/MICA-7T/rawdata -ses pilot
```

Processing 7T with micapipe
=======
1. First run the structural processing with the flag `-N4wm` for 7T data
```bash
# Subject's ID
sub=PNC001

micapipe -sub ${sub} -ses 01 \
         -bids /data_/mica3/BIDS_PNC/rawdata \
         -out /data_/mica3/BIDS_PNC/derivatives \
         -proc_structural \
         -N4wm -qsub
```

2.  Once is ready run the freesurfer processing with the flag `-hires` 
```bash
micapipe -sub ${sub} -ses 01 \
         -bids /data_/mica3/BIDS_PNC/rawdata \
         -out /data_/mica3/BIDS_PNC/derivatives \
         -proc_freesurfer -hires \
         -hires -qsub
```

3. Do the QC points and re-run freesurfer if necessary

4. Then the post structural processing and `dwi_proc`
```bash
micapipe -sub ${sub} -ses 01 \
         -bids /data_/mica3/BIDS_PNC/rawdata \
         -out /data_/mica3/BIDS_PNC/derivatives \
         -post_structural \
         -proc_dwi \
         -dwi_rpe rawdata/sub-${sub}/ses-01/fmap/sub-${sub}_ses-01_acq-b0_dir-PA_epi.nii.gz \ 
         -qsub
```

5. Once the post structural processing is ready run the `-GD` `-Morphology`, `-SC` and `-proc_func` with the corresponding arguments
```bash
# set the bids directory as a variable
rawdata=/data_/mica3/BIDS_PNC/rawdata

micapipe -sub ${sub} -ses 01 \
         -bids ${rawdata} \
         -out /data_/mica3/BIDS_PNC/derivatives \
         -SC -tracts 10M \
         -proc_func \
         -mainScanStr task-rest_echo-1_bold,task-rest_echo-2_bold,task-rest_echo-3_bold \
         -fmri_pe ${rawdata}/sub-${sub}/ses-01/fmap/sub-${sub}_ses-01_acq-fmri_dir-AP_epi.nii.gz \
         -fmri_rpe ${rawdata}/sub-${sub}/ses-01/fmap/sub-${sub}_ses-01_acq-fmri_dir-PA_epi.nii.gz \
         -MPC -mpc_acq T1map \
         -microstructural_img ${rawdata}/sub-${sub}/ses-01/anat/sub-${sub}_ses-01_acq-inv1_T1map.nii.gz \
         -microstructural_reg ${rawdata}/sub-${sub}/ses-01/anat/sub-${sub}_ses-01_acq-T1_T1map.nii.gz
         -qsub -threads 15 \
```


# Rawdata size
| **Directory** | **size** |
|---------------|----------|
| anat          | 495M     |
| dwi           | 1.2G     |
| fmap          | 15M      |
| func          | 7.7G     |
| *Total*      | 9.4G     |

# Derivatives size
| **Directory** | **size** |
|---------------|----------|
| freesurfer    | ~830     |
| micapipe/anat | ~820M    |
| micapipe/dwi  | 13G      |
| micapipe/func | 24G      |
| micapipe/logs | 31M      |
| micapipe/xfm  | 2.6G     |
| micapipe/QC   | 46M      |
| micapipe/     | ~10-40G  |
