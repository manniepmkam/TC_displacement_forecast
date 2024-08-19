#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 15:23:24 2022

@author: kampu
"""

import numpy as np
import matplotlib.pyplot as plt

from climada_petals.hazard import TCForecast
from climada.hazard import TropCyclone, Centroids
from climada.entity import LitPop
from climada.util.files_handler import get_file_names

BUFR_FOLDER = '../data/TC_yasa_bufr_tracks/'

CENTR_FILE = '../data/earth_centroids_150asland_1800asoceans_distcoast_region_nopoles.hdf5'

file_list = get_file_names(BUFR_FOLDER)

exp_fji = LitPop.from_countries('FJI')
extent = (-179.99, 180, min(exp_fji.gdf.latitude)-5, max(exp_fji.gdf.latitude)+5)

centr = Centroids.from_hdf5(CENTR_FILE)
centr_refine = centr.select(extent=extent)

for file in file_list:
    
    
    fcast = TCForecast()
    fcast.fetch_ecmwf(path=file)
    fcast_ens = fcast.subset({'is_ensemble': True})
    fcast_ens.equal_timestep(.5)

    fcast_time = np.datetime_as_string(fcast_ens.data[0].run_datetime, unit='h')
    ax_tr = fcast_ens.plot().get_figure().savefig('haz/tr_Yasa_'+fcast_time+'.png')

    tc_fcast = TropCyclone()
    tc_fcast.set_from_tracks(fcast_ens, centroids=centr_refine)
    
    tc_fcast.write_hdf5('haz/tc_haz_Yasa_'+fcast_time+'_updated.hdf5')