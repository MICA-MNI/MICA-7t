# MICA-7t
scripts for 7t sorting and organizing
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

3. Then the post structural processing and `dwi_proc`
```bash
micapipe -sub ${sub} -ses 01 \
         -bids /data_/mica3/BIDS_PNC/rawdata \
         -out /data_/mica3/BIDS_PNC/derivatives \
         -post_structural \
         -proc_dwi \
         -dwi_rpe rawdata/sub-${sub}/ses-01/fmap/sub-${sub}_ses-01_acq-b0_dir-PA_epi.nii.gz \ 
         -qsub
```

4. Once the post structural processing is ready run the `-GD` `-Morphology`, `-SC` and `-proc_func` with the corresponding arguments
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

Fastsurfer surface workflow with QC
=======
The main outputs of `fastsurfer` deep volumetric segmentation are found under the `mri/` directory: `aparc.DKTatlas+aseg.deep.mgz`, `mask.mgz`, and `orig.mgz`. The equivalent of freesurfer's brainmask.mgz now is called `norm.mgz`.

1. Run `run_fastsurfer.sh` deep segmentation first separately from micapipe using the singularity container:
```bash
# Define variables
sub=sub-PNA002
ses=ses-01
PNI_DIR=/data_/mica3/BIDS_PNI/derivatives
SUBJECTS_DIR=${PNI_DIR}/fastsurfer
t1nativepro=${PNI_DIR}/micapipe_v0.2.0/${sub}/${ses}/anat
fastsurfer_img=/data_/mica1/01_programs/fastsurfer/fastsurfer-cpu-v2.0.0.sif
fs_licence=/data_/mica1/01_programs/freesurfer-7.3.2/
threads=15
unset TMPDIR

# Run the singularity container
singularity exec --nv -B ${SUBJECTS_DIR}/${sub}_${ses}:/data \
                      -B "${SUBJECTS_DIR}":/output \
                      -B "${fs_licence}":/fs \
                      -B "${t1nativepro}":/anat \
                       ${fastsurfer_img} \
                       /fastsurfer/run_fastsurfer.sh \
                      --fs_license /fs/license.txt \
                      --t1 /anat/${sub}_${ses}_space-nativepro_t1w.nii.gz \
                      --sid ${sub}_${ses} --sd /output --no_fs_T1 \
                      --parallel --threads ${threads}
                      
# Change the outputs permission, in case that someone else has to work on them
chmod aug+wr -R ${SUBJECTS_DIR}/${sub}_${ses}
```

2. The edits should be perfom on the `mask.mgz` file. However, maybe it's easier to correct over the file called `norm.mgz`. Once the edits are perform you can replace `mask.mgz` with the binarized version of the corrected `norm.mgz`.

```bash
# Convert from mgz to nifti
mri_convert.bin norm.mgz norm.nii.gz

# Binarize nifti
fslmaths norm.nii.gz -bin mask.nii.gz

# Replace mask
mri_convert mask.nii.gz mask.mgz

# removed intermediate files
rm mask.nii.gz norm.nii.gz

# remove files previouslly created by the first run of recon-surf
rm wm.mgz aparc.DKTatlas+aseg.orig.mgz
```

3. Run the command `recon-surf.sh` using a singularity container to generate the new surfaces:
```
# Subject id
sub=sub-PNA002
ses=ses-01

# output directory
SUBJECTS_DIR=/data_/mica3/BIDS_PNI/derivatives/fastsurfer

# path to singularity image
fastsurfer_img=/data_/mica1/01_programs/fastsurfer/run_fastsurfer.sh

# freesurfer licence
fs_licence=/data_/mica1/01_programs/freesurfer-7.3.2/

# Number of threads for parallel processing
threads=15

# Remove this variable from `env` cos it could lead to an error withing the container
unset TMPDIR

# Run only the surface recontruction with spectral spherical projection (fastsurfer default algorithm instead of freesurfer)
singularity exec --nv -B ${SUBJECTS_DIR}/${sub}_${ses}:/data \
                      -B "${SUBJECTS_DIR}":/output \
                      -B "${fs_licence}":/fs \
                       ${fastsurfer_img} \
                       /fastsurfer/recon_surf/recon-surf.sh \
                      --fs_license /fs/license.txt \
                      --t1 /data/mri/orig.mgz \
                      --sid ${sub}_${ses} --sd /output --no_fs_T1 \
                      --parallel --threads ${threads}
                      
# Change the outputs permission, in case that someone else has to work on them
chmod aug+wr -R ${SUBJECTS_DIR}/${sub}_${ses}
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
