# Precision NeuroImaging 7T

[![version](https://img.shields.io/github/v/tag/MICA-MNI/MICA-7t)](https://github.com/MICA-MNI/MICA-7t)
[![Docker Image Version](https://img.shields.io/docker/v/micalab/7t2bids?color=blue&label=docker%20version)](https://hub.docker.com/r/micalab/7t2bids)
[![License: GPL v3](https://img.shields.io/github/license/MICA-MNI/MICA-7t?color=blue)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub issues](https://img.shields.io/github/issues/MICA-MNI/MICA-7t)](https://github.com/MICA-MNI/MICA-7t/issues)
[![GitHub stars](https://img.shields.io/github/stars/MICA-MNI/MICA-7t.svg?style=flat&label=⭐%EF%B8%8F%20stars&color=brightgreen)](https://github.com/rcruces/7T_pipeline/stargazers)


Scripts for sorting, organizing and processing the 7T database
=======
## 0 Running the protocol with `Aaron`
```bash
# 1. log in to Aaron, source and activate conda environments 
source /export02/local/conda/etc/profile.d/conda.sh

# 2. conda envt for Day 1 and 2 
conda activate py38env

# 3. conda envt for Day 3 and 4
conda activate py382env

# 4. go to 7T dir
cd /data/mica3/7T_task_fMRI/from_micaopen/micaopen/7T_task_fMRI

# 5. open the GUI 
python run_tasks.py

# 6. if running Day 3 or 4, open another terminal and repeat the 1-4 steps then

python test_vlc.py

# Running GUI with mica laptop
source /home/mica/Desktop/conda/etc/profile.d/conda.sh
conda activate py39env
cd 7T_cp
python run_tasks.py

```
## 1 . Transfering the data
The files from the 7t scan are in `/data/dicom/PNC001_Day1_?????`. First, find and claim data using `find_mri` and  `find_mri -claim` script. Then copy 7T data to our folder /data/mica3/BIDS_PNI/sorted/sub-${SUBID}_${ses}/dicoms.
```bash
SUBID=PNC001
ses1=01
ses=ses-${ses1}
find_mri ${SUBID}
find_mri -claim ${dicoms_directory}

# Create the directories
mkdir -p /host/verges/tank/data/BIDS_PNI/sorted/sub-${SUBID}_${ses}/{beh,dicoms,dicoms_sorted}

# Copy the DICOMS
cp -r ${dicoms_directory_returned_from_previous_command}/*  /host/verges/tank/data/BIDS_PNI/sorted/sub-${SUBID}_${ses}/dicoms
```

## 2. Integrated workflow from DICOMS to BIDS
This workflow is composed of three modular steps: the first sorts the DICOMs to `/data_/mica3/BIDS_PNI/sorted/sub-XXX000_ses-xx`, then it converts the sorted DICOMs into BIDS, and finally, it runs a BIDS validation.

> **Note**: this workflow replaces the previous Bash scripts `dcmSort` and `7t2bids`. `dcmSort` was updated and rewritten in Python using `pydicom`. `7t2bids` is still integrated in the workflow.

### Singularity command:
```bash
sub=PNE018
ses=a1

# Variables
data_dir="/data_dir="/host/verges/tank/data/BIDS_PNI"
bids_dir="/data_/mica3/BIDS_PNI/rawdata"
dicoms_dir="${data_dir}/sorted/sub-${sub}_ses-${ses}/dicoms"
sorted_dir="${data_dir}/sorted/sub-${sub}_ses-${ses}/dicoms_sorted"

# Path to singularity image v2.2
dcm2bids_img=/data/mica1/01_programs/MICA-7t/7t2bids_v2.2.sif

# Run dcm2bids.py with singularity container
singularity run --containall \
	-B "${bids_dir}":"${bids_dir}" \
	-B "${dicoms_dir}":"${dicoms_dir}" \
	-B "${sorted_dir}":"${sorted_dir}" \
    "${dcm2bids_img}" --sub "${sub}" --ses "${ses}" \
        --dicoms_dir "${dicoms_dir}" \
        --sorted_dir "${sorted_dir}" \
        --bids_dir "${bids_dir}"
```

## 3. Copy behavior data
This step is to copy the behavior data from cognitive tasks.
```bash
cp -r /data/mica3/7T_task_fMRI/7T_task_fMRI/logs/sub-${SUBID}/$ses/beh/* /data/mica3/BIDS_PNI/sorted/sub-${SUBID}_${ses}/beh/
```
Please note that for Day3 we use different folder for now, and the rs-fMRI data is also named as different name (ses-03_2). The script should be therefore replace with:
```bash
cp -r /data/mica3/7T_task_fMRI/7T_task_fMRI_NE/logs/sub-${SUBID}/$ses/beh/* /data/mica3/BIDS_PNI/sorted/sub-${SUBID}_${ses}/beh/
cp -r /data/mica3/7T_task_fMRI/7T_task_fMRI_NE/logs/sub-${SUBID}/${ses}2/beh/* /data/mica3/BIDS_PNI/sorted/sub-${SUBID}_${ses}/beh/
```

Processing 7T with `micapipe`
=======
You can run any module of the pipeline locally (`-mica`), on the mica.q (`-qsub`) or all.q (`-qall`). But you should always use one of these flags.

0. Set singularity environment and directories 


```bash
#!/bin/bash
# micapipe v0.2.0 "Northern Flicker"

sub=PNC001
ses=01

# Variables
bids=/data/mica3/BIDS_PNI/rawdata/
out=/data/mica3/BIDS_PNI/derivatives
tmp=/host/percy/local_raid/donna/useful/7T_processing/tmp_dir
fs_lic=/data_/mica1/01_programs/freesurfer-7.3.2/license.txt

# run this container
micapipe_img=/data_/mica1/01_programs/micapipe-v0.2.0/micapipe_v0.2.3.sif

```

`micapipe` first stage modules: structural processing
-------
1. First run the structural processing with the flag `-uni` for MP2RAGE 7T data
```
#There are two uni images with 0.5mm and 0.7mm, for our purposes, we only process 0.5mm
# call singularity
singularity run --writable-tmpfs --containall \
	-B ${bids}:/bids \
	-B ${out}:/out \
	-B ${tmp}:/tmp \
	-B ${fs_lic}:/opt/licence.txt \
	${micapipe_img} \
	-bids /bids -out /out -fs_licence /opt/licence.txt -threads 6 -sub ${sub} -ses ${ses} \
	-proc_structural -uni -T1wStr acq-05mm_UNIT1,acq-05mm_inv-1_MP2RAGE,acq-05mm_inv-2_MP2RAGE

```

Surface processing
-------
2.  Here we run a denoising algorithm on the `t1nativepro` to enhance contrast in grey/white matter to facilitate the surface generation.
> This step might be incorporated into the pipeline in the future but is still work on progress...

```bash
# cd to micapipe subject directory
id1=sub-PNC018/ses-01/
id=sub-PNC018_ses-01

Nifti=${id1}/anat/${id/\//_}_space-nativepro_T1w.nii.gz
outStr=${id/\//_}_space-nativepro_T1w_nlm
outdir=${id1}/anat

bash /host/yeatman/local_raid/rcruces/git_here/MRI_analytic_tools/Freesurfer_preprocessing/denoiseN4 $Nifti $outStr $outdir 15
```

2.  Once the denoised data is ready, run the surface processing module with the `-fastsurfer` and `-T1` flags
```bash

# Variables
bids=/data/mica3/BIDS_PNI/rawdata/
out=/data/mica3/BIDS_PNI/derivatives
tmp=/host/percy/local_raid/donna/useful/7T_processing/tmp_dir
fs_lic=/data_/mica1/01_programs/freesurfer-7.3.2/license.txt

# run this container
micapipe_img=/data_/mica1/01_programs/micapipe-v0.2.0/micapipe_v0.2.3.sif

#make sure to mount this, otherwise, it won't work
t1nlm=${out}/micapipe_v0.2.0/sub-${sub}/ses-${ses}/anat/sub-${sub}_ses-${ses}_space-nativepro_T1w_nlm.nii.gz

# call singularity
singularity run --writable-tmpfs --containall \
	-B ${bids}:/bids \
	-B ${out}:/out \
	-B ${tmp}:/tmp \
	-B ${fs_lic}:/opt/licence.txt \
    -B ${t1nlm}:/opt/T1.nii.gz \
	${micapipe_img} \
	-bids /bids -out /out -fs_licence /opt/licence.txt -threads 6 -sub ${sub} -ses ${ses} \
	-proc_surf -T1 /opt/T1.nii.gz
```

Run CNN 
-------
c/o Donna 
Note: CNN generated masks should be applied to Fastsurfer before manual QC

To apply the mask: 

```bash
# 1. Generate the new binary mask from the CNN inference

mask_inference=/host/percy/local_raid/donna/7T_NNunet/new/nnUNet_results/Dataset500_Segmentation/nnUNetTrainer__nnUNetPlans__3d_fullres/inference/PNC_118.nii.gz
fsdir=/data/mica3/BIDS_PNI/derivatives/fastsurfer/sub-PNC018_ses-01

#2. Erase the mask and the norm
rm ${fsdir}/mri/mask.mgz ${fsdir}/mri/norm.mgz

#3. Replace the mask
mri_convert $mask_inference ${fsdir}/mri/mask.mgz

#4.  Multiply the orig_nu.mgz with the inference_mask
mrconvert ${fsdir}/mri/orig_nu.mgz ${fsdir}/mri/orig_nu.nii.gz
fslmaths $mask_inference -mul ${fsdir}/mri/orig_nu.nii.gz ${fsdir}/mri/norm.nii.gz

#5. Convert norm.nii.gz to mgz
mrconvert ${fsdir}/mri/norm.nii.gz ${fsdir}/mri/norm.mgz

#6.  Remove files previouslly created by the first run of recon-surf
rm ${fsdir}/mri/wm.mgz ${fsdir}/mri/aparc.DKTatlas+aseg.orig.mgz ${fsdir}/mri/orig_nu.nii.gz

#7. re-run fastsurfer
sub=PNC018
ses=01
/data/mica1/01_programs/MICA-7t/functions/post-qc_fastsurfer.sh -sub ${sub} -ses ${ses} \
         -out /data_/mica3/BIDS_PNI/derivatives/fastsurfer
```
Fastsurfer QC
-------
The main outputs of `fastsurfer` deep volumetric segmentation are found under the `mri/` directory: `aparc.DKTatlas+aseg.deep.mgz`, `mask.mgz`, and `orig.mgz`. The equivalent of freesurfer's brainmask.mgz now is called `norm.mgz`.

Warning!! Please make sure your eraser and brush values when editing are set to zero, otherwise, it will create issues on the subsequent steps.

1. The edits should be perfom on the `mask.mgz` file. However, maybe it's easier to correct over the file called `norm.mgz`. Once the edits are perform you can replace `mask.mgz` with the binarized version of the corrected `norm.mgz`.

2. Run the next script after you are done with the edits. It will create new surfaces based on on the edits and generate a file named `qc_done.txt` under the subject's directory e.g. `fastsurfer/sub-PNC018_ses-01`.

```bash
sub=PNC018
ses=01
/data/mica1/01_programs/MICA-7t/functions/post-qc_fastsurfer.sh -sub ${sub} -ses ${ses} \
         -out /data_/mica3/BIDS_PNI/derivatives/fastsurfer
```
<details><summary>post-qc_fastsurfer.sh details</summary>
<p>

#### `post-qc_fastsurfer.sh` will do the next steps:
```bash
# Convert from mgz to nifti
mri_convert norm.mgz norm.nii.gz

# --- IF YOU EDIT THE norm.mgz
# Binarize the mask edits
fslmaths norm.nii.gz -thr 1 -uthr 1 -binv mask_edited.nii.gz

# Generate the new mask from the norm.nii.gz edited
fslmaths norm.nii.gz -mul mask_edited.nii.gz -bin mask.nii.gz

# Generate the new norm multiplying the mask
fslmaths norm.nii.gz -mul mask.nii.gz norm.nii.gz

# Replace mask
rm mask.mgz norm.mgz norm.mgz~
mri_convert mask.nii.gz mask.mgz
mri_convert norm.nii.gz norm.mgz

# remove nifitis
rm mask_edited.nii.gz mask.nii.gz norm.nii.gz

# remove files previouslly created by the first run of recon-surf
rm wm.mgz aparc.DKTatlas+aseg.orig.mgz
```

Run the command `recon-surf.sh` using a singularity container to generate the new surfaces:
```
# Subject id
sub=sub-PNC018
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

touch ${SUBJECTS_DIR}/${sub}_${ses}/qc_done.txt
```
</p>
</details>

`micapipe` second stage modules
# One shot processing after reconsurf
```

bids=/data/mica3/BIDS_PNI/rawdata/
out=/data/mica3/BIDS_PNI/derivatives
tmp=/host/percy/local_raid/donna/useful/7T_processing/tmp_dir
fs_lic=/data_/mica1/01_programs/freesurfer-7.3.2/license.txt

# run this container
micapipe_img=/data_/mica1/01_programs/micapipe-v0.2.0/micapipe_v0.2.3.sif

#define subject and session 
sub=sub-PNC018
ses=ses-01

# call singularity
singularity run --writable-tmpfs --containall \
	-B ${bids}:/bids \
	-B ${out}:/out \
	-B ${tmp}:/tmp \
	-B ${fs_lic}:/opt/licence.txt \
	 ${micapipe_img} -bids /bids -out /out \
	-sub ${sub} -ses ${ses} -fs_licence /opt/licence.txt -threads 10 \
        -post_structural \
	-proc_dwi -dwi_main /bids/${sub}/${ses}/dwi/${sub}_${ses}_acq-multib38_dir-AP_dwi.nii.gz,/bids/${sub}/${ses}/dwi/${sub}_${ses}_acq-multib70_dir-AP_dwi.nii.gz -dwi_rpe /bids/${sub}/${ses}/dwi/${sub}_${ses}_acq-b0_dir-PA_dwi.nii.gz -regSynth \
	-GD -proc_func \
	-mainScanStr task-rest_echo-1_bold,task-rest_echo-2_bold,task-rest_echo-3_bold \
	-func_pe /bids/${sub}/${ses}/fmap/${sub}_${ses}_acq-fmri_dir-AP_epi.nii.gz \
	-func_rpe /bids/${sub}/${ses}/fmap/${sub}_${ses}_acq-fmri_dir-PA_epi.nii.gz \
	-MPC -mpc_acq T1map -regSynth \
	-microstructural_img /bids/${sub}/${ses}/anat/${sub}_${ses}_acq-05mm_T1map.nii.gz \
	-microstructural_reg FALSE \
	-SC -tracts 40M

```
cleanup - Change the module name and subject name accordingly 
-------

```
micapipe_img=/data_/mica1/01_programs/micapipe-v0.2.0/micapipe_v0.2.3.sif
bids=/data/mica3/BIDS_PNI/rawdata_v2.0.0/
out=/data/mica3/BIDS_PNI/derivatives
fs_lic=/data_/mica1/01_programs/freesurfer-7.3.2/license.txt
tmp=/data/mica2/temporaryNetworkProcessing
sub=sub-PNC018
ses=ses-01
echo "cleaning ${idBIDS} directory"
micapipe_cleanup -sub "${sub}" \
        -ses "${ses}" \
        -bids '/data/mica3/BIDS_PNI/rawdata' \
        -out '/data/mica3/BIDS_PNI/derivatives' \
        -post_structural
```


# Processing times
| **Module**    | **Cores**|  **7T-PNI**  |  **3T-MICs** | **CPU**|
|---------------|----------|--------------|--------------|--------|
| `proc_struct` |   15     |   122 ± 16   |   48 ± 10    |   yes  |
| `proc_surf`   |   15     |   188 ± 36   |   961 ± 205  |   yes  |
| `post_struct` |   15     |   303 ± 41   |   75 ± 13    |   yes  |
| `proc_func`   |   15     |    94 ± 8    |   103 ± 7    |   yes  |
| `proc_dwi`    |   15     |       ?      |   184 ± 11   |   yes  |
| `SC`          |   15     |       ?      |   918 ± 299  |   yes  |
| `MPC`         |   10     |    14 ± 3    |   8 ± 2      |   no   |
| `GD`          |   10     |    96 ± 21   |   171 ± 25   |   yes  |
| `proc_flair`  |   10     |       -      |     2 ± 0    |   yes  |
| *Total*       |    -     |   818 ± 125  |       ±      |    -   |


## Processing times diferences between versions
|  `micapipe`      | `v0.1.4`   | `v0.2.0`   | Difference |
|------------------|------------|------------|------------|
|  `proc_struct`   | 88 ± 17    | 48 ± 10    | faster     |
|  `proc_surf`     | 961 ± 205  | ~120       | faster     |
|  `post_struct`   | 125 ± 14   | 75 ± 13    | faster     |
|  `proc_func`     | 101 ± 8    | 103 ± 7    | similar    |
|  `proc_dwi`      | 246 ± 37   | 184 ± 11   | faster     |
|  `SC`            | 906 ± 427  | 918 ± 299  | similar    |
|  `MPC`           | 7 ± 1      | 8 ± 2      | similar    |
|  `GD`            | 159 ± 21   | 171 ± 25   | slower     |
| *Total*          | 2593 ± 730 | 1627 ± 367 | 966 ± 363  |


# Derivatives size
| **Directory** | **size** |
|---------------|----------|
| freesurfer    | ~830     |
| micapipe/anat | ~820M    |
| micapipe/dwi  | 13G      |
| micapipe/func | 24G      |
| micapipe/maps |          |
| micapipe/surf |          |
| micapipe/logs | 31M      |
| micapipe/xfm  | 2.6G     |
| micapipe/QC   | 46M      |
| micapipe/     | ~10-40G  |


# Rawdata size
| **Directory** | **size** |
|---------------|----------|
| anat          | 495M     |
| dwi           | 1.2G     |
| fmap          | 15M      |
| func          | 7.7G     |
| *Total*       | 9.4G     |

# PNI 7T MRI acquisition protocol

## Anatomical
| Session  | Acquisition                                | BIDS dir | BIDS name              |
|----------|--------------------------------------------|----------|------------------------|
| 01/02/03 | "*anat-T1w_acq-mprage_07mm_UP"             | anat     | acq-mprage_T1w         |
| ?        | "*anat-T1w_acq-mp2rage_07mm_CSptx_INV1"    | anat     | inv-1_MP2RAGE          |
| ?        | "*anat-T1w_acq-mp2rage_07mm_CSptx_INV2"    | anat     | inv-2_MP2RAGE          |
| ?        | "*anat-T1w_acq-mp2rage_07mm_CSptx_T1_Images" | anat   | T1map                  |
| ?        | "*anat-T1w_acq-mp2rage_07mm_CSptx_UNI_Images" | anat  | UNIT1                  |
| ?        | "*anat-T1w_acq-mp2rage_07mm_CSptx_UNI-DEN" | anat     | desc-denoised_UNIT1    |
| ?        | "*cstfl-mp2rage-05mm_INV1"                 | anat     | acq-05mm_inv-1_MP2RAGE |
| ?        | "*cstfl-mp2rage-05mm_INV2"                 | anat     | acq-05mm_inv-2_MP2RAGE |
| ?        | "*cstfl-mp2rage-05mm_T1_Images"            | anat     | acq-05mm_T1map         |
| ?        | "*cstfl-mp2rage-05mm_UNI_Images"           | anat     | acq-05mm_UNIT1         |
| ?        | "*cstfl-mp2rage-05mm_UNI-DEN"              | anat     | acq-05mmDenoised_UNIT1 |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP*_INV1"       | anat     | acq-inv1_T1map         |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP*_INV2"       | anat     | acq-inv2_T1map         |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP*_T1_Images"  | anat     | acq-T1_T1map           |
| 01/02/03 | "*anat-T1w_acq-mp2rage_05mm_UP*_UNI_Images" | anat     | acq-uni_T1map          |
| a1       | "*anat-flair_acq-0p7mm_UPAdia"              | anat     | FLAIR                  |
| ?        | "*anat-flair_acq-07iso_dev3_5SD_UP"         | anat     | FLAIR                  |
| a1       | "*CLEAR-SWI_anat-T2star_acq-me_gre_0*7iso_ASPIRE"    | anat | acq-SWI_T2starw   |
| a1       | "*Romeo_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE" | anat | acq-romeo_T2starw      |
| a1       | "*Romeo_Mask_anat-T2star_acq-me_gre_0*7iso_ASPIRE"   | anat | acq-romeo_desc-mask_T2starw   |
| a1       | "*Romeo_B0_anat-T2star_acq-me_gre_0*7iso_ASPIRE" | anat | acq-romeo_desc-unwrapped_T2starw  |
| a1       | "*Aspire_M_anat-T2star_acq-me_gre_0*7iso_ASPIRE"     | anat | acq-aspire_part-mag_T2starw   |
| a1       | "*Aspire_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE"     | anat | acq-aspire_part-phase_T2starw |
| a1       | "*EchoCombined_anat-T2star_acq-me_gre_0*7iso_ASPIRE" | anat | acq-aspire_desc-echoCombined_T2starw |
| a1       | "*sensitivity_corrected_mag_anat-T2star_acq-me_gre_0*7iso_ASPIRE" | anat | acq-aspire_desc-echoCombinedSensitivityCorrected_T2starw |
| a1       | "*T2star_anat-T2star_acq-me_gre_0*7iso_ASPIRE" | anat | acq-aspire_[T2starw,T2starmap] |
| 02/03    | "*anat-T2star_acq-me_gre_07mm"             | anat     | acq-me_T2starw         |
| 02/03    | "*T2Star_Images"                           | anat     | acq-me_T2starmap       |
| 03       | "*_MTON"                                   | anat     | mt-on_MTR              |
| 03       | "*_MTOFF"                                  | anat     | mt-off_MTR             |
| 03       | "*_T1W"                                    | anat     | acq-MTR_T1w            |
| ?        | "*anat-mtw_acq-MTON_07mm"                  | anat     | acq-mtw_mt-on_MTR      |
| ?        | "*anat-mtw_acq-MTOFF_07mm"                 | anat     | acq-mtw_mt-off_MTR     |
| ?        | "*anat-mtw_acq-T1w_07mm"                   | anat     | acq-mtw_acq-MTR_T1w    |
| 03       | "*anat-angio_acq-tof_03mm_inplane"         | anat     | angio                  |
| 03       | "*anat-angio_acq-tof_03mm_inplane_MIP_SAG" | anat     | acq-sag_angio          |
| 03       | "*anat-angio_acq-tof_03mm_inplane_MIP_COR" | anat     | acq-cor_angio          |
| 03       | "*anat-angio_acq-tof_03mm_inplane_MIP_TRA" | anat     | acq-tra_angio          |

> The acquisitions `acq-romeo_part-phase_T2starw`, `acq-aspire_part-mag_T2starw`, and `acq-aspire_part-phase_T2starw` each have five echoes. The final string will include the identifier `echo-` followed by the echo number. For example: `acq-aspire_echo-1_part-mag_T2starw`.

## Field maps
| Session     | Acquisition                                | BIDS dir | BIDS name              |
|-------------|--------------------------------------------|----------|------------------------|
| 01/02/03/a1 | "*fmap-b1_acq-tra_p2"                      | fmap     | acq-[anat,sfam]_TB1TFL |
| 01/02/03/a1 | "*fmap-b1_acq-sag_p2"                      | fmap     | acq-[anat,sfam]_TB1TFL |
| 01/02/03    | "*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP*"    | fmap     | acq-fmri_dir-AP_epi    |
| 01/02/03    | "*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA*"    | fmap     | acq-fmri_dir-PA_epi    |

## Functional MRI
| Session  | Acquisition                                | BIDS dir | BIDS name              |
|----------|--------------------------------------------|----------|------------------------|
| ?        | "*func-rsfmri_acq-singleE_1*"              | func     | acq-singleE_task-rest_bold |
| 01/02/03 | "*func-rsfmri_acq-mbep2d_ME_19mm"          | func     | task-rest_bold         |
| 01       | "*func-epiencode_acq-mbep2d_ME_19mm"       | func     | task-epiencode_bold    |
| 01       | "*func-epiretrieve_acq-mbep2d_ME_19mm"     | func     | task-epiretrieve_bold  |
| 01       | "*func-pattersep1_acq-mbep2d_ME_19mm"      | func     | task-patternsep1_bold  |
| 01       | "*func-patternsep2_acq-mbep2d_ME_19mm"     | func     | task-patternsep2_bold  |
| 02       | "*func-semantic1_acq-mbep2d_ME_19mm"       | func     | task-semantic1_bold    |
| 02       | "*func-semantic2_acq-mbep2d_ME_19mm"       | func     | task-semantic2_bold    |
| 02       | "*func-spatial1_acq-mbep2d_ME_19mm"        | func     | task-spatial1_bold     |
| 02       | "*func-spatial2_acq-mbep2d_ME_19mm"        | func     | task-spatial2_bold     |
| 03       | "*func-movie*1_acq-mbep2d_ME_19mm"         | func     | task-movies1_bold      |
| 03       | "*func-movie*2_acq-mbep2d_ME_19mm"         | func     | task-movies2_bold      |
| 03       | "*func-movies3_acq-mbep2d_ME_19mm"         | func     | task-movies3_bold      |
| 03       | "*func-movies4_acq-mbep2d_ME_19mm"         | func     | task-movies4_bold      |
| ?        | "*func-semphon1_acq-mbep2d_ME_19mm"        | func     | task-semphon1_bold     |
| ?        | "*func-semphon2_acq-mbep2d_ME_19mm"        | func     | task-semphon2_bold     |
| ?        | "*func-audiobook1_acq-mbep2d_ME_19mm"      | func     | task-audiobook1_bold   |
| ?        | "*func-audiobook2_acq-mbep2d_ME_19mm"      | func     | task-audiobook2_bold   |
| ?        | "*func-sens1_acq-mbep2d_ME_19mm"           | func     | task-sens2_bold        |
| ?        | "*func-sens2_acq-mbep2d_ME_19mm"           | func     | task-sens1_bold        |
| ?        | "*func-slient1_acq-mbep2d_ME_19mm"         | func     | task-salient_bold      |

> Each functional MRI acquisition includes three echoes and a phase. The final string will contain the identifier `echo-` followed by the echo number (e.g., `task-rest_echo-1_bold`). Additionally, the string `part-phase` will be included to identify the phase (e.g., `task-rest_echo-1_part-phase_bold`).

## Diffusion weighted Imaging
| Session  | Acquisition                              | BIDS dir | BIDS name                  |
|----------|------------------------------------------|----------|----------------------------|
| 01/02/a1 | "*dwi_acq_b0-dir_PA_SBRef"               | dwi      | acq-b0_dir-PA_sbref        |
| 01/02/a1 | "*dwi_acq_b0-dir_PA"                     | dwi      | acq-b0_dir-PA_dwi          |
| 01/02/a1 | "*dwi_acq_b0_PA_SBRef"                   | dwi      | acq-b0_dir-PA_sbref        |
| 01/02/a1 | "*dwi_acq_b0_PA"                         | dwi      | acq-b0_dir-PA_dwi          |
| ?        | "*dwi_acq_b0_PA_1p5iso_SBRef"            | dwi      | acq-b0_dir-PA_sbref        |
| ?        | "*dwi_acq_b0_PA_1p5iso"                  | dwi      | acq-b0_dir-PA_dwi          |
| 01/02    | "*dwi_acq_b2000_90d-dir_AP_SBRef"        | dwi      | acq-b2000_dir-AP_sbref     |
| 01/02    | "*dwi_acq_b2000_90d-dir_AP"              | dwi      | acq-b2000_dir-AP_dwi       |
| 01/02    | "*dwi_acq_b700_40d-dir_AP_SBRef"         | dwi      | acq-b700_dir-AP_sbref      |
| 01/02    | "*dwi_acq_b700_40d-dir_AP"               | dwi      | acq-b700_dir-AP_dwi        |
| 01/02    | "*dwi_acq_b300_10d-dir_AP_SBRef"         | dwi      | acq-b300_dir-AP_sbref      |
| 01/02    | "*dwi_acq_b300_10d-dir_AP"               | dwi      | acq-b300_dir-AP_dwi        |
| a1       | "*dwi_acq_multib_38dir_AP_acc9_SBRef"    | dwi      | acq-multib38_dir-AP_sbref  |
| a1       | "*dwi_acq_multib_38dir_AP_acc9"          | dwi      | acq-multib38_dir-AP_dwi    |
| a1       | "*dwi_acq_multib_38dir_AP_acc9_1p5iso_SBRef" | dwi   | acq-multib38_dir-AP_sbref |
| a1       | "*dwi_acq_multib_38dir_AP_acc9_1p5iso"   | dwi      | acq-multib38_dir-AP_dwi    |
| a1       | "*dwi_acq_multib_38dir_AP_acc9_test_SBRef" | dwi    | acq-multib38_dir-AP_sbref  |
| a1       | "*dwi_acq_multib_38dir_AP_acc9_test"     | dwi      | acq-multib38_dir-AP_dwi    |
| a1       | "*dwi_acq_multib_70dir_AP_acc9_SBRef"    | dwi      | acq-multib70_dir-AP_sbref  |
| a1       | "*dwi_acq_multib_70dir_AP_acc9"          | dwi      | acq-multib70_dir-AP_dwi    |
| a1       | "*dwi_acq_multib_70dir_AP_acc9_1p5iso_SBRef" | dwi   | acq-multib70_dir-AP_sbref |
| a1       | "*dwi_acq_multib_70dir_AP_acc9_1p5iso"   | dwi      | acq-multib70_dir-AP_dwi    |

### Abbreviation Glossary

| **Abbreviation** | **Description**                                               |
|-------------------|---------------------------------------------------------------|
| **AP**           | Anterio-Posterior                                             |
| **PA**           | Postero-anterior                                              |
| **mtw**          | Magnetic transfer weighted                                    |
| **sfmap**         | Scaled flip angle map                                        |
| **tof**          | Time of flight                                                |
| **multib**       | Multi shell N directions                                      |
| **semphon**      | Semantic-phonetic                                             |
| **romeo**        | Rapid opensource minimum spanning tree algorithm              |
| **aspire**       | Combination of multi-channel phase data from multi-echo acquisitions |

# References

1. Eckstein K, Dymerska B, Bachrata B, Bogner W, Poljanc K, Trattnig S, Robinson SD. Computationally efficient combination of multi‐channel phase data from multi‐echo acquisitions (ASPIRE). Magnetic resonance in medicine. 2018 Jun;79(6):2996-3006. https://doi.org/10.1002/mrm.26963

2. Dymerska B, Eckstein K, Bachrata B, Siow B, Trattnig S, Shmueli K, Robinson SD. Phase unwrapping with a rapid opensource minimum spanning tree algorithm (ROMEO). Magnetic resonance in medicine. 2021 Apr;85(4):2294-308. https://doi.org/10.1002/mrm.28563

3. Sasaki M, Shibata E, Tohyama K, Takahashi J, Otsuka K, Tsuchiya K, Takahashi S, Ehara S, Terayama Y, Sakai A. Neuromelanin magnetic resonance imaging of locus ceruleus and substantia nigra in Parkinson's disease. Neuroreport. 2006 Jul 31;17(11):1215-8. https://doi.org/10.1097/01.wnr.0000227984.84927.a7 
