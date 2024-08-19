# Impact-Based Forecasting of Tropical Cyclone-Related Human Displacement to Support Anticipatory Action

These scripts reproduce the main results of the paper:

 **Impact-Based Forecasting of Tropical Cyclone-Related Human Displacement to Support Anticipatory Action.**
 
Pui Man Kam (1,2), Fabio Ciccone (1), Chahan, M. Kropf (1,3), Lukas Riedel (1,3), Christopher Fairless (1), and David N. Bresch (1,3)

Publication status: [under revision](https://www.researchsquare.com/article/rs-3682198/v1).

(1) Institute for Environmental Decisions, ETH Zurich, Switzerland

(2) Internal Displacement Monitoring Centre, Geneva, Switzerland

(3) Federal Office of Meteorology and Climatology MeteoSwiss, Switzerland

Contact: Pui Man Kam ([mannie.kam@usys.ethz.ch](mannie.kam@usys.ethz.ch))

## Content:
The project is seperated into two main folders. `TC_Yasa_case_study` contains all the scripts to reproduce the results from the case study of TC Yasa that caused displacement in Fiji. `Sensitivity_analysis_events_2017-2020` contains scripts for the sensitivity analysis for all TC displacement events recorded between 2017-2020.

#### TC_Yasa_case_study
`TC_yasa_FJI_2d_leadtime.py`: Python script for running the impact forecast for displacement at 2 days leadtime (2020-12-15 00UTC) prior the landfall of TC Yasa at Fiji. This script can be run independantly with the fulfilment of data requirements.

`tc_haz_Yasa.py`: Python script for calculating the 1-minute maximum sustained wind speed at 10 metres from surface for TC Yasa. The forecast initiate time is ranging from 2020-12-13 12UTC to 2020-12-17 00UTC with time interval of 12 hours. The output hdf5 files are the hazard sets, which are further used for the impact calculation.

`calc_unc_Yasa_FJI.py`: Python script for computing the uncertainty and sensitivity analysis for the TC Yasa case study. Make sure to run this after `tc_haz_Yasa.py`.

#### Sensitivity_analysis_events_2017-2020
`create_NETCDF_from_TIGGE_n2o_matched_ibtracs.py`: Python script for extracting archived TC track forecast incxml format from TIGGE project NetCDF files for later computation. Original data can be retrived from [NCAR Data Research Archive](https://rda.ucar.edu/datasets/d330003/).

`unc_sen_analysis_events_2017-2020.py`: Python script for computing the uncertainty and sensitivity analysis for all TC displacement events recorded between 2017-2020. The output hdf5 files are the CLIMADA UncOutput objects. Make sure to run this after `create_NETCDF_from_TIGGE_n2o_matched_ibtracs.py`, and `load_TIGGE_tracks.py` which contains the function to read TC tracks in NetCDF into CLIMADA is placed in the same working directory,

`unc_output_to_xlsx.py`: Python script for reading the hdf5 files output from `unc_sen_analysis_events_2017-2020.py` into xlsx files.

`load_TIGGE_tracks.py`: Python script that contains function to process TC tracks in NetCDT file (output from `create_NETCDF_from_TIGGE_n2o_matched_ibtracs.py`) into climada.hazard.TCTracks object. 

## Requirements
Requires:
- Python 3.9+ environment (best to use conda for CLIMADA repository)
- *CLIMADA* repository version 3.3+: [https://wcr.ethz.ch/research/climada.html https://github.com/CLIMADA-project/climada_python](https://wcr.ethz.ch/research/climada.html https://github.com/CLIMADA-project/climada_python)

## ETH cluster
Computationally demanding calculations were run on the [Euler cluster of ETH Zurich](https://scicomp.ethz.ch/wiki/Euler).

## Documentation:
Publication: submitted to **Nature Communications**

Documentation for CLIMADA is available on Read the Docs:
* [online (recommended)](https://climada-python.readthedocs.io/en/stable/)
* [PDF file](https://buildmedia.readthedocs.org/media/pdf/climada-python/stable/climada-python.pdf)

If script fails, revert CLIMADA version to release v3.3:
* from [GitHub](https://github.com/CLIMADA-project/climada_python/releases/tag/v3.1.2)

## History

Created on 25 June 2024

-----

[www.wcr.ethz.ch](www.wcr.ethz.ch)
