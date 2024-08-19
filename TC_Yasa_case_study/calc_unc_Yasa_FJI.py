#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  6 10:46:31 2022

@author: kampu

calculate the uncertainty for cyclone Yasa case
"""
import numpy as np
import scipy as sp
from pathos.multiprocessing import ProcessPool as Pool

from climada.hazard import Hazard
from climada.entity import LitPop
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.engine.unsequa import CalcImpact
from climada.engine.unsequa import InputVar

HAZ_FILE = '../haz/tc_haz_Yasa_{run_datetime}_updated.hdf5'

SAVE_UNC = './unc_output/yasa_unc_output_{run_datetime)_updated.hdf5'

run_datetime_list = np.arange('2020-12-13T12', '2020-12-17T12', np.timedelta64(12,'h'), dtype='datetime64[h]')

N_SAMPLE = 1000

# uncertanty parameters
## hazard sub-sampling with replacement
n_ev_haz = 1
## exposures
bounds_totval = [0.8, 1.2] #+- 25% noise on the total exposures value
## impf v_half IQR
impf_distr = {"v_half": sp.stats.uniform(38.8, 76.2-38.8)}

pool_unc = Pool()
pool_sen = Pool()


def do_unc_calc(exp_iv, impf_iv, haz_iv, N, pool=None):

    calc_imp = CalcImpact(exp_iv, impf_iv, haz_iv)
    
    output_imp = calc_imp.make_sample(N=N) 
    output_imp = calc_imp.uncertainty(output_imp, rp = [], pool=pool_unc)
    output_imp = calc_imp.sensitivity(output_imp, pool=pool_sen)
    
    # close pool
    pool_unc.close()
    pool_unc.join()
    pool_unc.terminate()
    
    pool_sen.close()
    pool_sen.join()
    pool_sen.terminate()
    
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
impf_iv = InputVar(impf_func, impf_distr)

##### exposure Fiji #####
exp_base = LitPop.from_population('FJI')

##### do the uncertainty calculation for each run_datetime #####
for run_datetime in run_datetime_list:
    # haz uncertainty
    haz_base = HAZ_FILE.format(run_datetime=run_datetime)
    haz_base.frequency = np.ones(51)/n_ev_haz
    
    haz_iv = InputVar.haz(haz_base, n_ev=n_ev_haz)
    
    # exposure uncertainty
    exp_base.assign_centroids(haz_base)
    
    exp_iv = InputVar.exp([exp_base], bounds_totval=bounds_totval)
    
    # calculate uncertainty
    unc_output = do_unc_calc(exp_iv, impf_iv, haz_iv, N=N_SAMPLE)
    
    # save uncertainty file to hdf5 for each run_datetime
    unc_output.to_hdf5(SAVE_UNC.format(run_datetime=run_datetime))