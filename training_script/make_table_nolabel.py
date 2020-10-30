# -*- coding: utf-8 -*-
"""
make csv of entire dataset, with no labels by reading the segments csv.

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

# read segments
# add fields from \k_means_segmentation\tables\
df_s = pd.DataFrame()
fl = glob.glob(os.path.join('..', '..', p_tables, 'landslide_*.csv'))
for f in fl:
    if f.endswith('.csv'):
        df_ = pd.read_csv(f)
        df_s = df_s.append(df_, ignore_index=True)

# finalize
df_fin = df_s
df_fin = df_fin.drop('Unnamed: 0', 1)
df_fin = df_fin[~np.array([dfff.endswith('_S0') for dfff in df_fin['segment_id'].astype(str).values])] # remove zeros lines

# save df as csv
df_fin.to_csv('df4ML_all_nolabel.csv', index=False)
