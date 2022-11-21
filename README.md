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
7t2bids -in /data_/mica3/MICA-7T/sorted/sub-pilot3 -id PNC001 -bids /data_/mica3/MICA-7T/rawdata -ses 01
```

Processing 7T with micapipe
=======
1. First run the structural processing with the flag `-uni` for MP2RAGE 7T data
```bash
# Subject's ID
sub=PNC001

micapipe -sub PNC001 -ses 01 -bids bids_PNC \
         -out bids_PNC/derivatives/ \
         -uni -t1wStr acq-uni_T1map \
         -proc_structural –mf 3 -qsub \
         -threads 15

```

2.  Once is ready run the surface processing module
```bash
micapipe -sub PNC001 -ses 01 -bids bids_PNC \
         -out bids_PNC/derivatives/ \
         -proc_surf \
         -threads 15
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

# 7T MRI acquisition protocol
| Session  | Acquisition                                | BIDS dir | BIDS name              |
|----------|--------------------------------------------|----------|------------------------|
| 01/02/03 | "*anat-T1w_acq-mprage_07mm_UP"             | anat     | acq-mprage_T1w         |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP_INV1"       | anat     | acq-inv1_T1map         |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP_INV2"       | anat     | acq-inv2_T1map         |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP_T1_Images"  | anat     | acq-T1_T1map           |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP_UNI_Images" | anat     | acq-uni_T1map          |
| 01/02    | "*dwi_acq_b0-dir_PA_SBRef"                 | dwi      | acq-b0_dir-PA_sbref    |
| 01/02    | "*dwi_acq_b0-dir_PA"                       | dwi      | acq-b0_dir-PA_epi      |
| 01/02    | "*dwi_acq_b2000_90d-dir_AP_SBRef"          | dwi      | acq-b2000_dir-AP_sbref |
| 01/02    | "*dwi_acq_b2000_90d-dir_AP"                | dwi      | acq-b2000_dir-AP_dwi   |
| 01/02    | "*dwi_acq_b700_40d-dir_AP_SBRef"           | dwi      | acq-b700_dir-AP_sbref  |
| 01/02    | "*dwi_acq_b700_40d-dir_AP"                 | dwi      | acq-b700_dir-AP_dwi    |
| 01/02    | "*dwi_acq_b300_10d-dir_AP_SBRef"           | dwi      | acq-b300_dir-AP_sbref  |
| 01/02    | "*dwi_acq_b300_10d-dir_AP"                 | dwi      | acq-b300_dir-AP_dwi    |
| 01/02/03 | "*func-rsfmri_acq-mbep2d_ME_19mm"          | func     | task-rest_bold         |
| 01       | "*func-epiencode_acq-mbep2d_ME_19mm"       | func     | task-epiencode_bold    |
| 01       | "*func-epiretrieve_acq-mbep2d_ME_19mm"     | func     | task-epiretrieve_bold  |
| 01       | "*func-pattersep1_acq-mbep2d_ME_19mm"      | func     | task-patternsep1_bold  |
| 01       | "*func-patternsep2_acq-mbep2d_ME_19mm"     | func     | task-patternsep2_bold  |
| 01/02/03 | "*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP"     | fmap     | acq-fmri_dir-AP_epi    |
| 01/02/03 | "*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA"     | fmap     | acq-fmri_dir-PA_epi    |
| 01/02/03 | "*fmap-b1_acq-tra_p2"                      | fmap     | acq-b1tra_fieldmap     |
| 01/02/03 | "*fmap-b1_acq-sag_p2"                      | fmap     | acq-b1sag_fieldmap     |
| 02       | "*func-semantic1_acq-mbep2d_ME_19mm"       | func     | task-semantic1_bold    |
| 02       | "*func-semantic2_acq-mbep2d_ME_19mm"       | func     | task-semantic2_bold    |
| 02       | "*func-spatial1_acq-mbep2d_ME_19mm"        | func     | task-spatial1_bold     |
| 02       | "*func-spatial2_acq-mbep2d_ME_19mm"        | func     | task-spatial2_bold     |
| 02/03    | "*anat-T2star_acq-me_gre_07mm"             | anat     | T2starw                |
| 02/03    | "*T2Star_Images"                           | anat     | T2starmap              |
| 03       | "*func-movies1_acq-mbep2d_ME_19mm"         | func     | task-movies1_bold      |
| 03       | "*func-movies2_acq-mbep2d_ME_19mm"         | func     | task-movies2_bold      |
| 03       | "*func-movies3_acq-mbep2d_ME_19mm"         | func     | task-movies3_bold      |
| 03       | "*func-movies4_acq-mbep2d_ME_19mm"         | func     | task-movies4_bold      |
| 03       | "*anat-angio_acq-tof_03mm_inplane"         | anat     | angio                  |
| 03       | "*anat-angio_acq-tof_03mm_inplane_MIP_SAG" | anat     | acq-sag_angio          |
| 03       | "*anat-angio_acq-tof_03mm_inplane_MIP_COR" | anat     | acq-cor_angio          |
| 03       | "*anat-angio_acq-tof_03mm_inplane_MIP_TRA" | anat     | acq-tra_angio          |
| 03       | "*_MTON"                                   | anat     | mt-on_MTR              |
| 03       | "*_MTOFF"                                  | anat     | mt-off_MTR             |
| 03       | "*_T1W"                                    | anat     | acq-T1w_MTR            |


# Rawdata size
| **Directory** | **size** |
|---------------|----------|
| anat          | 495M     |
| dwi           | 1.2G     |
| fmap          | 15M      |
| func          | 7.7G     |
| *Total*       | 9.4G     |

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
