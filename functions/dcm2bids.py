#!/usr/bin/env python3
"""
This script converts DICOM files to BIDS format using the PNI 7T workflow.

Modules:
    os: Provides a way of using operating system dependent functionality.
    subprocess: Allows you to spawn new processes, connect to their input/output/error pipes, and obtain their return codes.
    tempfile: Generates temporary files and directories.
    bids_validator: Validates BIDS datasets.
    argparse: Parses command-line arguments.

Functions:
    run_command(command):
        Executes a shell command and raises an error if the command fails.
        Args:
            command (str): The command to be executed.
        Raises:
            subprocess.CalledProcessError: If the command execution fails.

    main():
        Main function that sets up the workflow for converting DICOMs to BIDS format.
        It creates a temporary directory, runs the necessary scripts, and validates the BIDS output.

Arguments:
    --dicoms_dir (str): Directory containing DICOM files.
    --bids_dir (str): Output BIDS directory.
    --sub (str): Subject ID, NO sub- string.
    --ses (str): Session ID, NO ses- string.
"""
import os
import subprocess
import argparse
import time

# Arguments
parser = argparse.ArgumentParser(description='Convert DICOMs to BIDS format.')
parser.add_argument('--sub', required=True, help='Subject ID')
parser.add_argument('--ses', required=True, help='Session ID')
parser.add_argument('--dicoms_dir', required=False, help='Directory containing DICOM files')
parser.add_argument('--sorted_dir', required=True, help='Directory containing SORTED DICOM files')
parser.add_argument('--bids_dir', required=True, help='Output BIDS directory')
parser.add_argument('--force', action='store_true', help='Optional argument to overwrite the subject bids directory')

args = parser.parse_args()
dicoms_dir = os.path.abspath(args.dicoms_dir) if args.dicoms_dir else None
bids_dir = os.path.abspath(args.bids_dir)
sorted_dir = os.path.abspath(args.sorted_dir)
sub = args.sub
ses = args.ses
force = args.force

# Remove strings if they exist in sub and ses
sub = sub.replace('sub-', '')
ses = ses.replace('ses-', '')

print('-------------------------------------------------------')
print('         PNI 7T - DICOM to BIDS workflow')
print('-------------------------------------------------------')
print(f'Subjet:             {sub}')
print(f'Session:            {ses}')
if dicoms_dir is not None:
    print(f'dicoms directory:   {dicoms_dir}')
print(f'sorted directory:   {sorted_dir}')
print(f'bids directory:     {bids_dir}')
if force:
    print(f'Overwrite subject:   {force}')
    force_flag=' -force'
else:
    force_flag=''
# Function to run a command
def run_command(command):
    try:
        print(f"Running command: {command}")
        subprocess.run(command.split(), check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: Exception: {e}")

# Workflow steps
def sorted2bids():
    print("\n[ info ] ... Running Sorted dicoms to BIDS ...\n")
    run_command(f'7t2bids -in {sorted_dir} -id {sub} -ses {ses} -bids {bids_dir}{force_flag}')

def validate_bids():
    print("\n[ info ] ... Running BIDS validator ...\n")
    command = f'deno run --allow-write -ERN jsr:@bids/validator {bids_dir} --ignoreWarnings --outfile {bids_dir}/bids_validator_output.txt'
    run_command(command)

def main():
    # Set a timer
    start_time = time.time()

    # Check if sorted_dir exists, and create it if it doesn't
    if not os.path.exists(sorted_dir):
        print("\n[info] ... Creating sorted dicoms directory\n")
        os.makedirs(sorted_dir)

    if dicoms_dir is None:
        # Case 1: NO dicoms_dir & sorted_dir is empty (ERROR)
        # If sorted_dir is empty, exit and error
        if not os.listdir(sorted_dir):
            print("\n[error] ... Sorted directory is empty\n")
            print(sorted_dir)
            return
        # Case 2: NO dicoms_dir & sorted_dir with dicoms directories
        sorted2bids()
    else:
        # Case 3: dicoms_dir provided (run the full pipeline)
        # Run sorting and then sorted2bids
        print("\n[step 1] ... Running sorting of dicoms ...\n")
        run_command(f'dcmSort.py {dicoms_dir} {sorted_dir}')

        print("\n[step 2] ... Running sorted2bids ...\n")
        sorted2bids()

    # Run validate_bids
    validate_bids()

    # Print validate_bids output
    with open(os.path.join(bids_dir, 'bids_validator_output.txt'), 'r') as file:
        print(file.read())
        
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Workflow completed successfully in {minutes:.0f} minutes and {seconds:.0f} seconds.")
    print('-------------------------------------------------------')

if __name__ == "__main__":
    main()