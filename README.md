# MICA-7t
Scripts for sorting, organizing and processing the 7T database
=======

## 1 . Transfering the data
>  Update this step
The files from the 7t scan are in `/data/transfer/dicoms?????`.   

## 2. Sorting the dicoms
The first step is to sort the dicoms to `/data_/mica3/BIDS_PNI/sorted` using the `dcmSort` script.
```bash
dcmSort <dicoms_directory> /data_/mica3/BIDS_PNI/sorted/PNC001_ses-01
```

## 3. From sorted dicoms to BIDS
Once the dicoms are sorted we can run the `7t2bids` to transform all the dicoms into NIFTIS and rename and organize the files  accoding to BIDS. 
```bash
7t2bids -in /data_/mica3/BIDS_PNI/sorted/PNC001_ses-01 -id PNC001 -bids /data_/mica3/MICA-7T/rawdata -ses 01
```

Processing 7T with `micapipe`
=======
You can run any module of the pipeline locally (`-mica`), on the mica.q (`-qsub`) or all.q (`-qall`). But you should always use one of these flags.

`micapipe` first stage modules: structural processing
-------
1. First run the structural processing with the flag `-uni` for MP2RAGE 7T data
```bash
# Subject's ID
sub=PNC001
ses=01
bids=bids_PNC/rawdata
out=bids_PNC/derivatives

micapipe -sub ${sub} -ses ${ses} -bids ${bids} \
         -out ${out} \
         -uni -T1wStr acq-uni_T1map \
         -proc_structural –mf 3 \
         -threads 15 -qsub

```

Surface processing
-------
2.  Here we run a denoising algorithm on the `t1nativepro` to enhance contrast in grey/white matter to facilitate the surface generation.
> This step might be incorporated into the pipeline in the future but is still work on progress...

```bash
id=sub-PNC001_ses-01
Nifti=${id}/anat/${id/\//_}_space-nativepro_T1w.nii.gz
outStr=${id/\//_}_space-nativepro_T1w_nlm
outdir=${id}/anat
  
denoiseN4 $Nifti $outStr $outdir
```

2.  Once the denoise is ready run the surface processing module with the `-fastsurfer` and `-T1` flags
```bash
sub=PNC001
ses=01
bids=/data_/mica3/BIDS_PNI/rawdata
out=/data_/mica3/BIDS_PNI/derivatives
t1nlm=${out}/micapipe_v0.2.0/sub-${sub}/ses-${ses}/anat/sub-${sub}_ses-${ses}_space-nativepro_T1w_nlm.nii.gz

micapipe -sub ${sub} -ses ${ses} \
  -bids ${bids} \
  -out ${out} \
  -proc_surf -threads 15 \
  -fastsurfer -T1 ${t1nlm} -qsub
```

Fastsurfer QC
-------
The main outputs of `fastsurfer` deep volumetric segmentation are found under the `mri/` directory: `aparc.DKTatlas+aseg.deep.mgz`, `mask.mgz`, and `orig.mgz`. The equivalent of freesurfer's brainmask.mgz now is called `norm.mgz`.

1. The edits should be perfom on the `mask.mgz` file. However, maybe it's easier to correct over the file called `norm.mgz`. Once the edits are perform you can replace `mask.mgz` with the binarized version of the corrected `norm.mgz`.

```bash
# Convert from mgz to nifti
mri_convert norm.mgz norm.nii.gz

# Binarize nifti
fslmaths norm.nii.gz -bin mask.nii.gz

# Replace mask
rm mask.mgz
mri_convert mask.nii.gz mask.mgz

# removed intermediate files
rm mask.nii.gz norm.nii.gz norm.mgz~

# remove files previouslly created by the first run of recon-surf
rm wm.mgz aparc.DKTatlas+aseg.orig.mgz
```

2. Run the command `recon-surf.sh` using a singularity container to generate the new surfaces:
```
# Subject id
sub=sub-PNA002
ses=ses-01

# output directory
SUBJECTS_DIR=/data_/mica3/BIDS_PNI/derivatives/fastsurfer

# path to singularity image
fastsurfer_img=/data_/mica1/01_programs/fastsurfer/fastsurfer-cpu-v2.0.0.sif

# freesurfer licence
fs_licence=/data_/mica1/01_programs/freesurfer-7.3.2/

# Number of threads for parallel processing
threads=15

# Remove this variable from `env` because it could lead to an error withing the container
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

`micapipe` second stage modules
-------
1. Then the post structural processing and `dwi_proc`
```bash
micapipe -sub ${sub} -ses 01 \
         -bids /data_/mica3/BIDS_PNC/rawdata \
         -out /data_/mica3/BIDS_PNC/derivatives \
         -post_structural \
         -proc_dwi \
         -dwi_rpe rawdata/sub-${sub}/ses-01/fmap/sub-${sub}_ses-01_acq-b0_dir-PA_epi.nii.gz \ 
         -qsub
```

2. Once the post structural processing is ready run the `-GD` `-Morphology`, `-SC` and `-proc_func` with the corresponding arguments
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

# Processing times
# Rawdata size
| **Module**    | **Cores**| **Time min** |
|---------------|----------|--------------|
| `proc_struct` |   15     | 122 ± 16  |
| `proc_surf`   |   15     | 188 ± 36  |
| `post_struct` |   15     | 303 ± 41  |
| `proc_func`   |   15     |     ?     |
| `proc_dwi`    |   15     |     ?     |
| `SC`          |   15     |     ?     |
| `MPC`         |   10     |  14 ± 3   |
| `Morphology`  |   10     |   1 ± 0   |
| `GD`          |   10     |  96 ± 21  |
| *Total*       |    -     | 724 ± 117 |

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
