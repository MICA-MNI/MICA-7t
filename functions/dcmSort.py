#!/usr/bin/env python3

import os
import sys
from collections import defaultdict
import pydicom

def print_help():
    print("""
COMMAND:
   dcmSort.py

ARGUMENTS:
   <pos1>        : Input directory with unsorted DICOMS
   <pos2>        : Output directory

USAGE:
    dcmSort.py <input_directory> <outputDirectory>
""")

if len(sys.argv) < 3:
    print("\n[ERROR]... A mandatory argument is missing:")
    print("      inputDirectory    : {}".format(sys.argv[1] if len(sys.argv) > 1 else ""))
    print("      outputDirectory   : {}".format(sys.argv[2] if len(sys.argv) > 2 else ""))
    print_help()
    sys.exit(1)

input_directory = sys.argv[1]
output_directory = sys.argv[2]

print("[ info ] ... Getting DICOM information...")

dicoms = [os.path.join(input_directory, f) for f in os.listdir(input_directory) if os.path.isfile(os.path.join(input_directory, f))]
dicom_info = []

for dicom in dicoms:
    ds = pydicom.dcmread(dicom)
    series_date = ds.SeriesDate
    series_time = ds.SeriesTime.split('.')[0]  # Remove any fractional seconds
    series_number = "{:02d}".format(int(ds.SeriesNumber))
    series_description = ds.SeriesDescription
    dicom_info.append((series_date, series_time, series_number, series_description, dicom))

# Add session numbers
dicom_info.sort()
session_data = defaultdict(int)
prev_id = 0
session = 1

for i, (series_date, series_time, series_number, series_description, dicom) in enumerate(dicom_info):
    id2 = int(series_number.lstrip('0'))
    if id2 < prev_id:
        session += 1
    prev_id = id2
    session_data[(series_date, series_time, series_number, series_description)] = session

# Copy to correct directory
print("[ info ] ... Sorting DICOMS...")
for series_date, series_time, series_number, series_description, dicom in dicom_info:
    # Retrieve data from dicom info
    session = session_data[(series_date, series_time, series_number, series_description)]

    # Create directory name
    directory = f'S{session}_{series_number}_{series_description}'

    # Output directory
    output_path = os.path.join(output_directory, directory)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    os.system(f'cp {dicom} {output_path}')