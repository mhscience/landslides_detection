# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 18:23:08 2020

@author: santinel
"""

import os
from osgeo import ogr
import pandas as pd

#csv file from ML model
# segmented images to read: 0, 1, 15, 17, 2, 43, 47, 55, 59.
#csvfile = r'd:\new_stuff\ls\k_means_segmentation\new_tables\df4ML_all_withProbability_nonRandom.csv'
csvfile = r'd:\new_stuff\ls\k_means_segmentation\new_tables\df4ML_all_withProbability_model1noL2.csv'
#path where segments are. Just copied the ones in viz to a test folder,
#so that shapes can be copied inplace
#inpath = r'd:\new_stuff\ls\k_means_segmentation\new_tables\new_viz\nonrandom2'
inpath = r'd:\new_stuff\ls\k_means_segmentation\new_tables\new_viz\random1noL2'
lsmap = 'landslide_59_segmented' #0,1,15,17,2,43,47,55,59
ls = 'landslide_59_segmented.shp'
L = 'L' + lsmap.split('_')[1]
geometryType = ogr.wkbPolygon

# Open a Shapefile, and get field names
#source = ogr.Open(os.path.join(path, lsmap, ls), update=True)
driver = ogr.GetDriverByName('ESRI Shapefile')
inds = driver.Open(os.path.join(inpath, lsmap, ls), 1) 

layer = inds.GetLayer()
layer_defn = layer.GetLayerDefn()
field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
print(len(field_names), 'landslide_' in field_names) # check if existing
# Add a new field called landslide
new_field = ogr.FieldDefn('landslide_', ogr.OFTReal)
layer.CreateField(new_field)
# check new field
layer = inds.GetLayer()
layer_defn = layer.GetLayerDefn()
print('fields are ' + str(
    [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]))

# read csv file
df = pd.read_csv(csvfile)

# write field based on csv coming from ML
for fc in range(layer.GetFeatureCount()):
    print(fc)
    f = layer.GetFeature(fc)
    S = 'S' + str(int(f.GetField('raster_val')))
    segment_id = L + '_' + S
    if S == 'S0':
        f.SetField('landslide_', 0)
        continue
    prob = df.loc[df['segment_id']==segment_id,'LS_probability'].to_list()[0]
    f.SetField('landslide_', prob)
    
    layer.SetFeature(f)
    layer.SyncToDisk()
    
#fc=4
#f = layer.GetFeature(fc)    
#f.ExportToJson()

# Close the Shapefile
inds = None
outds = None
print('eof')
