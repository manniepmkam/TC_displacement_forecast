#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 10:29:45 2019

@author: alessio
"""

''' This code reads xml TIGGE file and create a netCDF4 file '''

import netCDF4 as nc
import xarray as xr
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from datetime import datetime
import os

provider='ecmf'

#basin='Northeast Pacific'

YEAR = np.arange(2016,2021)
#YEAR = np.arange(2019, 2021)

BASINS = ['Northeast Pacific', 'Northwest Pacific', 'North Atlantic', 'North Indian', 'Southwest Pacific', ]
#BASINS =  ['Northeast Pacific']

def run_TIGGE2NetCDF(year, basin):
    vars_dict={'member':('fcMember', int, ('nstorms',)),
               'cycloneName':('cycloneName', str, ('nstorms',)), 
               'localID':('localID', str, ('nstorms',)), 
               'basin':('basin', str, ('nstorms',)),
               'ID':('ID', str, ('nstorms',)),        
               'fix':('hour', float, ('nstorms','date_time',)),
               'validTime':('time', str, ('nstorms','date_time',)),
               'latitude':('lat', float, ('nstorms','date_time',)), 
               'longitude':('lon', float, ('nstorms','date_time',)), 
               'pressure':('minPressure', float, ('nstorms','date_time',)),
               'speed':('maxWind', float, ('nstorms','date_time',))}
    
    convert={'deg N': +1, 'deg S': -1, 'deg E': +1, 'deg W': -1}
    ## in kwbc, we have only easting, up to 360 degrees
    ## TODO: check for lat values (if all e.g. in northing)
    #convert_lon = lambda x: x-360 if x > 180 else x
    
    dict_events={}
    event_num=0
    
    file_list=os.listdir('../{year}/cxml'.format(year=year))
    
    #rand_pos=np.random.randint(0, len(file_list), 500)
    #file_list=[file_list[i] for i in rand_pos]
    
    file_with_basin = []
    pos_file_with_basin=[]
    thrown_files = []
    
    for file in file_list:
        try:
            obj = ET.parse('../{}/cxml/{}'.format(year, file))
        except ET.ParseError:
            thrown_files.append(file)
            continue
        
        root=obj.getroot()
        
        for child in root:
    #        _is_there_name = False
            if child.tag == 'data':
                
                if 'ensembleForecast' in child.attrib.values():
                    ensemble_num = int(child.attrib['member'])+1
                    
                elif 'forecast' in child.attrib.values():
                    ensemble_num = 0
                    
                elif 'analysis' in child.attrib.values():
                    continue
                else:
                    raise('No single forecast nor ensembles found in {}'.format(file))
                
                dist_counter=0
                for disturbance in child:
                    if disturbance.find('./basin').text != basin:
                        continue
    
                    if file not in file_with_basin:
                        file_with_basin.append(file)
                        pos_file = file_list.index(file)
                        pos_file_with_basin.append(pos_file)
    
                    # fc member: member.disturbance (should you have 
                    # more than 1 cyclone in each member)
                    dict_events.update({event_num:{
                            '{}_{}'.format(provider, vars_dict[key][0]):[
                                    ] for key in vars_dict.keys()}})
    
                    dict_events[event_num]['{}_fcMember'.format(provider)
                                           ].append(ensemble_num)
    
                    dict_events[event_num]['{}_ID'.format(provider)
                    ].append('{}.{}'.format(disturbance.attrib['ID'], pos_file))
    
                    dist_counter+=1
                    
                    wind_flag = 0
                    count_skip = 0
                    for forecast in disturbance.iter():
                        tag = forecast.tag
    
                        if ((wind_flag) and (count_skip<2)):
                           count_skip += 1
                           continue
    
                        elif count_skip == 2:
                            wind_flag = 0
                            count_skip = 0
    
                    # Sometimes more than 1 track per ensemble, only keep the first
    #                if tag == 'cycloneName':
    #                    if _is_there_name:
    #                        break
    #                    else:
    #                        _is_there_name = True
                            
                        if tag in vars_dict.keys():
                            name, _type, _ = vars_dict[tag]
                            new_name='{}_{}'.format(provider, name)
                        
                            if tag == 'fix':
                                value = _type(forecast.attrib[name])
                            
                            elif tag in ['latitude', 'longitude']:
                                ## in kwbc
                                if ((forecast.attrib['units'] == 'deg S') or (forecast.attrib['units'] == 'deg W')):
                                    value = -_type(forecast.text)
                                else:
                                    value = _type(forecast.text)
                                ## in babj
    #                            sign = convert[forecast.attrib['units']]
    #                            value = _type(forecast.text)*sign
                            elif tag == 'speed':
                                value = _type(forecast.text)
                                wind_flag = 1
                                
                            else:
                                value = _type(forecast.text)
                            dict_events[event_num][new_name].append(value)
                      
                    event_num+=1
    
    #np.savetxt('{}_tracksfiles_kwbc.txt'.format(basin), file_with_basin, fmt='%s')
    
    print('Saved {} files list and thrown {} files out of the initial set of {} files'.format(
            len(file_with_basin), len(thrown_files), len(file_list)))
    
    ## Drop:
    ## - files with no data; 
    ## - data with no id nor name;
    ## and reorder dict keys.
    new_track_pos=0
    dict_events_={}
    dist_ID_list=[]
    for track in dict_events.keys():
        # if you at least have a track (two numbers) and there are 
        # either localids or cyclonenames
        if (len(dict_events[track]['{}_lon'.format(provider)]) > 1) and (
            len(dict_events[track]['{}_localID'.format(provider)]) != 0 or 
            len(dict_events[track]['{}_cycloneName'.format(provider)]) != 0
            ): # and (dict_events[track]['{}_disturbanceID'.format(provider)] not in dist_ID_list):
            
    #        dist_ID_list.append(dict_events[track]['{}_disturbanceID'.format(provider)])
            
    #        rec_t = dict_events[track]['{}_time'.format(provider)][0]
    #        dict_events[track]['{}_disturbance_ID'.format(provider)].append(rec_t)
            if len(dict_events[track]['{}_localID'.format(provider)]) == 0: 
                dict_events[track]['{}_localID'.format(provider)].append(
                        dict_events[track]['{}_cycloneName'.format(provider)][0])
            
            elif len(dict_events[track]['{}_cycloneName'.format(provider)]) == 0: 
                dict_events[track]['{}_cycloneName'.format(provider)].append(
                        dict_events[track]['{}_localID'.format(provider)][0])        
            
            dict_events_.update({new_track_pos: dict_events[track]})
          
            new_track_pos+=1
            
    ## USE xarray:
    nstorms=len(dict_events_.keys())
    ###also get them as number of members from heading
    date_time=np.max([len(dict_events_[i][
            '{}_time'.format(provider)]) for i in dict_events_.keys()])
    
    dims_dict={'nstorms': nstorms, 'date_time': date_time}
    
    NANS={float: np.nan, str: ''} # only validtime has string type when we call 
                                  # this (cannot apply datetime[ns] type when reading string)
    #new_type={float: float, str: 'datetime64[ns]'}
    
    new_type={float: float, str: str} # this became redundant
    
    out_dict={}
    
    for var in vars_dict.keys():
        name, _type, dim = vars_dict[var]
        new_name='{}_{}'.format(provider, name)
        # either mono or bidimensional array and first dim always nsotrms: 
        # so not a general solution at all
        if len(dim) == 1:
            values=np.array([dict_events_[i][new_name][0] for i in range(nstorms)])      
            out_dict.update({new_name:(dim, values)})
        else:
    #        dummy=np.zeros(shape=(dims_dict[dim[0]], dims_dict[dim[1]]), dtype=_type)
            dummy=[]
            for storm in range(nstorms):
                values=np.array(dict_events_[storm][new_name])
                
                if len(values) < date_time:
                    len_to_fill=date_time-len(values)
                    values = np.append(values, np.repeat(NANS[_type], len_to_fill))
                    
                dummy.append(values)
    
            out_dict.update({new_name:(dim, np.array(dummy, dtype=new_type[_type]))})
    
    coords={'time': out_dict['{}_time'.format(provider)],
            'lon': out_dict['{}_lon'.format(provider)],
            'lat': out_dict['{}_lat'.format(provider)]} # when with more providers, basically 
                                                        # APPEND from all providers
                                                        
    ####### giving matched IBTrACS ID
    df_ibtracs_current_year = pd.read_excel('../data/ibtracs_storm/TC_ibtracks_basin_sid_{year}.xlsx'.format(year=year))
    df_ibtracs_last_year = pd.read_excel('../data/ibtracs_storm/TC_ibtracks_basin_sid_{year}.xlsx'.format(year=year-1))
    
    ibtracs_arr = ["" for i in range(nstorms)]
    
    for i_track in range(nstorms):
        tc_name = out_dict['ecmf_cycloneName'][1][i_track].upper()
        time_str = out_dict['ecmf_time'][1][i_track][0]
        run_datetime = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
        
        try:
            ibtracs_id = df_ibtracs_current_year['ibtracs_id'][df_ibtracs_current_year['TC_Name']==tc_name].values[0]
        except IndexError:
            if year==2016:
                ibtracs_id = 'NOT_AVAILABLE'
            elif run_datetime >= datetime(year,1,1) and run_datetime < datetime(year,1,31): # look for previous year
                try:
                    ibtracs_id = df_ibtracs_last_year['ibtracs_id'][df_ibtracs_last_year['TC_Name']==tc_name].values[0]
                except IndexError:
                    ibtracs_id = 'NOT_AVAILABLE'
            else:
                ibtracs_id = 'NOT_AVAILABLE'
                    
        ibtracs_arr[i_track] = ibtracs_id
    
    out_dict.update({'matched_ibtracs': (('nstorms',), np.array(ibtracs_arr, dtype=str))})
    
        
        
    
    file = xr.Dataset(out_dict, coords=coords)
    
    file.to_netcdf('../{year}/nc_{provider}_{year}_{basin}.nc'.format(year=year, provider=provider, basin=basin.replace(' ','')))
    

for year in YEAR:
    for basin in BASINS:
        run_TIGGE2NetCDF(year, basin)


# ###### load tracks to climada.hazard.TCTracks
# import load_TIGGE_tracks
# from climada.hazard import TCTracks


# tracks = []
# nstorms = file.dims['nstorms']

# for i in range(nstorms):
#     tracks.append(load_TIGGE_tracks.read_one_TIGGE(file, i, 'ecmf'))
    
# tr = TCTracks()
# tr.data = tracks
