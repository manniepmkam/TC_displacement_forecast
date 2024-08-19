#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 11:11:48 2023

@author: kampu
"""
import sys
import glob
import pandas as pd

from climada.engine.unsequa import UncOutput

UNC_OUTPUT_DIR = '../uncertainty_updated/uncertainty_files/{leadtime_str}/hdf5_files/sample_1000/'

SAVE_SEN = '../uncertainty_updated/uncertainty_files/first_order_sensitivity_{leadtime_str}_leadtime_e_ibtracsID.xlsx'

def main(leadtime_str='0_5d', temp=None):
    
    df_sen = pd.DataFrame(columns=['ibtracs_id', 'param', 'S1', 'S1_conf'])
    
    for file in glob.glob(UNC_OUTPUT_DIR.format(leadtime_str=leadtime_str) +'*.hdf5'):
        
        # Find the index of the 8th and 9th '_'
        eighth_underscore_index = 0
        ninth_underscore_index = 0
        underscore_count = 0
        
        for i, char in enumerate(file):
            if char == '_':
                underscore_count += 1
                if underscore_count == 8:
                    eighth_underscore_index = i
                elif underscore_count == 9:
                    ninth_underscore_index = i
                    break
        
        # Extract the substring between the 8th and 9th '_'
        event_id = file[eighth_underscore_index + 1:ninth_underscore_index]
        
        
        unc_output = UncOutput.from_hdf5(file)
        
        df_sen_temp = pd.DataFrame(data={'ibtracs_id': event_id,
                                         'param': unc_output.get_sensitivity('S1')['param'].values,
                                         'S1': unc_output.get_sensitivity('S1')['aai_agg'].values,
                                         'S1_conf': unc_output.get_sensitivity('S1_conf')['aai_agg'].values})
        df_sen = df_sen.append(df_sen_temp, ignore_index=True)
        
    df_sen.to_excel(SAVE_SEN.format(leadtime_str=leadtime_str))

if __name__ == "__main__":
     main(*sys.argv[1:])