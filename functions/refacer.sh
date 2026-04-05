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
bids=/data_/mica3/BIDS_PNI/rawdata
out=/data_/mica3/BIDS_PNI/derivatives
tmpDir=/data/mica2/tmpDir
threads=15

# Create command string
command="singularity exec --writable-tmpfs --containall -B ${bids}:/bids -B ${out}:/out -B ${tmpDir}:/tmp -B ${fs_lic}:/opt/licence.txt ${img_singularity}"

# ----------------------------------------------------------
# Run Defacer
${command} /opt/micapipe/functions/micapipe_anonymize \
-bids /bids -out /out -threads ${threads} -sub ${sub} -ses ${ses} -deface \
-regSynth -robust

# ----------------------------------------------------------
# Rename Defaced images (keep log in CHANGES)
