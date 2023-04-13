#!/bin/bash
#
# Post QC fastsurfer workflow
#

#---------------- Enviroment ----------------#
# Set freesurfer 7 default enviroment
PATH=$(IFS=':';p=($PATH);unset IFS;p=(${p[@]%%*Freesurfer*});IFS=':';echo "${p[*]}";unset IFS)
unset FSFAST_HOME SUBJECTS_DIR MNI_DIR
export FREESURFER_HOME=/data_/mica1/01_programs/freesurfer-7.3.2 && export MNI_DIR=${FREESURFER_HOME}/mni && source ${FREESURFER_HOME}/FreeSurferEnv.sh
export PATH=${FREESURFER_HOME}/bin/:${FSLDIR}:${FSL_BIN}:${PATH}

#---------------- FUNCTION: HELP ----------------#
help() {
echo -e "
\033[38;5;141mCOMMAND:\033[0m
   $(basename $0)


\033[38;5;141mARGUMENTS:\033[0m
\t\033[38;5;197m-sub\033[0m 	          : Subject identification
\t\033[38;5;120m-ses\033[0m 	          : OPTIONAL flag that indicates the session name (if omitted will manage as SINGLE session)
\t\033[38;5;197m-out\033[0m 	          : Path to fastsurfer outputs directory e.g. <derivatives/fastsurfer>

\033[38;5;141mOPTIONS:\033[0m
\t\033[38;5;197m-h|-help\033[0m           : Print help
\t\033[38;5;197m-quiet\033[0m 	          : Do not print comments
\t\033[38;5;197m-threads\033[0m           : Number of threads (Default is 10)
\t\033[38;5;197m-tmpDir\033[0m            : Specify location of temporary directory <path> (Default is /tmp)


\033[38;5;141mUSAGE:\033[0m
    \033[38;5;141m$(basename $0)\033[0m  \033[38;5;197m-sub\033[0m <subject_id> \033[38;5;197m-out\033[0m <outputDirectory> \033[38;5;197m-bids\033[0m <BIDS-directory> \033[38;5;197m-proc_structural\033[0m \033[38;5;197m-proc_freesurfer\033[0m

\033[38;5;141mDOCUMENTATION:\033[0m
    https://github.com/MICA-MNI/micapipe

\033[38;5;141mDEPENDENCIES:\033[0m
    > FSL         6.0.3     (https://fsl.fmrib.ox.ac.uk/fsl/fslwiki)
    > Freesurfer  7.3.2
    > fastsurfer  2.0.0   (https://www.mrtrix.org)

McGill University, MNI, MICA-lab
https://github.com/MICA-MNI/micapipe
http://mica-mni.github.io/
"
}

#			ARGUMENTS
# Create VARIABLES
argCP="$@"
for arg in "$@"
do
  case "$arg" in
  -h|-help)
    help
    exit 1
  ;;
  -sub)
    id=$2
    shift;shift
  ;;
  -out)
    out=$2
    shift;shift
  ;;
  -ses)
    SES=$2
    shift;shift
  ;;
  -tmpDir)
    tmpDir=$2
    shift;shift;
  ;;
  -threads)
    threads=$2
    shift;shift
  ;;
  -quiet)
    quiet=TRUE
    shift
  ;;
  -*)
    echo "[ERROR] Unknown option ${2}"
    help
    exit 1
  ;;
    esac
done

# Missing argument error
arg=($id $out)
if [ ${#arg[@]} -lt 2 ]; then
echo "[ERROR] One or more mandatory arguments are missing:
                 -sub  : $id
                 -out  : $out
          		 -h | -help (print help)"
 exit 1; fi


# Inputs
out=$(realpath "$out")
id=${id/sub-/}
subject="sub-${id}"
here=$(pwd)

# Number of session (Default is "ses-pre")
if [ -z ${SES} ]; then SES="SINGLE"; else SES="ses-${SES/ses-/}"; fi
# Handle Single Session
if [ "$SES" == "SINGLE" ]; then ses=""; else ses="_${SES}"; fi
export idBIDS="${subject}${ses}"

# test if the subjects directory exists
if [[ ! -d ${out}/${idBIDS} ]]; then echo -e "[ERROR] subjects fastsurfer directory does not exist or the path is wrong:\n\t\t${out}/${idBIDS}"; exit 1; fi

# output directory
SUBJECTS_DIR=${out}

# Check if the subject has been re-run 
if [[ -f ${SUBJECTS_DIR}/${idBIDS}/qc_done.txt ]]; then echo "[WARNING] ${idBIDS} has been QC and run"; exit 1; fi

# Move to the subjects directory
cd ${out}/${idBIDS}/mri

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

# Run the command recon-surf.sh using a singularity container to generate the new surfaces:
# path to singularity image
fastsurfer_img=/data_/mica1/01_programs/fastsurfer/fastsurfer-cpu-v2.0.0.sif

# freesurfer licence
fs_licence=/data_/mica1/01_programs/freesurfer-7.3.2/

# Number of threads for parallel processing
if [[ -z $threads ]]; then export threads=10; fi

# Remove this variable from `env` because it could lead to an error withing the container
unset TMPDIR

# Run only the surface recontruction with spectral spherical projection (fastsurfer default algorithm instead of freesurfer)
singularity exec --nv -B ${SUBJECTS_DIR}/${idBIDS}:/data \
                      -B "${SUBJECTS_DIR}":/output \
                      -B "${fs_licence}":/fs \
                       ${fastsurfer_img} \
                       /fastsurfer/recon_surf/recon-surf.sh \
                      --fs_license /fs/license.txt \
                      --t1 /data/mri/orig.mgz \
                      --sid ${idBIDS} --sd /output --no_fs_T1 \
                      --parallel --threads ${threads}
                      
# Change the outputs permission, in case that someone else has to work on them
chmod aug+wr -R ${SUBJECTS_DIR}/${idBIDS}

cd ${here}

touch ${SUBJECTS_DIR}/${idBIDS}/qc_done.txt
