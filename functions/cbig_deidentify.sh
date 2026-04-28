#!/bin/bash
# ----------------------------------------------------------
# Deface and rename anat images 
# for CBIG ingestion/data release
# ----------------------------------------------------------

# ----------------------------------------------------------
# Subjects and sessions
sub=$1
ses=$2

# micapipe version
version=v0.2.3

# 2.  Singularity image
img_singularity=/data/mica1/01_programs/micapipe-v0.2.0/micapipe_"${version}".sif

# 3. micapipe command
# Local variables
bids=/data_/mica3/BIDS_PNI/cbig/bids
out=/data_/mica3/BIDS_PNI/cbig/bids
fs_lic=/data_/mica1/01_programs/freesurfer-7.3.2/license.txt
tmpDir=/data/mica2/tmpDir
threads=15

# Create command string
command="singularity exec --writable-tmpfs --containall -B ${bids}:/bids -B ${out}:/out -B ${tmpDir}:/tmp -B ${fs_lic}:/opt/licence.txt ${img_singularity} /neurodocker/startup.sh "

denoise_mp2rage_sequences() {
    local sub="$1"
    local ses="$2"
    local bids="$3"
    local anat_dir="${bids}/sub-${sub}/ses-${ses}/anat"
    local anat_dir_singularity="/bids/sub-${sub}/ses-${ses}/anat"

    # Find all inv-1 files and extract the acquisition/run part
    mapfile -t mp2rage < <(
    find "$anat_dir" -type f -name "*_inv-1_MP2RAGE.nii.gz" \
    | sed -nE "s|.*/sub-${sub}_ses-${ses}_(acq-[^_]+_run-[^_]+)_inv-1_MP2RAGE.nii.gz|\1|p" \
    | sort -u
    )

    # If there are also files without acq/run (fallback case)
    if ls "$anat_dir"/sub-${sub}_ses-${ses}_inv-1_MP2RAGE.nii.gz &>/dev/null; then
        mp2rage+=("")
    fi

    # Loop over sequences
    for seq in "${mp2rage[@]}"; do
        if [[ -n "$seq" ]]; then
            suffix="_${seq}"
            MF=3
        else
            suffix=""
            MF=40
        fi

        bids_uni="${anat_dir_singularity}/sub-${sub}_ses-${ses}${suffix}_UNIT1.nii.gz"
        bids_inv1="${anat_dir_singularity}/sub-${sub}_ses-${ses}${suffix}_inv-1_MP2RAGE.nii.gz"
        bids_inv2="${anat_dir_singularity}/sub-${sub}_ses-${ses}${suffix}_inv-2_MP2RAGE.nii.gz"
        bids_uni_dns="${anat_dir_singularity}/sub-${sub}_ses-${ses}_desc-denoised${suffix}_UNIT1.nii.gz"

        # Denoising UNI image
        # Only run if the denoised file doesn't already exist
        if [[ ! -f "$bids_uni_dns" ]]; then
            echo -e "----------------------------------------------------------\n\tRunning MP2RAGE denoising on ${seq}\n----------------------------------------------------------"
            ${command} /opt/micapipe/functions/mp2rage_denoise.py "${bids_uni}" "${bids_inv1}" "${bids_inv2}" "${bids_uni_dns}" --mf "${MF}"

            # Copy the UNI json and add:
            bids_uni="${anat_dir}/sub-${sub}_ses-${ses}${suffix}_UNIT1.nii.gz"
            bids_uni_dns="${anat_dir}/sub-${sub}_ses-${ses}_desc-denoised${suffix}_UNIT1.nii.gz"
            cp "${bids_uni%.nii.gz}.json" "${bids_uni_dns%.nii.gz}.json"

            sed -i $'/^{/a\\\t"ImageComments": "Denoised Uniform Image (multiplying factor = '"$MF"')",' "${bids_uni_dns%.nii.gz}.json"
        else
            echo -e "\ntDenoised UNI image already exists for ${seq}, skipping MP2RAGE denoising\n"
        fi
    done
}

# ----------------------------------------------------------
# Timer
aloita=$(date +%s)

# ----------------------------------------------------------
# Denoise UNI images
denoise_mp2rage_sequences $sub $ses $bids

# ----------------------------------------------------------
# Run Defacer — select best available denoised UNIT1 file
for acq in "_acq-05mm" "_acq-05mm_run-1" ""; do
  uni="${bids}/sub-${sub}/ses-${ses}/anat/sub-${sub}_ses-${ses}_desc-denoised${acq}_UNIT1.nii.gz"
  [[ -f "$uni" ]] && break
done

if [[ ! -f "$uni" ]]; then echo "ERROR: No denoised UNIT1 file found"; fi

uni_dns="/bids/sub-${sub}/ses-${ses}/anat/sub-${sub}_ses-${ses}_desc-denoised${acq}_UNIT1.nii.gz"

echo -e "----------------------------------------------------------\n\tAnonymizing using reference: ${acq:-default}\n----------------------------------------------------------"
# micapipe_dev
micapipe_anonymize_v2 \
  -bids ${bids} -out ${out} -threads "${threads}" -sub "${sub}" -ses "${ses}" \
  -deface -reface -regSynth -robust \
  -T1 "$uni"

# Singularity
${command} /opt/micapipe/functions/micapipe_anonymize \
  -bids /bids -out /out -threads "${threads}" -sub "${sub}" -ses "${ses}" \
  -deface -reface -regSynth -robust \
  -T1 "$uni_dns"

# JSON keys to remove: InstitutionAddress, ProcedureStepDescription, AcquisitionTime
# Maybe: ProtocolName, SeriesDescription, ReceiveCoilName, 
# CBIG specific kys to remove: ??
# MICA specific keys to remove: ?? for REB compliance

# Processing time
lopuu=$(date +%s)
eri=$(echo "$lopuu - $aloita" | bc)
eri=$(echo print "$eri"/60 | perl)
echo -e "----------------------------------------------------------
Processing ended in $(printf "%0.3f\n" "$eri") minutes
----------------------------------------------------------"