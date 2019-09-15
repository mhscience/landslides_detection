# landslide_detector
Landslide detection using GEE and Python
Author: Ir. Meylin Herrera Herrera 
This tool was created as part of my MSc Thesis In Geomatics made in join collaboration Delft University of Technology (https://www.tudelft.nl/en/) and Deltares Research Institute (https://www.deltares.nl/en/).


#### Minium Requirements:
-Windows OS x64 \
-Run the Requirements file to create a env for this project

Remarks: if it does not work, then follows the steps to install GEOBIA and Scikit learn: 


## GEOBIA: 

A modular system for performing Geographic Object-Based Image Analysis using open source software (Clewley et al., 2014)

The system uses the following libraries: GDAL,RSGISLib,TuiView,RIOS

### Installation:

If using Conda

1. GDAL: for geospatial data manipulation and raster data model
   
Within the conda terminal, install the package running:

```
   conda install -c conda-forge gdal 
```
https://anaconda.org/conda-forge/gdal

2. The Remote Sensing and GIS Library (RSGISLib): for segmentation and attribution of objects

Within the conda terminal, install RSGISLib to a new environment using:

```
  conda create -n rsgislib -c conda-forge rsgislib   

  activate rsgislib
```

3. TuiView: for viewing and manipulating RATs (Raster Attribute Tables)

- To install this package with conda run:  

```
conda config --add channels conda-forge

conda create -n myenv tuiview

conda activate myenv
```
http://tuiview.org/


- To open the raster and/or segmented images files:

Within the conda terminal (in myenv) run: tuiview

4. Raster I/O Simplification (RIOS): for reading, writing and classifying attributed objects

To install this package with conda run:
```
conda install -c conda-forge rios 
```

https://anaconda.org/conda-forge/rios


## Scikit Learn
A free software Machine Learning library for Python 
 
### Requirements 
Python (>= 3.5)\
NumPy (>= 1.11.0)\
SciPy (>= 0.17.0)\
joblib (>= 0.11)

https://scikit-learn.org/stable/install.html

To install this package with conda run:
```
conda install scikit-learn
```
To install pyyaml

```
conda install -c anaconda pyyaml
```
