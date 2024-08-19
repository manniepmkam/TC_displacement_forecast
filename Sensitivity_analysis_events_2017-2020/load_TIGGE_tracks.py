#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 13:15:18 2019

@author: alessio
"""

import xarray as xr
from climada.hazard import set_category
from climada.hazard.tc_tracks import estimate_rmw, TCTracks
import numpy as np
import datetime as dt
import pandas as pd

def read_one_TIGGE(nc_data, i_track, provider):
    """Load from netcdf4, adjust names (basically dropping provider prefix and
       putting this info in the attributes) and create new xr.data_set. If 
       names were correct, just do load as xr.data_set and slice per storm 
       doing ds.isel(nstorsm=ind).
       
       Parameters:
       nc_data (Dataset): netcdf data set
       i_track (int): track position in netcdf data
       provider (str): data provider. e.g. babj
    """
    
    fcMember = int(nc_data.variables[provider + '_fcMember'][i_track].data)
    cycloneName = str(nc_data.variables[provider + '_cycloneName'][i_track].data)
    basin_init = str(nc_data.variables[provider + '_basin'][i_track].data)
    localID = str(nc_data.variables[provider + '_localID'][i_track].data)
    ID = str(nc_data.variables[provider + '_ID'][i_track].data)
    bool_ens = False if fcMember == 0 else True
    ibtracs_id = str(nc_data.variables['matched_ibtracs'][i_track].data)
    
    # compute this inside the netcdf file so you can use it in the current 
    # CLIMADA filtering function
    sid = '{}_{}'.format(localID.upper(), ID[:10])
    
    t_string = [str(t.data) for t in nc_data.variables['time'][i_track,:] if t]
    val_len = len(t_string)
    datetimes = list()
    for t in t_string:
#        datetimes.append(num2date(date_time, 'days since {}'.format(t_start), 
#                                  calendar='standard'))
        datetimes.append(dt.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ'))
    
    time_step=[]
    for i_time, time in enumerate(datetimes[1:], 1):
        time_step.append((time - datetimes[i_time-1]).total_seconds()/3600)
    time_step_=[time_step[-1]]
    time_step_.extend(time_step)
    
    # some tracks of non-monotonic time series, usually due to few messed up 
    # records at the beginning. If instead more than one error, ignore track.
    start_val=0
    split_values=np.where(np.diff(datetimes).astype('timedelta64') \
                          <= np.array(0).astype('timedelta64'))[0]
    if len(split_values) > 1:
        return None
    elif len(split_values) == 1:
        start_val=split_values[0]
    
    # some others (see e.g. sid='2_1219_2012-10-03T12:00:00Z' or '0_1219_2012-10-03T12:00:00Z')
    # have two different values recorded for the same time step, which lead deltaT=0
    # start_val=0
    # if datetimes[0]==datetimes[1]:
    #     start_val=1 
    
    ## TODO: when you do this, it can happen that if there are two values
    ## with the same then you end up with only one: fix it
    datetimes = datetimes[start_val:val_len]
    lon = nc_data.variables[provider + '_lon'][i_track, :][start_val:val_len]
    lat = nc_data.variables[provider + '_lat'][i_track, :][start_val:val_len]
    cen_pres = nc_data.variables[provider + '_minPressure'][i_track, :][start_val:val_len]
    
    wind = nc_data.variables[provider + '_maxWind'][i_track, :][start_val:val_len]
    if not all(wind.data): # if wind is empty
        wind = np.ones(wind.size)*-999.9

    tr_df = pd.DataFrame({'time': datetimes, 'lat': lat, 'lon':lon, 
            'max_sustained_wind': wind, 'central_pressure': cen_pres, 
            'environmental_pressure': np.ones(lat.size)*1015., 
            'radius_max_wind': estimate_rmw(np.repeat(np.nan, len(lon)), cen_pres),
            'time_step': time_step_[start_val:val_len],
            'basin': np.repeat(basin_init, len(datetimes))})
    # TODO: assess environemtnal pressure based on lat and lon
    
    # construct xarray
    tr_ds = xr.Dataset.from_dataframe(tr_df.set_index('time'))
    tr_ds = tr_ds.set_coords('lat')
    tr_ds = tr_ds.set_coords('lon')
    tr_ds.attrs = {'max_sustained_wind_unit': 'm/s', 
                   'central_pressure_unit': 'mb', 
                   'name': cycloneName.upper(), 
                   'sid':sid,
                   'orig_event_flag': True,
                   'data_provider': provider, 
                   'id_no':ID, 
                   'matched_ibtracs': ibtracs_id,
                   'ensemble_number': fcMember,
                   'is_ensemble': bool_ens, 
                   'run_datetime': datetimes[0],
                   'category': set_category(wind, 'm/s')}
    return tr_ds

def read_TIGGE_netcdf(filepath, matched_ibtracs_only=True):
    """
    Load all the tracks from the NetCDF file into a climada.hazard.TCTracks object.
    
    Parameters:
        filepath (str): The file path of the netCDF file
        matched_ibtracs_only (bool): Whether to read tracks with matched IBTrACS only
                                     (Default: True)
    Return:
        tc_tracks (climada.hazard.TCTracks): 
    
    """
    
    nc_open = xr.open_dataset(filepath)

    tracks = []
    nstorms = nc_open.dims['nstorms']
    
    for i in range(nstorms):
        
        tr_temp = read_one_TIGGE(nc_open, i, 'ecmf')
        if matched_ibtracs_only and tr_temp.matched_ibtracs == 'NOT_AVAILABLE':
            continue
        
        tracks.append(read_one_TIGGE(nc_open, i, 'ecmf'))
    
    tc_tracks = TCTracks()
    tc_tracks.data = tracks
    
    return tc_tracks