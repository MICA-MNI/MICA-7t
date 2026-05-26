#!/usr/bin/env python3
import os
import sys
import shutil
import concurrent.futures
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

# REPLACED: bare pydicom.dcmread loop
def read_dicom_info(dicom):
    try:
        ds = pydicom.dcmread(dicom, stop_before_pixels=True)
    except Exception:
        return None
    series_date   = ds.get("SeriesDate",        "00000000")
    series_time   = str(ds.get("SeriesTime",    "000000")).split('.')[0]
    series_number = "{:02d}".format(int(ds.get("SeriesNumber", 0)))
    series_desc   = ds.get("SeriesDescription", "unknown")
    return (series_date, series_time, series_number, series_desc, dicom)

with concurrent.futures.ThreadPoolExecutor() as executor:
    results = executor.map(read_dicom_info, dicoms)
dicom_info = [r for r in results if r is not None]

# Add session numbers (UNCHANGED)
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

# REPLACED: sequential os.system('cp') loop
def copy_dicom(entry):
    series_date, series_time, series_number, series_description, dicom = entry
    session     = session_data[(series_date, series_time, series_number, series_description)]
    directory   = f'S{session}_{series_number}_{series_description}'
    output_path = os.path.join(output_directory, directory)
    os.makedirs(output_path, exist_ok=True)
    shutil.copy(dicom, output_path)

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(copy_dicom, dicom_info)