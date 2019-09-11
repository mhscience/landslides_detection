from joblib import dump, load
import numpy as np
import pandas as pd
import os
from scipy import stats
import json

def save_landslides_keys(file_name,predictions,config):

    path = config['model']['predictions']+file_name+'.json'
    with open(path, 'w') as json_file:
        json.dump(predictions, json_file)

# ### Calculate relative relief
def relative_relief(df_train, height_min, height_max):
    for key in df_train:
        relative_relief_list = []

        for i in range(len(df_train[key])):
            relative_relief = (df_train[key][height_max].iloc[i] - df_train[key][height_min].iloc[i])
            relative_relief_list.append(relative_relief)

        df_train[key]['relative_relief'] = relative_relief_list

def change_dataTypes(data_column, df):
    df['class'] = df['class'].astype('int64')
    #        df['brightness_change'] = df['brightness_change'].astype('float64')
    df[data_column] = df[data_column].astype('category')

def neighbours_relationship(df_train, feature, area):
    for key in df_train:

        # normalize the area values per segment:
        weighted_mean = (df_train[key][feature] * df_train[key][area]).sum() / (df_train[key][area].sum())
        mean_all_segments = df_train[key][feature].mean()
        feature_subtraction_deviation = []

        for i in range(len(df_train[key])):
            # Subtract the mean from each observation and squared it
            mean_weighted_subtraction = (df_train[key][feature].iloc[i] - weighted_mean)
            new_name_feature_deviation = feature[0:] + '_deviation'
            feature_subtraction_deviation.append(mean_weighted_subtraction)

        # Create a column from the list
        df_train[key][new_name_feature_deviation] = feature_subtraction_deviation

def make_predictions(df_frame,rforest_test,config):
    predictions = []
    predicted_val_data = {}

    X_val_array = df_frame.values
    X_val_numeric = np.delete(X_val_array, 0, 1)
    predictions_validation = rforest_test.predict(X_val_numeric)

    for i in range(len(X_val_array)):
        predicted_val_data[(X_val_array[i][0])] = predictions_validation[i]
    ld_count = 0
    #ld_total_only_one_photo = len(df)

    for key, value in predicted_val_data.items():
        if value == 1:
            ld_count = ld_count + 1
            print('Positive  Landslide:', key)
            predictions.append(key)
    print('----------------------------------------------------')
    if (ld_count > 0):
        save_landslides_keys(predictions[0].split('_')[0],{ predictions[0].split('_')[0] : predictions}, config)
        return 1
    return 0


def run(config):
    model_file = config['model']['path']
    path = config['model']['segments']

    rforest_test = load(model_file)
    df_val_data = {}

    for filename in os.listdir(path):  #iterate over the image difference folder
         if filename.endswith('.csv'):
            frame= pd.read_csv(path+filename,index_col=False)
            frame.rename( columns={'Unnamed: 0':'segment'}, inplace=True)  #rename columns
            df_val_data[filename[0:12]] = frame

    # for key in df_val_data:
    #     change_dataTypes('class',df_val_data[key])
    #     change_dataTypes('segment',df_val_data[key])

    for key in df_val_data:
        cols = df_val_data[key][['ndvi','b3','slope_mean','brightness','ndvi_change','ratio_rg_change']]
        z = np.abs(stats.zscore(cols))
        print ("Maximum Z:", z.max(), key ) # showing that outlier have been detected
        df_val_data[key] = df_val_data[key][(z <5).all(axis=1)]

    neighbours_relationship(df_val_data,'ndvi','area_m2')
    neighbours_relationship(df_val_data,'ratio_rg_change','area_m2')
    neighbours_relationship(df_val_data,'b3','area_m2')
    neighbours_relationship(df_val_data,'brightness','area_m2')
    neighbours_relationship(df_val_data,'gndvi','area_m2')
    neighbours_relationship(df_val_data,'ndvi_change','area_m2')
    neighbours_relationship(df_val_data,'brightness_change','area_m2')

    relative_relief (df_val_data, 'height_min', 'height_max')

    df_data = []

    for key in df_val_data:
        df = df_val_data[key]
        df_new = df[['segment_id', 'ndvi','ratio_rg_change_deviation','brightness_change_deviation','ndvi_change_deviation','brightness','slope_mean',
                    'gndvi_deviation','slope_max','nd_std','relative_relief']]
        if df_new.size == 0:
            print('Error Empty dataframe for:',key)
        else:
            df_data.append(df_new)

    count = 0
    for df in df_data:

        if make_predictions(df, rforest_test, config) == 1:
              count = count + 1
    print('count_per_picture:', count)

