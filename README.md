# MICA-7t
scripts for 7t sorting a organizing
=======
scripts for 7t sorting, organizing and processing data.

The files from the 7t scan are in `/data/transfer/dicoms`.  

1. The first step is to sort the dicoms to `/data_/mica3/MICA-7T/sorted`
```bash
dcmSort /data/transfer/dicoms/pilot3 /data_/mica3/MICA-7T/sorted/sub-pilot3
```
2. From sorted to BIDS
```bash
7t2bids -in /data_/mica3/MICA-7T/sorted/sub-pilot3 -id pilot3 -bids /data_/mica3/MICA-7T/rawdata -ses pilot
```

3. `micapipe`  
Here we run the first two steps, `proc_structural` and `proc_freesurfer`
```bash
mica-pipe -sub pilot3 -ses pilot -bids /data_/mica3/MICA-7T/rawdata \
    -out /data_/mica3/MICA-7T/derivatives \
    -proc_structural -proc_freesurfer -mica -threads 25
```
