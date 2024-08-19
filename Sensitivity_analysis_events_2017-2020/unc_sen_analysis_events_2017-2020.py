#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 11:11:07 2023

@author: kampu
"""

# import necessary packages
import sys
import numpy as np
import pandas as pd
import glob
from datetime import datetime, timedelta

import climada.util.coordinates as u_coord
from climada.util.coordinates import latlon_bounds
from climada.entity import ImpfTropCyclone, ImpactFuncSet, LitPop
from climada.hazard.tc_tracks import TCTracks
from climada.hazard import TropCyclone, Centroids
from climada.engine.unsequa import CalcImpact
from climada.engine.unsequa import InputVar

from load_TIGGE_tracks import read_TIGGE_netcdf

DATA_DIR = '../data/'
SAVE_DIR = '../results_updated/'
# save uncertainty file to hdf5
SAVE_UNC_PATTERN = '../uncertainty_updated/uncertainty_files/{leadtime_str}/hdf5_files/sample_1000/' +\
                    'unc_output_{tc_name}_{country_iso3}_{ibtracs_id}_{init_datetime_str}_{leadtime_str}_leadtime.hdf5'

CENT_PATH = DATA_DIR +'global_centroids_m60_60lat_1800as_on_see_150as_on_land.h5'
centroids_global = Centroids.from_hdf5(CENT_PATH)

STORM_DATA = DATA_DIR +'2017_2020_IBTrACS.xlsx'
df_storm = pd.read_excel(STORM_DATA)

# Country list and v_half
iso3_to_basin = {'NA1': ['AIA', 'ATG', 'ARG', 'ABW', 'BHS', 'BRB', 'BLZ', 'BMU',
                 'BOL', 'CPV', 'CYM', 'CHL', 'COL', 'CRI', 'CUB', 'DMA',
                 'DOM', 'ECU', 'SLV', 'FLK', 'GUF', 'GRD', 'GLP', 'GTM',
                 'GUY', 'HTI', 'HND', 'JAM', 'MTQ', 'MEX', 'MSR', 'NIC',
                 'PAN', 'PRY', 'PER', 'PRI', 'SHN', 'KNA', 'LCA', 'VCT',
                 'SXM', 'SUR', 'TTO', 'TCA', 'URY', 'VEN', 'VGB', 'VIR'],
         'NA2': ['CAN', 'USA'],
         'NI': ['AFG', 'ARM', 'AZE', 'BHR', 'BGD', 'BTN', 'DJI', 'ERI',
                'ETH', 'GEO', 'IND', 'IRN', 'IRQ', 'ISR', 'JOR', 'KAZ',
                'KWT', 'KGZ', 'LBN', 'MDV', 'MNG', 'MMR', 'NPL', 'OMN',
                'PAK', 'QAT', 'SAU', 'SOM', 'LKA', 'SYR', 'TJK', 'TKM',
                'UGA', 'ARE', 'UZB', 'YEM'],
        'OC1': ['ASM', 'COK', 'FJI', 'PYF', 'GUM', 'KIR', 'MHL', 'FSM', 
                    'NRU', 'NCL', 'NIU', 'NFK', 'MNP', 'PLW', 'PNG', 'PCN', 
                    'WSM', 'SLB', 'TLS', 'TKL', 'TON', 'TUV', 'VUT', 'WLF'],
        'OC2': ['AUS', 'NZL'],
         'SI': ['COM', 'COD', 'SWZ', 'MDG', 'MWI', 'MLI', 'MUS', 'MOZ',
                'ZAF', 'TZA', 'ZWE'],
         'WP1': ['KHM', 'IDN', 'LAO', 'MYS', 'THA', 'VNM'],
         'WP2': ['PHL'],
         'WP3': ['CHN'],
         'WP4': ['HKG', 'JPN', 'KOR', 'MAC', 'TWN'],
         'ROW': ['ALB', 'DZA', 'AND', 'AGO', 'ATA', 'AUT', 'BLR', 'BEL',
                 'BEN', 'BES', 'BIH', 'BWA', 'BVT', 'BRA', 'IOT', 'BRN',
                 'BGR', 'BFA', 'BDI', 'CMR', 'CAF', 'TCD', 'CXR', 'CCK',
                 'COG', 'HRV', 'CUW', 'CYP', 'CZE', 'CIV', 'DNK', 'EGY',
                 'GNQ', 'EST', 'FRO', 'FIN', 'FRA', 'ATF', 'GAB', 'GMB',
                 'DEU', 'GHA', 'GIB', 'GRC', 'GRL', 'GGY', 'GIN', 'GNB',
                 'HMD', 'VAT', 'HUN', 'ISL', 'IRL', 'IMN', 'ITA', 'JEY',
                 'KEN', 'PRK', 'XKX', 'LVA', 'LSO', 'LBR', 'LBY', 'LIE',
                 'LTU', 'LUX', 'MLT', 'MRT', 'MYT', 'MDA', 'MCO', 'MNE',
                 'MAR', 'NAM', 'NLD', 'NER', 'NGA', 'MKD', 'NOR', 'PSE',
                 'POL', 'PRT', 'ROU', 'RUS', 'RWA', 'REU', 'BLM', 'MAF',
                 'SPM', 'SMR', 'STP', 'SEN', 'SRB', 'SYC', 'SLE', 'SGP',
                 'SVK', 'SVN', 'SGS', 'SSD', 'ESP', 'SDN', 'SJM', 'SWE',
                 'CHE', 'TGO', 'TUN', 'TUR', 'UKR', 'GBR', 'UMI', 'ESH',
                 'ZMB', 'ALA']}

## impf v_half 80% quantiles
impf_80quantiles = {'NA1': [ 30.4,  33.5,  34.7,  35.7,  36.2,  40.8,  40.8,  41. ,  43. ,
                            43. ,  44.6,  47.1,  48.1,  48.6,  48.7,  48.7,  48.8,  51. ,
                            57.7,  58.5,  58.7,  64.8,  65.9,  66.5,  68.4,  70.3,  70.4,
                            71.1,  72.2,  74.6,  77.1,  83.2,  85.7,  87.4, 103.3, 118.4,
                            149.6],
                    'NA2': [ 42.4,  45.4,  48.1,  50.8,  59.1,  84.2, 103. , 134.2, 144.2],
                    'NI': [31.1, 31.2, 33.5, 33.5, 35. , 35.3, 36.4, 37.1, 37.8, 38.4, 39.3,
                           41.4, 43.7, 45.2, 46.3, 46.5, 48.2, 51.2, 54.4, 55.7, 58.1, 65.8,
                           75.8, 76.7],
                    'OC1': [32.2, 33.3, 37.9, 41.4, 41.5, 42.6, 45. , 45.4, 45.9, 46.9, 46.9,
                            47.3, 52.5, 53.3, 54.3, 56.6, 57.5, 59.3, 65.3, 68.9, 69.5, 76.8,
                            78.6, 82.3, 83.4, 85. ],
                    'OC2': [ 29.9,  40.2,  42.8,  47. ,  47. ,  54.3,  54.6,  62.9,  65.6,
                            68.9,  89.9, 108.9],
                    'SI': [33.8, 39.3, 40.4, 40.7, 46.2, 48.7, 49.3, 56.9, 58. , 58.2, 63.7,
                           68. ],
                    'WP1': [31.5, 38.6, 42.1, 43.6, 43.8, 51.6, 51.8, 53. , 54. , 54.9, 60.9,
                            69.8, 72.2, 78.1],
                    'WP2': [ 37.4,  38.8,  40.7,  42.5,  43.8,  43.8,  45.4,  49.2,  49.3,
                            49.5,  49.8,  51.6,  52. ,  52.3,  56. ,  56.7,  58.2,  60.6,
                            63.9,  65.1,  66.8,  73.6,  76.8,  83.9,  92.7,  97.5, 103.5],
                    'WP3': [25.8, 25.8, 25.8, 25.8, 25.8, 25.8, 28.1, 29.4, 30. , 31.9, 33.7,
                            33.8, 34. , 34.3, 37.5, 38.2, 40.9, 41.6, 42.7, 43.4, 44.3, 44.6,
                            45.3, 47.2, 47.3, 51.9, 56.1, 56.1, 57. , 59.4, 66.3, 67.2, 71.7,
                            73.3, 77. , 88.1],
                    'WP4': [ 37.4,  38.6,  40.4,  41.5,  41.6,  41.6,  43.2,  44.8,  49.2,
                            50.1,  52.5,  58.3,  62.7,  64.7,  67.1,  72.2,  85. ,  86.2,
                            87.9,  87.9,  97.2, 103.5, 105.6, 113.8, 118.1, 125.4, 127. ]}

leadtime_str2float = {'0_5d': 0.5, '1d': 1, '1_5d': 1.5, '2d': 2, '2_5d': 2.5, '3d': 3}

###### functions ######

def impf_func(v_half=45.6):
    imp_fun = ImpfTropCyclone.from_emanuel_usa(intensity=np.arange(0, 150, 1), v_half=v_half)
    imp_fun.haz_type = 'TC'
    imp_fun.intensity_unit = 'm/s'
    imp_fun.check()
    
    impf_set = ImpactFuncSet()
    impf_set.append(imp_fun)
    return impf_set

# Functions
def extent_buffer(extent, buffer=5):
    extent = latlon_bounds(np.array([extent[2], extent[3]]), np.array([extent[0], extent[1]]), buffer=buffer)
    
    return (extent[0], extent[2], extent[1], extent[3])

def get_impf_distr(country):
    """
    Get impf_distr according to selected country (country_iso3)
    Argument:
        country (string): selected country (variable is "country_iso3")
    """
    # Get basin in which country_iso3 lies
    basin = [key
            for key, list_of_values in iso3_to_basin.items()
            if country in list_of_values]
    
    # Get impf_distr corresponding to basin
    impf_distribution = impf_set_region[basin[0]]
    
    return impf_distribution

def do_unc_calc(exp_iv, impf_iv, haz_iv, N):

    calc_imp = CalcImpact(exp_iv, impf_iv, haz_iv)
    
    output_imp = calc_imp.make_sample(N=N)
    
    output_imp = calc_imp.uncertainty(output_imp, rp = [], processes=8)
    
    output_imp = calc_imp.sensitivity(output_imp)
 
    return output_imp

##### Uncertainty parameters #####
N_SAMPLE = 1024

# uncertanty parameters
## hazard sub-sampling with replacement
n_ev_haz = 1

## exposures
bounds_totval = [0.8, 1.2] #+- 20% noise on the total exposures value

## impact funcs
impf_set_region = {}
for region in impf_80quantiles:
    impf_set_list = []
    for v_half in impf_80quantiles[region]:
        impf_set = impf_func(v_half=v_half)
        impf_set_list.append(impf_set)
    impf_set_region[region] = impf_set_list

########## read TIGGE files ##########
def main(storm_year=2017, leadtime_str='0_5d'):

    # Read all TIGGE tracks from 2017-2020 into a TCTracks()-object
    tigge_tc_tracks = TCTracks()
    
    for file in glob.glob(DATA_DIR + 'nc_ecmf_{storm_year}_*.nc'.format(storm_year=storm_year)):
        print(file)                                              # to check in console if script is still running
        tigge_tc_tracks.data.extend(read_TIGGE_netcdf(file, matched_ibtracs_only=True).data)
    
    ##### run the uncertainty analysis #####
    for idx_entry in range(len(df_storm)):
       
        # extract the landfall time
        landfall_time = datetime.strptime(df_storm['landfall_time'][idx_entry], '%Y-%m-%dT%H:%M:%S')
        if landfall_time.year != int(storm_year):
            continue
        
        
        init_datetime = landfall_time - timedelta(days=leadtime_str2float[leadtime_str])
        
        # rounding time to 00 or 12 UTC
        if init_datetime.hour == 3 or init_datetime.hour == 15:
            init_datetime = init_datetime - timedelta(hours=3)
        elif init_datetime.hour == 6 or init_datetime.hour == 18:
            init_datetime = init_datetime - timedelta(hours=6)
        elif init_datetime.hour == 9 or init_datetime.hour == 21:
            init_datetime = init_datetime + timedelta(hours=3)
        
        # extract storm from TIGGE
        ibtracs_id = df_storm['ibtracs_id'][idx_entry]
        
        # select all the ens. tracks from 1 storm out of all TIGGE tracks from 2017-2020
        try:
            sel_storm = tigge_tc_tracks.subset({"matched_ibtracs": ibtracs_id,
                                                "is_ensemble": True,
                                                "run_datetime": init_datetime})
            sel_storm.equal_timestep(time_step_h=1)          # interpolate the track to 1 hour interval
            
            extent = sel_storm.get_extent()
            extent_buffered = extent_buffer(extent, buffer=5)
        except ValueError:
            print(ibtracs_id, 'with init datetime', init_datetime.strftime('%Y-%m-%dT%H:%M:%S'), 'does not exist')
            continue
        
        ##### compute TC windfield #####
        # Compute the predicted windfield of the track at a resolution of 150 ArcSec (approx. 5km) on land and 1800 ArcSec (approx. 50km) on sea
        centroids_sel = centroids_global.select(extent = extent_buffered)
        centroids_sel.lon = u_coord.lon_normalize(centroids_sel.lon)         # Lon-coordinates need to be normalized to a common 360 degree range
                    
        tc_fcast = TropCyclone.from_tracks(sel_storm, centroids_sel)
        tc_fcast.frequency = np.ones(len(tc_fcast.event_id))
        
        ##### haz_iv #####
        haz_iv = InputVar.haz([tc_fcast], n_ev=n_ev_haz)
        
        ##### exp_iv #####
        exp_base = LitPop.from_population(countries=df_storm['ISO3'][idx_entry])
        exp_base.assign_centroids(tc_fcast)
        
        exp_iv = InputVar.exp([exp_base], bounds_totval=bounds_totval)
        
        ##### impf_iv ######
        impf_iv = InputVar.impfset(impf_set_list=get_impf_distr(df_storm['ISO3'][idx_entry]))
        
        ##### calculate uncertainty and save outputs ######
        unc_output = do_unc_calc(exp_iv, impf_iv, haz_iv, N=N_SAMPLE)
        
        save_unc = SAVE_UNC_PATTERN.format(leadtime_str=leadtime_str, tc_name=df_storm['TC_name'][idx_entry],
                                           country_iso3=df_storm['ISO3'][idx_entry], ibtracs_id=ibtracs_id,
                                           init_datetime_str=init_datetime.strftime('%Y-%m-%dT%H:%M:%S'))
        print(save_unc)
        unc_output.to_hdf5(save_unc)
        
if __name__ == "__main__":
     main(*sys.argv[1:])