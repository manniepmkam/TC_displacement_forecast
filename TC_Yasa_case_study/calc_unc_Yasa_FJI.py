#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  6 10:46:31 2022

@author: kampu

calculate the uncertainty for cyclone Yasa case
"""
import numpy as np
import pandas as pd
# import scipy as sp

from climada.hazard import Hazard
from climada.entity import LitPop, Exposures
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.util.coordinates import get_land_geometry
from climada.engine.unsequa import CalcImpact
from climada.engine.unsequa import InputVar

HAZ_FILE = '../haz/tc_haz_Yasa_{run_datetime}_updated.hdf5'

SAVE_UNC = './unc_output/yasa_unc_output_{run_datetime}_updated_80pct_impf.hdf5'

EXP_FILE = '/cluster/work/climate/kampu/climada/data/gpw_v4_population_count_rev11_2020_30_sec.tif'

SAVE_UNC = './plots/uncertainty_distribution_yasa_updated_80pct_impf.xlsx'

SAVE_SEN = './plots/first_order_sensitivity_yasa_updated_80pct_impf.xlsx'

run_datetime_list = np.arange('2020-12-13T12', '2020-12-17T12', np.timedelta64(12,'h'), dtype='datetime64[h]')

df_unc = pd.DataFrame(columns=['run_datetime', 'forecasted_displacement'])

df_sen = pd.DataFrame(columns=['run_datetime', 'param', 'S1', 'S1_conf'])



N_SAMPLE = 1024

# uncertanty parameters
## hazard sub-sampling with replacement
n_ev_haz = 1
## exposures
bounds_totval = [0.8, 1.2] #+- 25% noise on the total exposures value

v_half_unc_list = [32.2, 33.3, 37.9, 41.4, 41.5, 42.6, 45. , 45.4, 45.9, 46.9, 46.9,
                   47.3, 52.5, 53.3, 54.3, 56.6, 57.5, 59.3, 65.3, 68.9, 69.5, 76.8,
                   78.6, 82.3, 83.4, 85. ]

def do_unc_calc(exp_iv, impf_iv, haz_iv, N, pool=None):

    calc_imp = CalcImpact(exp_iv, impf_iv, haz_iv)
    
    output_imp = calc_imp.make_sample(N=N) 
    output_imp = calc_imp.uncertainty(output_imp, rp = [], processes=4)
    output_imp = calc_imp.sensitivity(output_imp)
    
    return output_imp

def impf_func(v_half=45.6):
    imp_fun = ImpfTropCyclone.from_emanuel_usa(intensity=np.arange(0, 150, 1), v_half=v_half)
    imp_fun.haz_type = 'TC'
    imp_fun.intensity_unit = 'm/s'
    imp_fun.check()
    
    impf_set = ImpactFuncSet()
    impf_set.append(imp_fun)
    return impf_set


##### impf_iv ########
impf_set_list = []
for v_half in v_half_unc_list:
    impf_set = impf_func(v_half=v_half)
    impf_set_list.append(impf_set)
    
impf_iv = InputVar.impfset(impf_set_list=impf_set_list)

##### exposure Fiji #####
exp_base = LitPop.from_population('FJI')
# country_geom = get_land_geometry(country_names='FJI')
# exp_base = Exposures.from_raster(EXP_FILE, geometry=country_geom)
# exp_base.gdf['impf_TC'] = np.ones(len(exp_base.gdf))

##### do the uncertainty calculation for each run_datetime #####
for run_datetime in run_datetime_list:
    print(run_datetime, 'begin')
    # haz uncertainty
    haz_base = Hazard.from_hdf5(HAZ_FILE.format(run_datetime=run_datetime))
    haz_base.frequency = np.ones(51)/n_ev_haz
    
    haz_iv = InputVar.haz([haz_base], n_ev=n_ev_haz)
    
    # exposure uncertainty
    exp_base.assign_centroids(haz_base)
    
    exp_iv = InputVar.exp([exp_base], bounds_totval=bounds_totval)
    
    # calculate uncertainty
    unc_output = do_unc_calc(exp_iv, impf_iv, haz_iv, N=N_SAMPLE)
    
    # save uncertainty file to hdf5 for each run_datetime
#    unc_output.to_hdf5(SAVE_UNC.format(run_datetime=run_datetime))

    print(run_datetime, 'completed')
    
    # get the uncertainty analysis
    df_unc_temp = pd.DataFrame(data={'run_datetime': np.repeat(run_datetime, len(unc_output.get_uncertainty())),
                                     'forecasted_displacement': unc_output.get_uncertainty()['aai_agg'].values})
    df_unc = df_unc.append(df_unc_temp, ignore_index=True)
    
    # get the sensitivity analysis
    df_sen_temp = pd.DataFrame(data={'run_datetime': np.repeat(run_datetime, len(unc_output.get_sensitivity('S1'))),
                                     'param': unc_output.get_sensitivity('S1')['param'].values,
                                     'S1': unc_output.get_sensitivity('S1')['aai_agg'].values,
                                     'S1_conf': unc_output.get_sensitivity('S1_conf')['aai_agg'].values})
    df_sen = df_sen.append(df_sen_temp, ignore_index=True)
    
# save both files
df_unc.to_excel(SAVE_UNC)
df_sen.to_excel(SAVE_SEN)
