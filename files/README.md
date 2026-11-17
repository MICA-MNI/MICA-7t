# PNI: Precision Neuroimaging and Connectomics — MICA Lab

**Keywords:** precision neuroimaging, connectomics, epilepsy, autism, healthy controls, family members, multimodal MRI, ultra-high-field MRI, 7T MRI, structural MRI, diffusion MRI, DWI, functional MRI, resting-state fMRI, task-based fMRI, movie fMRI, quantitative MRI, microstructure, cortical gradients, longitudinal, BIDS

**Contact:** MICA Lab, Montreal Neurological Institute, McGill University  
boris.bernhardt@mcgill.ca

## Overview

PNI (Precision Neuroimaging and Connectomics) is a multimodal neuroimaging database developed by the Multimodal Imaging and Connectome Analysis (MICA) Lab at the Montreal Neurological Institute (MNI), McGill University.

The database was designed to support precision neuroimaging research through the acquisition and analysis of multimodal MRI data, combining structural, diffusion, quantitative, and functional imaging with complementary clinical and demographic information.

The PNI database includes multiple participant groups:

- **PNC:** Healthy controls
- **PNE:** Participants with epilepsy
- **PNA:** Participants with autism
- **PNF:** Family members
- **Pilot:** Pilot participants

The publicly released component of PNI, available through the Open Science Framework (OSF), comprises 10 healthy control participants scanned across three imaging sessions. The extended database includes additional healthy controls, clinical populations, family members, pilot participants, and longitudinal imaging sessions.

The public release is openly available, whereas the extended database is maintained internally by MICA Lab and is subject to McGill University data-sharing agreements (see `LICENSE`).

## Dataset summary (November 17, 2026)

The extended PNI database currently comprises **303 participant-sessions** across five participant groups: healthy controls (PNC), epilepsy (PNE), autism (PNA), family members (PNF), and pilot participants.

The distribution of participant-sessions across imaging sessions and participant groups is summarized below:

| Session | Total | Healthy (PNC) | Epilepsy (PNE) | Autism (PNA) | Family (PNF) | Pilot |
|---------|------:|--------------:|---------------:|-------------:|-------------:|------:|
| ses-01  | 34    | 26            | 1              | 7            | 0            | 0     |
| ses-02  | 21    | 20            | 0              | 1            | 0            | 0     |
| ses-03  | 14    | 13            | 0              | 1            | 0            | 0     |
| ses-04  | 12    | 11            | 0              | 1            | 0            | 0     |
| ses-05  | 4     | 1             | 0              | 0            | 0            | 3     |
| ses-a1  | 188   | 56            | 118            | 7            | 6            | 1     |
| ses-a2  | 24    | 6             | 15             | 2            | 0            | 1     |
| ses-a3  | 6     | 3             | 2              | 0            | 0            | 1     |
| **Total** | **303** | **136**    | **136**        | **19**       | **6**        | **6** |

**Total participant-sessions across the database: 303**

Note that these values represent participant-sessions rather than necessarily unique individuals. Participants may contribute data across multiple longitudinal sessions.

The publicly available OSF release corresponds to a subset of the healthy control (PNC) group and should be distinguished from the full internal PNI database.

## MRI acquisition protocols

The PNI dataset includes ultra-high-field (7T) MRI data acquired using two related acquisition protocols. Both protocols were designed to characterize individual brain anatomy, microstructure, and function using a combination of structural, diffusion, quantitative, and functional MRI acquisitions.

Protocol 1 corresponds to sessions `ses-01` through `ses-05`. Protocol 2 corresponds to sessions `ses-a1` through `ses-a3` and represents an updated version of the original acquisition framework. The protocols share several acquisition types, but differ in selected sequences, acquisition parameters, and reconstruction procedures. Some acquisitions were added, optimized, or removed during the transition between protocols.

The descriptions below summarize acquisitions observed in representative sessions. They are intended as an overview of the available data rather than an exhaustive list of sequences collected from every participant or at every session. Acquisition availability should therefore be checked at the individual participant and session level.

### Acquisition protocol 1 (sessions 1, 2, 3, 4, 5)

Examples from Protocol 1 include the following acquisition types:

- **Structural MRI:** High-resolution MP2RAGE acquisitions, including the two inversion images (`inv-1` and `inv-2`), the uniform image (`UNIT1`), and quantitative T1 maps (`T1map`). Example sessions include acquisitions at 0.5 mm resolution.
- **Diffusion MRI (dMRI):** Multi-shell diffusion-weighted imaging, with acquisitions represented by `acq-b300`, `acq-b700`, and `acq-b2000`, as well as b=0 images. Example datasets include anterior-to-posterior (AP) and posterior-to-anterior (PA) phase-encoding directions and corresponding single-band reference images (`sbref`).
- **Functional MRI (fMRI):** Multi-echo BOLD acquisitions, with examples containing three echoes per task. Available tasks vary across sessions and include resting-state (`rest`) and task-based acquisitions. Examples include episodic encoding and retrieval, pattern separation, semantic and spatial tasks, as well as other task paradigms.
- **Multi-echo gradient-echo MRI (MEGRE):** Multi-echo magnitude and phase acquisitions. For example, in `ses-03`, MEGRE data are organized under the acquisition label `acq-me`, with six echoes acquired in separate magnitude and phase runs. A derived T2* map (`T2starmap`) is also present.
- **Magnetization transfer (MT):** MT-on and MT-off acquisitions, including magnitude and phase images associated with magnetization-transfer ratio (MTR) data. Example sessions also include T1-weighted magnitude and phase images under the `acq-MTR` label.
- **Angiography:** Angiographic acquisitions are represented in multiple orientations, including coronal (`acq-cor_angio`), sagittal (`acq-sag_angio`), and transverse (`acq-tra_angio`) acquisitions, as well as additional angiography images.
- **Field mapping and B1 calibration:** EPI acquisitions with AP and PA phase-encoding directions are available for functional MRI distortion correction. B1-related acquisitions include `TB1TFL` images associated with anatomical and functional calibration.

### Acquisition protocol 2 (sessions a1, a2, a3)

Protocol 2 retains several acquisition types from Protocol 1 while incorporating updates to acquisition labels, sequence configurations, and reconstruction outputs. Examples from the available sessions include:

- **Structural MRI:** High-resolution MP2RAGE acquisitions, including inversion images (`inv-1` and `inv-2`), uniform images (`UNIT1`), and quantitative T1 maps (`T1map`). Example acquisitions include 0.5 mm and 0.7 mm resolutions. FLAIR images are also present in some sessions.
- **Diffusion MRI (dMRI):** Diffusion-weighted acquisitions with multiple acquisition labels, including `acq-b0`, `acq-multib38`, and `acq-multib70` in the example dataset. AP and PA phase-encoding directions are represented in the available data.
- **Functional MRI (fMRI):** Multi-echo BOLD acquisitions, with examples containing three echoes per task. Tasks vary across participants and sessions and include resting-state (`rest`) and task-based acquisitions. Examples include sensory (`sens1`, `sens2`), semantic/phonological (`semphon1`, `semphon2`), social (`social`), and episodic encoding and retrieval (`epiencode`, `epiretrieve`) paradigms.
- **Multi-echo gradient-echo MRI (MEGRE):** MEGRE acquisitions are also present in Protocol 2. For example, in `ses-a2`, the acquisition is labeled `acq-aspire` and includes five echoes with magnitude and phase data. The available derived outputs include ASPIRE echo-combined and sensitivity-corrected images, as well as a T2* map (`T2starmap`). The example session also includes ROMEO-derived phase images, a mask, and an unwrapped phase reconstruction.
- **Magnetization transfer (MT):** MT-on and MT-off MTR acquisitions are present in Protocol 2. In the example `ses-a2` dataset, these are organized under the `acq-mtw` label and include magnitude and phase images. T1-weighted magnitude and phase images are also available under this acquisition label.
- **Field mapping and B1 calibration:** EPI acquisitions with AP and PA phase-encoding directions are represented. Additional functional field-mapping acquisitions, including `fmriQ1K` examples, and `TB1TFL` acquisitions are also present.

**Note:** The examples above illustrate the contents and naming conventions observed in representative sessions. Sequence availability, number of echoes, acquisition parameters, and derived reconstructions may differ across participants and sessions. Please consult the corresponding BIDS files and JSON sidecars for the exact acquisition details of each dataset.

## References and Links

### Dataset repositories

- **OSF:** https://doi.org/10.17605/OSF.IO/MHQ3F
- **bioRxiv:** https://doi.org/10.1101/2024.06.17.596303
- **Scientific Data:** https://doi.org/10.1038/s41597-025-04863-7

### Primary publication

Cabalo DG, Leppert IR, Thevakumaran R, DeKraker J, Hwang Y, Royer J, Kebets V, Tavakol S, Wang Y, Zhou Y, Benkarim O, Eichert N, Paquola C, Doyon J, Tardif CL, Rudko D, Smallwood J, Rodriguez-Cruces R, Bernhardt BC. (2025). *Multimodal precision MRI of the individual human brain at ultra-high fields.* Scientific Data, 12, 526.

https://doi.org/10.1038/s41597-025-04863-7

### Preprint

Cabalo DG, Leppert IR, Thevakumaran R, DeKraker J, Hwang Y, Royer J, Kebets V, Tavakol S, Wang Y, Zhou Y, Benkarim O, Eichert N, Paquola C, Doyon J, Tardif CL, Rudko D, Smallwood J, Rodriguez-Cruces R, Bernhardt BC. (2024). *Multimodal precision neuroimaging of the individual human brain at ultra-high fields.* bioRxiv.

https://doi.org/10.1101/2024.06.17.596303

## License and Data Access

The PNI database is distributed under a split-access and licensing model. See `LICENSE` for the applicable terms and conditions.

- **Publicly released subset (OSF; 10 healthy control participants):** CC0 1.0 Universal. Data are openly available through the Open Science Framework and may be used according to the terms of the CC0 license.

- **Extended internal database (additional healthy controls, epilepsy, autism, family members, pilot participants, and additional sessions):** Internal use only. Redistribution, external sharing, or transfer of these data is permitted only under applicable McGill University data-sharing agreements and institutional authorization.

Access to the internal database does not imply permission to redistribute or share the data outside the authorized agreements.