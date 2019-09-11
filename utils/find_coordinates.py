import json
import os
import segmentation.merging_algorithm.merger as merging_algorithm


def findCoordinates(config):
    # Read predictions
    pred = []
    reg = []
    region_files = os.listdir(config['model']['regions'])
    for f in region_files:
        with open(config['model']['regions']+f) as json_file:
            data = json.load(json_file)
            reg.append(data)

    prediction_files = os.listdir(config['model']['predictions'])
    for f in prediction_files:
        with open(config['model']['predictions']+f) as json_file:
            data = json.load(json_file)
            pred.append(data)
    # Read CVS with all information
    segments_dict = merging_algorithm.load_images_segmentation(config['mergin_algorithm'])

    for p in pred:
       for k, segments in p.items():
            for segment_value in segments:
                segment_value = find_ids(reg, segment_value)
                for key, df in segments_dict.items():
                    if(len(df.loc[df['segment_id'] == segment_value]) >0 ):
                        print(df.loc[df['segment_id'] == segment_value][['east','north']])


def find_ids(regions,segment_value):
    for region in regions:
        for k,v in region.items():
            if(segment_value == k):
                return v[0]