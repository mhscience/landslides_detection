# -*- coding: utf-8 -*-
"""
#fields in ML phase:
,segment_id,area_m2,ratio_rg_change,ndvi,ndvi_change,brightness,brightness_change,
gndvi,nd_std,slope_mean,slope_max,b3,b4,b2,b8,height_min,height_max

# fields in segmenting phase:
,segment_id,area_m2,east,north,b4,b3,b2,b8,ndvi,ndvi_change,ratio_rg_change,
brightness,brightness_change,gndvi,slope_max,slope_mean,nd_std,
height_mean,height_min,height_max

"""

import os
import glob
import pandas as pd
import numpy as np

p_tables = os.path.join('k_means_segmentation','tables')
f_labels = 'Labels.xlsx'
sheets = []
# n_images = 80

# for ni in range(n_images):
#     sheets.append('L'+str(ni))

# read sheets L#
df = pd.DataFrame()
df_ = pd.read_excel(f_labels, None);
sheets = df_.keys()
for sh in sheets:
    if sh.startswith('L'):
        df_ = pd.read_excel(f_labels , sheet_name=sh)
        df_['segment_id'] = sh + '_S' + df_['Label'].astype(str)
        df = df.append(df_, ignore_index=True)
df = df.dropna(axis=1, how='all')
df = df.drop('Label', 1)

# read segments
# add fields from \k_means_segmentation\tables\
df_s = pd.DataFrame()
fl = glob.glob(os.path.join('..', '..', p_tables, 'landslide_*.csv'))
for f in fl:
    if f.endswith('.csv'):
        df_ = pd.read_csv(f)
        df_s = df_s.append(df_, ignore_index=True)

# join the two dfs
df_fin = df_s.merge(df,on='segment_id',how='left')
df_fin = df_fin.drop('Unnamed: 0', 1)
df_fin = df_fin[df_fin['Type'].notna()] # this removes all the landslide type = Nan

# save df as csv
df_fin.to_csv('df4ML.csv', index=False)
