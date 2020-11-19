# landslide_detector


The landslide_detector is a tool developed to detect landslides from optical remotely sensed images using Object-Based Image Analysis (OBIA) and Machine Learning (Random Forest classifier).

This tool was developed to test the methodology proposed in [my master thesis](https://repository.tudelft.nl/islandora/object/uuid%3A52fe6b3b-ec0b-4cad-b51d-7798830688a4?collection=education) in Geomatics at Delft University of Technology. This implementation can be used to assist landslides experts/non-experts in detecting new landslides events and improve existing inventories.

This project was made in join collaboration [Delft University of Technology](https://www.tudelft.nl/en/) and [Deltares Research Institute](https://www.deltares.nl/en/).

The tool is built using open source software: [Google Earth Engine(GEE)](https://earthengine.google.com/) and Python with their libraries [Remote Sensing and GIS software library (RSGISLib)](https://www.rsgislib.org/) and [Scikit-Learn](https://scikit-learn.org/stable/). It includes three main components:

![name me](/doc/img/segmentation.png)
*Image pre-processing and segmentation; sample in a remote area in Italy. (a) Cloud-free pre-landslide image. (b) Cloud-free post-landslide image. (c) Image difference using band ratioing red/green (RGD). (d) Image segmentation.*

- [Pre-processing script](https://github.com/mhscience/landslides_detection/blob/master/pre_processingGEE/pre_processing_thesis_mh.js) developed for Google Earth Engine. The script obtains cloud-free images from optical satellite imagery (Sentinel-2), extracts spectral and topographic features from Sentinel-2 and global Digital Elevation Model (DEM), and computes new landslides diagnostic features at pixel level

- [Image segmentation program](https://github.com/mhscience/landslides_detection/tree/master/segmentation) developed in Python.  Image segmentation is the first step towards the application of OBIA. It consists on the subdivision of an image into spatially continuous, disjoint, and relative homogeneous regions that refer to segments. This stage is implemented with an initial segmentation using a [k-means script](https://github.com/mhscience/landslides_detection/tree/master/segmentation/k_means_segmentation)   (developed using [RSGISLib](https://www.rsgislib.org/)).

- [Image classification script](https://github.com/mhscience/landslides_detection/tree/master/model) to detect the landslide segments. Once segments with features statistics are obtained from the Image segmentation step, the image is classified by assigning each segment to a class. The classification is conducted using supervised Machine Learning, specifically the Random Forest algorithm

We provide a [script](https://github.com/mhscience/landslides_detection/tree/master/training_script) for model training and testing.

#### Quickstart
[See our tutorial](https://github.com/mhscience/landslides_detection/wiki)

#### Author: 
MSc.ir. Meylin Herrera Herrera  
Master in Geomatics @ Delft University of Technology   
Contact: mhscience@gmail.com  

#### Contributors
Dr.ir. Faraz Tehrani @ Deltares Research Institute  
Ir. Giorgio Santinelli @ Deltares Research Institute

#### Contributing

We encourage you to contribute. Please check our [contributing guidelines](https://github.com/mhscience/landslides_detection/blob/master/contributing.md)

