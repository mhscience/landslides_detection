import os
import time
import math
import json
import numpy as np
import pandas as pd
from sklearn.neighbors import KDTree

def save_segments_in_regions(key,segments,config):
    print(key)
    print(config['output']['regions'])
    path = config['output']['regions']
    with open(path + key + '.json', 'w') as json_file:
        json.dump(segments, json_file)


def save_wrong_merged(key, lst, config):
    df = pd.DataFrame(lst)
    path = config['output']['wrong']
    df.to_csv(path+key + r'_wrong_merged_segmentation.csv')

def save_merged_images(key, new_segments_df,config):
    path = config['output']['merged']
    new_segments_df.to_csv(path+key+r'_merged_segmentation.csv')

def load_images_segmentation(config):
    path1 = config['input']['tables']
    landslides_seg = {}
    for filename in os.listdir(path1):  # iterate over the image difference folder
        if filename.endswith('.csv'):
            frame = pd.read_csv(path1 + filename, index_col=False)
            frame.rename(columns={'Unnamed: 0': 'segment'}, inplace=True)  # rename columns
            frame.drop(columns={'height_mean'}, inplace=True)
            landslides_seg[filename[0:14]] = frame
    return landslides_seg

def clean(frame):

            frame.loc [(frame['b4']<1)& (frame['b3']<1) &(frame['b2']<1), 'class']='no_data'  #identify and delete no data values
            frame.loc [(frame['ratio_rg_change']<0.09), 'class']='no_data'
            frame.drop(frame[(frame['class']=='no_data')].index, inplace=True)
            #
            frame.loc [(frame['brightness']>2 , 'class')]='clouds_bright'
            frame.drop(frame[(frame['class']=='clouds_bright')].index, inplace=True)
            #
            frame.loc[(frame['brightness'] < 0.50, 'class')] = 'shadows'
            frame.drop(frame[(frame['class'] == 'shadows')].index, inplace=True)
            #
            frame.loc [(frame['ndvi'] < -(0.1)) ,'class']='water'  #identify and delete water
            frame.drop(frame[(frame['class']=='water')].index, inplace=True)
            #
            frame.loc [(frame['area_m2']<5000,'class')]='small_segments'  #identify and delete very small segments (<2000m2)
            #
            frame.drop(frame[(frame['class']=='small_segments')].index, inplace=True)
            #
            frame.loc [(frame['area_m2']>2000000),'class']='large_segments'  #identify and delete very large segmentd segments (>1000000m2)
            frame.drop(frame[(frame['class']=='large_segments')].index, inplace=True)

            return frame

def min_ratio_segment(data_frame):
    return data_frame.loc[data_frame['ratio_rg_change'].idxmin()]

def check_region_conditions(region_current, nearest_neighbour_df, ndvi_mean_w_global, ndvi_std_w_global, ndvi_change_mean_w_global, ndvi_change_std_w_global, rgd_mean_w_global, rgd_std_w_global, config):

    region_current_df = pd.DataFrame(region_current)
    ndvi_mean = compute_mean(region_current_df, 'ndvi')
    ndvi_neighbour = nearest_neighbour_df['ndvi']
    ndvi_change_neighbour = nearest_neighbour_df['ndvi_change']

    diff_ndvi = abs(ndvi_neighbour - ndvi_mean)
    
    rgd_neighbour = nearest_neighbour_df['ratio_rg_change']

    n_std_ndvi_change = config['params']['n_std_ndvi_change']
    n_std_rgd = config['params']['n_std_rgd']

    thr = config['params']['thr_coarse']
    thr2 = config['params']['thr_fine']

    right_boundary_ndvi_change = ndvi_change_mean_w_global + n_std_ndvi_change*ndvi_change_std_w_global

    right_boundary_rgd = rgd_mean_w_global + n_std_rgd*rgd_std_w_global
    #NEW
    if ndvi_neighbour > ndvi_mean_w_global and diff_ndvi < thr:
        return True
    if ndvi_change_neighbour < right_boundary_ndvi_change and diff_ndvi < thr:
        return True
    if rgd_neighbour < right_boundary_rgd and diff_ndvi < thr:
        return True
    if diff_ndvi < thr2:
        return True

    return False

def create_kd_tree(available_segments):
    aux_dic = dict()
    coordinates = []
    segments_coordinates = available_segments[['segment_id', 'east', 'north']]
    for index, row in segments_coordinates.iterrows():
        aux_dic[(row['east'], row['north'])] = row['segment_id']
        coordinates.append((row['east'], row['north']))
    kd_tree = KDTree(np.array(coordinates))
    return aux_dic, coordinates, kd_tree


def find_nearest_neighbours(current_segment, aux_dic, coordinates, kd_tree):
    current_segment_coordinates = (current_segment['east'], current_segment['north'])
    dist, ind = kd_tree.query([current_segment_coordinates],5)
    segment_list = []
    for i in ind[0]:
        if coordinates[i] in aux_dic:
            segment_list.append(aux_dic[coordinates[i]])
    return segment_list


def compute_mean(region, prop):
    return (region[prop] * region['area_m2']).sum() / region['area_m2'].sum()

def compute_std(region, prop):
    ndvi_mean_w = compute_mean(region, prop)
    return math.sqrt(((region[prop] - ndvi_mean_w)**2).sum() / len(region))

def merge_segments_no_class(regions,key,config):
    list_of_series = []
    segments_region = {}
    i = 0
    for region in regions:
        df_region = pd.DataFrame(region)
        region_id = df_region['segment_id'].values[0][:3] + '_' + 'R' + str(i)
        for segment in region:
            segments_region.setdefault(region_id, []).append(segment['segment_id'])
        data = merge_region(df_region, region_id, 0)
        list_of_series.append(data)
        i = i + 1
    save_segments_in_regions(key, segments_region, config)
    return pd.DataFrame(list_of_series, columns=['segment_id', 'area_m2', 'ratio_rg_change', 'ndvi', 'ndvi_change', 'brightness', 'brightness_change','gndvi',  'nd_std', 'slope_mean', 'slope_max', 'b3', 'b4', 'b2', 'b8', 'height_min', 'height_max'])


def merge_segments_with_class(regions, key, config):
    df = pd.DataFrame([], columns=['segment_id','class','area_m2','ratio_rg_change', 'ndvi', 'ndvi_change','brightness','brightness_change','gndvi', 'nd_std', 'slope_mean','slope_max', 'b3', 'b4','b2','b8', 'height_min','height_max'])
    list_of_series = []
    segments_region = {}
    i = 0
    for region in regions:
        df_region = pd.DataFrame(region)
        region_id = df_region['segment_id'].values[0][:3] + '_' + 'R' + str(i)
        class_relabeled_mean = df_region['class'].mean()

        # create a dictionary with key = region_id, value = segments_ids
        for segment in region:
            segments_region.setdefault(region_id, []).append(segment['segment_id'])
            segments_region.setdefault(region_id, []).append(int(segment['class']))

        if class_relabeled_mean == 0:
            data = merge_region(df_region,region_id,0)
            list_of_series.append(data)
        else:
            list_class_0 = pd.DataFrame([], columns=['segment_id','class','area_m2','ratio_rg_change', 'ndvi', 'ndvi_change','brightness','brightness_change','gndvi', 'nd_std', 'slope_mean','slope_max', 'b3', 'b4','b2','b8', 'height_min','height_max'])


            counter_class_1 = 0
            for segment in region:

                single_segment = pd.Series(
                    [segment['segment_id'], segment['class'], segment['area_m2'], segment['ratio_rg_change'], segment['ndvi'], segment['ndvi_change'],segment['brightness'],\
                     segment['brightness_change'],segment['gndvi'],segment['nd_std'], segment['slope_mean'], segment['slope_max'],segment['b3'],segment['b4'],segment['b2'],segment['b8'],\
                     segment['height_min'],segment['height_max']],
                    index=df.columns)


                if segment['class'] == 0:
                    list_class_0 = list_class_0.append(single_segment, ignore_index=True)
                else:
                    counter_class_1 = counter_class_1 + 1
                    list_of_series.append(single_segment)

            if len(list_class_0) > 0:
                data = merge_region(list_class_0,region_id,0)
                list_of_series.append(data)
            print('############################## Stats ##############################')
            print('Number of regions:  '+str(len(region)) +'  Class 0: '+str(len(list_class_0))+'  Class 1: '+str(counter_class_1) + ' P0: '+str(len(list_class_0)/len(region)) + 'P1: '+str(counter_class_1/len(region)))
            if(((counter_class_1)/len(region)) != 0 and (counter_class_1/len(region)) != 1):
                save_wrong_merged(key +'_'+ str(int(time.time())), region, config)

        i = i + 1
    save_segments_in_regions(key, segments_region, config)
    final_regions = pd.DataFrame(list_of_series, columns=['segment_id', 'class', 'area_m2', 'ratio_rg_change', 'ndvi', 'ndvi_change', 'brightness', 'brightness_change','gndvi',  'nd_std', 'slope_mean', 'slope_max', 'b3', 'b4', 'b2', 'b8', 'height_min', 'height_max'])

    # control heterogeneos regions:
    print('len_regions', ', ',  'before_', len(regions), ',', 'after_',  len(final_regions), 'region_id_', key)
    return final_regions

def merge_region(list_of_regions, region_id, class_label):
    df = pd.DataFrame([], columns=['segment_id', 'class', 'area_m2', 'ratio_rg_change', 'ndvi', 'ndvi_change', 'brightness', 'brightness_change', 'gndvi', 'nd_std', 'slope_mean', 'slope_max', 'b3', 'b4', 'b2', 'b8', 'height_min', 'height_max'])
    ratio_rg = (list_of_regions['ratio_rg_change'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    ndvi = (list_of_regions['ndvi'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    brightness = (list_of_regions['brightness'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    nd_std = (list_of_regions['nd_std'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    slope_mean = (list_of_regions['slope_mean'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    b3 = (list_of_regions['b3'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    gndvi = (list_of_regions['gndvi'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    area_m2 = list_of_regions['area_m2'].sum()
    brightness_change = (list_of_regions['brightness_change'] * list_of_regions['area_m2']).sum() / (
        list_of_regions['area_m2'].sum())
    ndvi_change = (list_of_regions['ndvi_change'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    b4 = (list_of_regions['b4'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    b2 = (list_of_regions['b2'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    b8 = (list_of_regions['b8'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    slope_max = (list_of_regions['slope_max'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    height_min = (list_of_regions['height_min'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())
    height_max = (list_of_regions['height_max'] * list_of_regions['area_m2']).sum() / (list_of_regions['area_m2'].sum())

    return pd.Series([region_id, class_label,area_m2, ratio_rg, ndvi, ndvi_change,brightness, brightness_change, \
                      gndvi,nd_std, slope_mean,slope_max, b3,b4,b2,b8,height_min, height_max], index=df.columns)

def sort_seeds(seeds_current, region_current):
    region_current_df = pd.DataFrame(region_current)
    mean = compute_mean(region_current_df, 'ndvi')
    return sorted(seeds_current, key=lambda seed:  abs(seed['ndvi'] - mean))


# Enter list of segments
def remove_tiles(region):
    df_region = pd.DataFrame(region)
    independent_segments = []

    if len(region) < 5:
        for segment in region:
            independent_segments.append(segment)
        return independent_segments
    return []

# Region growing
def region_growing(available_segments, config):
    # Compute Global Means
    ndvi_mean_w_global = compute_mean(available_segments, 'ndvi')
    ndvi_std_w_global = compute_std(available_segments, 'ndvi')
    
    rgd_mean_w_global = compute_mean(available_segments, 'ratio_rg_change') 
    rgd_std_w_global = compute_std(available_segments, 'ratio_rg_change')

    ndvi_change_mean_w_global = compute_mean(available_segments, 'ndvi_change')
    ndvi_change_std_w_global = compute_std(available_segments, 'ndvi_change')
    print("Init Segments ", len(available_segments))
    print("ndvi_change_mean_w_global ", ndvi_change_mean_w_global)
    print("ndvi_change_std_w_global ", ndvi_change_std_w_global)
    print("ndvi_mean_w_global ",ndvi_mean_w_global)
    print("ndvi_std_w_global ",ndvi_std_w_global)
    print("rgd_mean_w_global ",rgd_mean_w_global)
    print("rgd_std_w_global ",rgd_std_w_global)

    aux_dic, coordinates, kd_tree = create_kd_tree(available_segments)
    region_list = []
    while len(available_segments) > 0:
        region_current = []
        seeds_current = []
        segment_min = min_ratio_segment(available_segments)
        seeds_current.append(segment_min)
        region_current.append(segment_min)
        available_segments.drop(
            available_segments[(available_segments['segment_id'] == segment_min['segment_id'])].index, inplace=True)

        while len(seeds_current) > 0:
            # Order Seeds from closer to current region
            seeds_current = sort_seeds(seeds_current, region_current)

            # Find N-N
            seed_current_df = seeds_current.pop(0) #use index zero the closer region
            nearest_neighbours_ids = find_nearest_neighbours(seed_current_df, aux_dic, coordinates, kd_tree)
            for j in range(len(nearest_neighbours_ids)):
                nearest_neighbour_id = nearest_neighbours_ids[j]
                nearest_neighbour = available_segments.loc[available_segments['segment_id'] == nearest_neighbour_id].squeeze()
                if (not nearest_neighbour.empty) and (check_region_conditions(region_current, nearest_neighbour, ndvi_mean_w_global, ndvi_std_w_global,ndvi_change_mean_w_global, ndvi_change_std_w_global, rgd_mean_w_global, rgd_std_w_global, config)):
                    region_current.append(nearest_neighbour)
                    available_segments.drop(available_segments[(available_segments['segment_id'] == nearest_neighbour['segment_id'])].index, inplace=True)
                    seeds_current.append(nearest_neighbour)
                # end if
            # end for
        # end while

        # Do not merge small regions
        independent_segments = remove_tiles(region_current)
        if (len(independent_segments) > 0):
            for independent in independent_segments:
                region_list.append([independent])
        else:
            region_list.append(region_current)
    # end while
    return region_list

def run(config):
    dev_mode = config['dev_mode']
    config = config['mergin_algorithm']
    images_segmentation = load_images_segmentation(config)

    for key in images_segmentation.keys():
        print('load image ' + key)
        # 1 load
        image_landslide = images_segmentation[key]
        # 2 clean images
        image_landslide = clean(image_landslide)
        # 3 merge segments from same image using region growing
        regions = region_growing(image_landslide, config)
        # 4 calculate new segments properties
        if dev_mode:
            new_segments = merge_segments_with_class(regions, key, config)
        else:
            new_segments = merge_segments_no_class(regions, key, config)
        # 5 save new table to csv file
        save_merged_images(key, new_segments, config)

def main():
    print('add main')

if __name__ == "__main__":
    main()
