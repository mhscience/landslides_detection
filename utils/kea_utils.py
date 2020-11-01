from osgeo import gdal
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
import matplotlib.pyplot as plt
from rasterio.features import shapes
import segmentation.merging_algorithm.merger as merging_algorithm

def kea2shp(config):
    
    nameFile = (element) + "_segmented"
    clumpsFile = config['k_means_segmentation']['output']['segments'] + nameFile + '.kea'
    
    #Read file 
    src = rasterio.open('c:\Users\santinel\Documents\landslides\landslides_detection\datasets\output\k_means_segmentation\segments\landslide_17_segmented.kea') #kea filepath
    image = src.read(1)
    
    plt.imshow(image)
    
    #Convert data from uint32 to int32 and update profile to write to tif (optional - for visualisation in qgis)
    image = image.astype('int32')
    #optional
    profile = src.profile.copy()
    profile.update({
                'dtype': 'int32',
                'driver':'GTIFF'})
    with rasterio.open('N:\My_Documents\MScThesis\landslide_17_segmented.tif', 'w', **profile) as dst:
            dst.write_band(1, image)
    
    #make polygons using rasterio.features.shapes
    results = ({'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image, mask=None, transform=src.transform)))
    
    geoms = list(results)
    #Convert to geodataframe with WKT polygons
    gpd_polygonized_raster  = gpd.GeoDataFrame.from_features(geoms)
    
    #set CRS to get .prj file 
    gpd_polygonized_raster.crs = src.crs
    
    #Write to file
    gpd_polygonized_raster.to_file(driver = 'ESRI Shapefile', filename='C:\Thesis\Data\landslide.shp')
    
    
    # def find_poly(clumpsFile):
    #     import rasterio
    #     from rasterio.features import shapes
    
    #     mask = None
    #     with rasterio.drivers():
    #         with rasterio.open(clumpsFile) as src:
    #             image = src.read(1) # first band
    #             results = (
    #             {'properties': {'raster_val': v}, 'geometry': s}
    #             for i, (s, v) 
    #             in enumerate(shapes(image, mask=mask, transform=src.affine)))
    #     geoms = list(results)
    #     # first feature
    #     print(geoms[0])
