#Author: Meylin Herrera
#mhscience525@gmail.com / meylinh52@gmail.com
#Description: Apply  k-means implementation (Shepherd  et  al.  (2019]) to segment satellite images and extract features
#Input: satellite imagery
#Output: atrributes tables with features statistics per segments

import rsgislib
from rsgislib import rastergis
from rsgislib.segmentation import segutils
import os
import rios
import pandas as pd
from rsgislib.rastergis import ratutils


def segmentation(imagery_files, config):
    dev_mode = config['dev_mode']

    for element in imagery_files:
        inputImage_difference = imagery_files[element][0]
        inputImage_post = imagery_files[element][1]
        inputImage_color = inputImage_post

        nameFile = (element) + "_segmented"
        clumpsFile = config['k_means_segmentation']['output']['segments'] + nameFile + '.kea'


        # Run segmentation_file.py algorithm
        segutils.runShepherdSegmentation(inputImage_difference, clumpsFile, tmpath=config['k_means_segmentation']['temps']['shepherd'],
                                         numClusters=config['k_means_segmentation']['params']['numClusters'], minPxls=config['k_means_segmentation']['params']['minPxls'],
                                         distThres=config['k_means_segmentation']['params']['distThres'], bands =[1],
                                         sampling=config['k_means_segmentation']['params']['sampling'], kmMaxIter=config['k_means_segmentation']['params']['kmMaxIter'])

        # Features extraction and computation of statistical measures
        # Feature from Image difference
        bs = [rastergis.BandAttStats(band=1, meanField='ratio_rg_change')]
        rastergis.populateRATWithStats(inputImage_difference, clumpsFile, bs)

        bs = [rastergis.BandAttStats(band=2, meanField='ndvi_change')]
        rastergis.populateRATWithStats(inputImage_difference, clumpsFile, bs)

        bs = [rastergis.BandAttStats(band=3, meanField='brightness_change')]
        rastergis.populateRATWithStats(inputImage_difference, clumpsFile, bs)

        # Feature from post_image
        bs = [rastergis.BandAttStats(band=1, meanField='B4'),
              rastergis.BandAttStats(band=2, meanField='B3'),
              rastergis.BandAttStats(band=3, meanField='B2'),
              rastergis.BandAttStats(band=4, meanField='B8'),
              rastergis.BandAttStats(band=5, meanField='ndvi'),
              rastergis.BandAttStats(band=6, maxField='slope_max', meanField='slope_mean'),
              rastergis.BandAttStats(band=7, meanField='mean_height', minField='min_height', maxField='max_height'),
              rastergis.BandAttStats(band=8, meanField='nd_stdDev'),
              rastergis.BandAttStats(band=12, meanField='gndvi'),
              rastergis.BandAttStats(band=13, meanField='brightness')]
        rastergis.populateRATWithStats(inputImage_color, clumpsFile, bs)

        add_Coordinates(clumpsFile)
        if dev_mode:
            input_training = imagery_files[element][2]
            add_Training(clumpsFile, input_training, config)
        reading_tables(clumpsFile, element, nameFile, config['k_means_segmentation']['output']['tables'], config)

def reading_tables(clumps, element,nameFile,path_tables,config):
    dev_mode = config['dev_mode']
    input_features= {}
    data_npixels= rios.rat.readColumn(clumps, 'Histogram')
    data_east= rios.rat.readColumn(clumps, 'Easting')
    data_north = rios.rat.readColumn(clumps, 'Northing')
    if dev_mode:
        data_class = rios.rat.readColumn(clumps, 'class')
        data_class_name = rios.rat.readColumn(clumps, 'class_name')
    data_b4 = rios.rat.readColumn(clumps, 'B4')
    data_b3 = rios.rat.readColumn(clumps, 'B3')
    data_b2 = rios.rat.readColumn(clumps, 'B2')
    data_b8 = rios.rat.readColumn(clumps, 'B8')
    data_ndvi = rios.rat.readColumn(clumps, 'ndvi')
    data_ndvi_change = rios.rat.readColumn(clumps, 'ndvi_change')
    data_ratio = rios.rat.readColumn(clumps, 'ratio_rg_change')
    data_brightness = rios.rat.readColumn(clumps, 'brightness')
    data_brightness_change = rios.rat.readColumn(clumps, 'brightness_change')
    data_gndvi = rios.rat.readColumn(clumps, 'gndvi')
    data_slope_max = rios.rat.readColumn(clumps, 'slope_max')
    data_slope_mean = rios.rat.readColumn(clumps, 'slope_mean')
    data_ndstdDev = rios.rat.readColumn(clumps, 'nd_stdDev')
    data_mean_height = rios.rat.readColumn(clumps, 'mean_height')
    data_min_height = rios.rat.readColumn(clumps, 'min_height')
    data_max_height = rios.rat.readColumn(clumps, 'max_height')

    list_test=[]
    for i in range(data_ratio.size):

        # calculate area per segment
        area= data_npixels[i]*100

        #unique segment ids
        segment_id = 'L' + element.split('_')[1] + '_S' + str(i)

        # #re-escale ndvi_texture
        # nd_sdt = data_ndstdDev[i]*10
        if dev_mode:
            input_features[i] = segment_id, area, data_east[i], data_north[i], data_class[i], data_class_name[i], data_b4[i], data_b3[i], data_b2[i], data_b8[i], \
                          data_ndvi[i], data_ndvi_change[i],data_ratio[i], data_brightness[i],data_brightness_change[i],data_gndvi[i],data_slope_max[i], data_slope_mean[i], \
                          data_ndstdDev[i],data_mean_height,data_min_height[i],data_max_height[i]
        else:
            input_features[i] = segment_id, area, data_east[i], data_north[i], \
                                data_b4[i], data_b3[i], data_b2[i], data_b8[i], \
                                data_ndvi[i], data_ndvi_change[i], data_ratio[i], data_brightness[i], \
                                data_brightness_change[i], data_gndvi[i], data_slope_max[i], data_slope_mean[i], \
                                data_ndstdDev[i], data_mean_height, data_min_height[i], data_max_height[i]

    training_frame = pd.DataFrame(input_features).T

    if dev_mode:
        training_frame_col = pd.DataFrame(training_frame.values, columns=['segment_id','area_m2', 'east', 'north', 'class', 'class_name', 'b4', 'b3','b2','b8', \
                                                                         'ndvi', 'ndvi_change', 'ratio_rg_change','brightness', 'brightness_change','gndvi','slope_max','slope_mean', \
                                                                         'nd_std', 'height_mean','height_min','height_max'])
    else:
        training_frame_col = pd.DataFrame(training_frame.values,
                                          columns=['segment_id', 'area_m2', 'east', 'north', \
                                                   'b4', 'b3', 'b2', 'b8', \
                                                   'ndvi', 'ndvi_change', 'ratio_rg_change', 'brightness',
                                                   'brightness_change', 'gndvi', 'slope_max', 'slope_mean', \
                                                   'nd_std', 'height_mean', 'height_min', 'height_max'])

    #write tables
    training_frame_col.to_csv(path_tables+nameFile+".csv")

#add spatial location
def add_Coordinates (clumpsFile):
    eastings = 'Easting'
    northings = 'Northing'
    rsgislib.rastergis.spatialLocation(clumpsFile, eastings, northings,ratband=1)
    return (clumpsFile)

#add labels (landslide/ non_landslide)
def add_Training (clumpsFile,input_training, config):

    print ('input_training', input_training)
    classesDict = dict()
    classesDict['landslide'] = [1, input_training]

    classesDict['no_landslide'] = [0, config['k_means_segmentation']['input']['training_labels']]

    tmpPath = config['k_means_segmentation']['temps']['shapes']
    trainCol = 'class'
    trainColName = 'class_name'
    ratutils.populateClumpsWithClassTraining(clumpsFile, classesDict, tmpPath,
                                             trainCol, trainColName)
    return (clumpsFile)


def create_image_files(config):
    #Input directories
    image_difference_folder = config['k_means_segmentation']['input']['image_difference']
    post_image_folder = config['k_means_segmentation']['input']['post_event_image']
    training_labels = config['k_means_segmentation']['input']['training_labels']
    imagery_files={}
    for filename in os.listdir(image_difference_folder):
        if filename.endswith(".tif"):
            key_landslide= filename[5:filename.__len__()].split('.')[0]
            input_image = image_difference_folder + filename
            for filename in os.listdir(post_image_folder):
                if filename.endswith(".tif"):
                    input_image_post= post_image_folder + filename
                    key_landslide_post = filename[5:filename.__len__()].split('.')[0]
                    if config['dev_mode']:
                        for filename in os.listdir(training_labels):
                            if filename.endswith(".shp"):
                                input_training = training_labels + filename
                                key_landslide_training = filename[6:filename.__len__()].split('.')[0]
                                if key_landslide == key_landslide_post and key_landslide==key_landslide_training:
                                    imagery_files[key_landslide]= input_image,input_image_post, input_training
                    elif key_landslide == key_landslide_post:
                        imagery_files[key_landslide] = input_image, input_image_post
    return imagery_files


def _test():
    print('add test')

    
def run(config):
    #Output Tables and Segmented Images
    #files iteration within the folder and dictionaries with target imges (values)for every landslide (key)
    imagery_files = create_image_files(config)
    segmentation(imagery_files, config)

if __name__ == "__main__":
        _test()

