from timeit import default_timer as timer
start = timer()

import numpy as np
import pandas as pd
import scipy as sp

from climada_petals.hazard import TCForecast
from climada.hazard import TropCyclone, Centroids
from climada.entity import LitPop
from climada.engine import ImpactCalc
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.engine.unsequa import InputVar
from climada.engine.unsequa import CalcImpact

BUFR_FILE = '../data/TC_yasa_bufr_tracks/A_JSXX01ECEP150000_C_ECMP_20201215000000_tropical_cyclone_track_YASA_172p7degE_-15degS_bufr4.bin'

CENTR_FILE = '../data/earth_centroids_150asland_1800asoceans_distcoast_region_nopoles_new.hdf5'

v_thresh = 25.7

v_half_fji = 42.0

v_half_unc_list = [29.2, 32.2, 33.3, 37.9, 41.4, 41.5, 42.6, 45. , 45.4, 45.9, 46.9,
                   46.9, 47.3, 52.5, 53.3, 54.3, 56.6, 57.5, 59.3, 65.3, 68.9, 69.5,
                   76.8, 78.6, 82.3, 83.4, 85. , 93.6]

def set_displacement_emanuel_impfSet(v_half=32.93):
    """
    Set the step function set
    Argument:
        threshold (float): threshold for the step function. default 32.93m/s (64knots)
    """
    impf_tc = ImpfTropCyclone.from_emanuel_usa(v_thresh=v_thresh, \
                                                v_half=v_half, \
                                                scale=1.)
    impf_tc.haz_type = 'TC'
    impf_tc.id = 1
    impf_tc.name = 'TC impf v_half ' +str(v_half)  +' m/s)'
    impf_tc.intensity_unit = 'm/s'

    impf_set = ImpactFuncSet()
#    impf_set.tag.description = 'TC impf v_half ' +str(v_half)  +' m/s)'
    impf_set.append(impf_tc)
    
    return impf_set

exp_fji = LitPop.from_population('FJI')
extent = (-179.99, 180, min(exp_fji.gdf.latitude)-5, max(exp_fji.gdf.latitude)+5)

centr = Centroids.from_hdf5(CENTR_FILE)
centr_refine = centr.select(extent=extent)

##### load the TC forecast tracks and compute wind field #####
fcast = TCForecast()
fcast.fetch_ecmwf(path=BUFR_FILE)
fcast_ens = fcast.subset({'is_ensemble': True})
fcast_ens.equal_timestep(.5)

fcast_time = np.datetime_as_string(fcast_ens.data[0].run_datetime, unit='h')

tc_fcast = TropCyclone.from_tracks(fcast_ens, centroids=centr_refine)

##### compute impact considering only meteorological variability #####
impf_fji = set_displacement_emanuel_impfSet(v_half=v_half_fji)
exp_fji.assign_centroids(tc_fcast)

imp_met_var = ImpactCalc(exp_fji, impf_fji, tc_fcast).impact()
imp_met_var.write_excel('./time_run_imp_yasa_met_var.xlsx')

##### do the uncertainty and sensitivity analysis ##+###
N_SAMPLE = 1000

# uncertanty parameters
## hazard sub-sampling with replacement
n_ev_haz = 1
## exposures
bounds_totval = [0.8, 1.2] #+- 25% noise on the total exposures value

def do_unc_calc(exp_iv, impf_iv, haz_iv, N, pool=None):

    calc_imp = CalcImpact(exp_iv, impf_iv, haz_iv)
    
    output_imp = calc_imp.make_sample(N=N) 
    output_imp = calc_imp.uncertainty(output_imp, rp = [])
    output_imp = calc_imp.sensitivity(output_imp)
    
    return output_imp

# impf_iv
impf_set_list = []
for v_half in v_half_unc_list:
    impf_set = set_displacement_emanuel_impfSet(v_half=v_half)
    impf_set_list.append(impf_set)
    
impf_iv = InputVar.impfset(impf_set_list=impf_set_list)

# haz_iv
tc_fcast.frequency = np.ones(51)/n_ev_haz
haz_iv = InputVar.haz([tc_fcast], n_ev=n_ev_haz)

# exp_iv
exp_iv = InputVar.exp([exp_fji], bounds_totval=bounds_totval)

# calculate uncertainty
unc_output = do_unc_calc(exp_iv, impf_iv, haz_iv, N=N_SAMPLE)

# save uncertainty into excel
df_unc = pd.DataFrame(data={'run_datetime': np.repeat(fcast_time, len(unc_output.get_uncertainty())),
                            'forecasted_displacement': unc_output.get_uncertainty()['aai_agg'].values})
df_unc.to_excel('./Yasa_FJI_2d_leadtime_unc_dist.xlsx')

# save sensitivity into excel
df_sen = pd.DataFrame(data={'run_datetime': np.repeat(fcast_time, len(unc_output.get_sensitivity('S1'))),
                            'param': unc_output.get_sensitivity('S1')['param'].values,
                            'S1': unc_output.get_sensitivity('S1')['aai_agg'].values,
                            'S1_conf': unc_output.get_sensitivity('S1_conf')['aai_agg'].values})

df_sen.to_excel('./asa_FJI_2d_leadtime_sen_index.xlsx')

end = timer()
print(end - start)

