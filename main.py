import os
import glob
import yaml
import time
from distutils.dir_util import copy_tree

from utils.file_io import remove_files
from utils.find_coordinates import findCoordinates
import segmentation.k_means_segmentation.initial_segmentation_thesis_mh as k_means
import segmentation.merging_algorithm.merger as merging_algorithm
import model.model as md

# Read Config file
config = {}
with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

print("loading config success")

print("cleaning output folders")
print("cleaning k_means_segmentation output files")
remove_files(glob.glob(config['k_means_segmentation']['output']['tables']+"*"))
remove_files(glob.glob(config['k_means_segmentation']['output']['segments']+"*"))
print("cleaning merging algorithm output files")
remove_files(glob.glob(config['mergin_algorithm']['output']['wrong']+"*"))
remove_files(glob.glob(config['mergin_algorithm']['output']['merged']+"*"))
remove_files(glob.glob(config['mergin_algorithm']['output']['regions']+"*"))
remove_files(glob.glob(config['model']['predictions']+"*"))
print("cleaning output folders success")

# Run k-means
print("1 Running k-means algorithm")
k_means.run(config)

# Run Merging Algorithm
print("2 Running merging algorithm")
merging_algorithm.run(config)

# Run Model
print("3 Searching for landslides")
md.run(config)

print("4 Printing landlines coordinates")
findCoordinates(config)

if config['save_dataset']:
    print("Saving dataset")
    fromDirectory = "datasets"
    toDirectory = "historics/datasets"+ str(int(time.time()))
    copy_tree(fromDirectory, toDirectory)
    #Remove files
    if len([name for name in glob.glob('historics/*')]) == 5:
        oldest_file = min('historics/', key=os.path.getctime)
        remove_files(oldest_file)
