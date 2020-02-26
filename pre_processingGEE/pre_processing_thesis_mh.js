Imports: Sentinel-2 MSI: MultiSpectral Instrument, Level-1C
         
          ALOS DSM: Global 30m


// Author:
//  Meylin Herrera  // mhscience525@gmail.com
//
// Date: 
//  29/08/2019
//
// Description:
//   This script is used to analyze landslide events;
//   Generates a set cloud-free images pre-and-pos-event that includes ndvi, slope, elevation, glcm
//   Generates the image difference using band rationing (red/green) and includes ndvi, slope, elevation, glcm.
//
// Imports:
//  - Add to GEE sentinel2 and dem_alos
//
// Dependencies:
//   - geetools https://github.com/fitoprincipe/geetools-code-editor
//
// Input:
//   - A feature collection, from google fusion table (to generate a fusion table see https://fusiontables.google.com)
//     with the following mandatory colums [landslide_id, event_date, longitude, latidude]
//     For more information to read fusion tables check ee.FeatureCollection
//     you can point to your fusion tables by changing fusion_table_id (do not use more than 50 rows per table)
//
// Output:
//   - A series of images to download to Google drive, Check Export_to_drive;
//   diff_id contains the image difference
//   post_description_id contains the pos-event image
//   pre_description_id contains the pre-event  image   
//
// Properties:
// Change the values under PROPERTIES, as default search from the event date of free images is 4 and for a composite is 12 months.
//
// How to use this code:
// 1. Set your Google Drive and Fusion tables.
// 2. Rename the Properties; Use your settings from step 1.
// 3. Check the console tab,  wait until your images are ready to download. 
// 4. Download the images to google drive, from Tasks tab

//Properties
//Set your appropiate google drive-folder and landslide fusion table,
//for more information look the header of this file.
var my_google_drive_folder = "Landslides_images_June2019";
var fusion_table_id = 'ft:1pt_zzsvIVF1WawnCIinydD9y8NQrLuvrZgsv89OB';   
var free_cloud_month_range = 4;
var composite_image_search_range = 12;
var download_prefix_description = 'landslide_test';

// Dependencies
var cloud_masks = require('users/fitoprincipe/geetools:cloud_masks');
var sentinel2function = cloud_masks.sentinel2();

var rgbVis = {
	min : 0.0,
	max : 3000,
	bands : ['B4', 'B3', 'B2'],
};


// Util: prepare image for download 
var create_download_image = function (id, image, region, description) {
	var download_image = {
		id : id,
		image : image,
		region : region,
		description : description + '_' + id
	};
	return download_image;
};

// Util: Exports an image to drive within a region and a description
var export_to_drive = function (image, region, description) {
	Export.image.toDrive({
		image : image, //.visualize(rgbVis),
		description : description,
		scale : 10,
		folder : my_google_drive_folder,
		region : region,
	});
};

// Util: Download a collection of images to drive within a region and a description as harcoded variables
var download_images_to_drive = function (download_images) {
	//Calls export_to_drive over a collection
	for (var i = 0; i < download_images.length; i++) {
		var image = download_images[i].image;
		var description = download_images[i].description;
		var region = download_images[i].region;
		export_to_drive(image, region, description);
	}
};

// Main: process_landslides_images receives a collection of landslides locations, free_cloud range, composite range and
// download description, 
var process_landslides_images = function (satellite, landslides, cloud_months, composite_months, description_prefix) {
	landslides.toList(landslides.size()).evaluate(function (landslide_list) {
		var min_images = landslide_list.length;
		var collector = create_image_collector(min_images);
		print('Processing Images');

		for (var i = 0; i < landslide_list.length; i++) {
			var landslide_item = ee.Feature(landslide_list[i]);
			var description_post = 'post_' + description_prefix;
			var description_pre = 'pre_' + description_prefix;
			//Start 2 pre-and-post image proceses, 
			process_images_from_landslide_post(satellite, landslide_item, cloud_months, composite_months, description_post, collector);
			process_images_from_landslide_pre(satellite, landslide_item, cloud_months, composite_months, description_pre, collector);
		}
	});
};

// Main:  Attempts to retrive the image with the lower percentage of clouds 
var find_less_cloudy_image = function (images, cloud_index, composite_case, callback, context) {
  print('Looking for free cloud images');
	var sort_post = true;
		if (context === 'pre') {
			sort_post = false;
		}
		var increase = 5;
	var composition_threshold = 30;
	var error = 110;
	ee.ImageCollection(images).filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_index)).size().gt(0).evaluate(function (result) {
		if (result) {
			var image_found = ee.ImageCollection(images).filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_index)).map(sentinel2function).sort('CLOUDY_PIXEL_PERCENTAGE', true).first(); //'system:time_start'
			callback(ee.Image(image_found));
		} else if (cloud_index >= composition_threshold) {
			composite_case();
		} else if (cloud_index >= error) {
			print('Something wrong just happened; Image cloud index greater than 100, nothing found :(');
			return -1;
		} else {
			var increment = cloud_index + increase;
			find_less_cloudy_image(images, increment, composite_case, callback, context);
		}
	});
};

// Main:  Creates a composite image
var composite_image = function (images, cloud_index, callback) {
	var up = 10;
	var error = 110;
	ee.ImageCollection(images).filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_index)).size().gt(0).evaluate(function (result) {
		if (result) {
			var composite = ee.ImageCollection(images).filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_index)).map(sentinel2function).median();
			callback(ee.Image(composite));
		} else if (cloud_index > 110) {
			print('Something wrong just happened during composite; Image cloud index greater than 100, nothing found :(');
			return -1;
		} else {
			var increment = cloud_index + up;
			composite_image(images, increment, callback);
		}
	});
};

// Util: Retrive coordinates
var get_coordinates = function (landslide, callback) {
	var coordinates = landslide.geometry().coordinates();
	ee.Geometry.Point(coordinates).evaluate(
		function (result) {
		callback(result);
	});
};

//Util: calculate texture parameters
var texture = function (image) {

	//compute the texture
	var nir = image.select('B8');

	// Define a neighborhood with a kernel.
	var square = ee.Kernel.square({
			radius : 4
		});

	// Compute entropy and display.
	var entropy = nir.entropy(square);
	var glcm = nir.glcmTexture({
			size : 4
		});

	return glcm;

};

// Main:  Creates a region and exectute a callback fucntion with point, region as parameters
var process_region_and_coordinates = function (landslide, callback) {

	var create_region = function (point) {
		var region = ee.Geometry.Point([point.coordinates[0], point.coordinates[1]]).buffer(2500).bounds();
		region.evaluate(function (region_result) {
			callback(point, region_result);
		});
	};
	get_coordinates(landslide, create_region);
};

// Main: Process images after the landslide event
var process_images_from_landslide_post = function (satellite, landslide, adv_months_cloud_case, adv_months_composite_case, description, image_collector) {
	var context = 'post';
	//3.B Composite Path, if the cloud index percetange is above the threshold this function will be called
	//see find_less_cloudy_image
	var composite_case = function () {
		//1 Composite runs on a 8 Months period
		var process_composite_event_date = function (landslide) {
			var event_date = ee.Date(landslide.get('event_date'));
			event_date.evaluate(function (ev_result) {
				process_composite_post_event_date(ev_result);
			});
		};
		//2 Calculate the end of range after the landslide
		var process_composite_post_event_date = function (ev_result) {
			var post_event = ee.Date(ev_result.value).advance(ee.Number(adv_months_composite_case), 'Month');
			post_event.evaluate(function (post_ev_result) {
				var event_date = ee.Date(ev_result.value);
				var post_event = ee.Date(post_ev_result.value);
				process_composite_event_time_range(event_date, post_event);
			});

			//3 With the images in range from (1) and (2) Process the images see process_images function
			var process_composite_event_time_range = function (event_date, post_event) {
				var get_image_from_composite = function (coordinates, region) {
					var images = satellite.filterBounds(coordinates).filterDate(event_date, post_event);
					process_composite_images(images, context, region, landslide, description, image_collector);
				};
				process_region_and_coordinates(landslide, get_image_from_composite);
			};
		};
		process_composite_event_date(landslide);
	};

	//3 With the images in range from (1) and (2) Process the images see process_images function
	var process_event_time_range = function (event_date, post_event) {
		var get_image = function (coordinates, region) {
			var images = satellite.filterBounds(coordinates).filterDate(event_date, post_event);
			process_images(images, context, region, composite_case, landslide, description, image_collector);
		};
		process_region_and_coordinates(landslide, get_image);
	};
	//1 Get the event date from landlide event date history
	var process_event_date = function (landslide) {
		var event_date = ee.Date(landslide.get('event_date'));
		event_date.evaluate(function (ev_result) {
			process_post_event_date(ev_result);
		});
	};
	//2 Calculate the end of range after the landslide
	var process_post_event_date = function (ev_result) {
		var post_event = ee.Date(ev_result.value).advance(adv_months_cloud_case, 'Month');
		post_event.evaluate(function (post_ev_result) {
			var event_date = ee.Date(ev_result.value);
			var post_event = ee.Date(post_ev_result.value);
			process_event_time_range(event_date, post_event);
		});
	};
	process_event_date(landslide);
};

// Main:  Process images before the landslide event
var process_images_from_landslide_pre = function (satellite, landslide, back_months_cloud_case, back_months_composite_case, description, image_collector) {
	var context = 'pre';
	//3.B Composite Path, if the cloud index percetange is above the threshold this function will be called
	//see find_less_cloudy_image
	var composite_case = function () {
		//1 Composite runs on a 8 Months period
		var process_composite_event_date = function (landslide) {
			var event_date = ee.Date(landslide.get('event_date'));
			event_date.evaluate(function (ev_result) {
				process_composite_post_event_date(ev_result);
			});
		};
		//2 Calculate the end of range after the landslide
		var process_composite_post_event_date = function (end_date_result) {
			//3 With the images in range from (1) and (2) Process the images see process_images function
			var process_composite_event_time_range = function (event_date, post_event) {
				var get_image_from_composite = function (coordinates, region) {
					var images = satellite.filterBounds(coordinates).filterDate(event_date, post_event);
					process_composite_images(images, context, region, landslide, description, image_collector);
				};
				process_region_and_coordinates(landslide, get_image_from_composite);
			};

			var start_event = ee.Date(end_date_result.value).advance(ee.Number(-1 * back_months_composite_case), 'Month');
			start_event.evaluate(function (start_ev_result) {
				var start_date = ee.Date(start_ev_result.value);
				var end_date = ee.Date(end_date_result.value);
				process_composite_event_time_range(start_date, end_date);
			});
		};
		process_composite_event_date(landslide);
	};

	//3 With the images in range from (1) and (2) Process the images see process_images function
	var process_event_time_range = function (event_date, post_event) {
		var get_image = function (coordinates, region) {
			var images = satellite.filterBounds(coordinates).filterDate(event_date, post_event);
			process_images(images, context, region, composite_case, landslide, description, image_collector);
		};
		process_region_and_coordinates(landslide, get_image);
	};
	//1 Get the event date from landlide event date history
	var process_event_date = function (landslide) {
		var event_date = ee.Date(landslide.get('event_date'));
		event_date.evaluate(function (ev_result) {
			process_post_event_date(ev_result);
		});
	};
	//2 Calculate the end of range after the landslide
	var process_post_event_date = function (end_date_result) {
		var start_event = ee.Date(end_date_result.value).advance(-1 * back_months_cloud_case, 'Month');
		start_event.evaluate(function (start_ev_result) {
			var start_date = ee.Date(start_ev_result.value);
			var end_date = ee.Date(end_date_result.value);
			process_event_time_range(start_date, end_date);
		});
	};
	process_event_date(landslide);
};

var process_composite_images = function (images, context, region, landslide, description, download_body) {
	print('Running Composite');
	//4 download the images
	var download = function () {
		print('Waiting to complete');
		if (download_body.retrieve_done()) {
			download_body.calculate_difference();
			download_images_to_drive(download_body.list_pre);
			download_images_to_drive(download_body.list_post);
		}
	};

	//2 After cleaning the images, add the bands
	var add_bands_callback = function (image_input) {

		// Compute NDVI from the NAIP imagery.
		var naipNDVI = image_input.normalizedDifference(['B8', 'B4']);
		var test = naipNDVI.reduceNeighborhood({  // Compute standard deviation (SD) as texture of the NDVI.
				reducer : ee.Reducer.stdDev(),
				kernel : ee.Kernel.circle(7),
			});
		//     // Display the results.
		Map.addLayer(test, {
			min : 0,
			max : 0.3
		}, 'SD of   NDVI', false);

		var imageRGB = image_input.visualize({
				bands : ['B5', 'B4', 'B3'],
				min : 0.0,
				max : 3000
			});
		// print ('imageRGB',imageRGB )


		//calculate ndvi
		var nir = image_input.select('B8');
		var red = image_input.select('B4');
		var blue = image_input.select('B2');
		var ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI');

		var green = image_input.select('B3');
		var gndvi = nir.subtract(green).divide(nir.add(green)).rename('GNDVI');

		//calculate brightness
		var brightness = (((red.add(green).add(blue)).divide(3)).divide(1000)).rename('brightness');

		//calculate slope and elevation from ALOS  and adapt projection to input image
		var imageProjection = ndvi.projection(); //get input imagery projection

		var slope_alos = ee.Terrain.slope(dem_alos).rename('slope');

			var dem_projected = dem_alos.reproject({
				crs : imageProjection
			});

		var slope_projected = slope_alos.reproject({
				crs : imageProjection
			});

		//merge the bands
		var image = image_input.float().select('B4', 'B3', 'B2', 'B8').addBands(ndvi.float().select('NDVI'))
			.addBands(slope_projected.float().select('slope'))
			.addBands(dem_projected.float().select('AVE').rename('elevation'))
			.addBands(test.float().select('nd_stdDev'))
			.addBands(imageRGB.float().select('vis-red', 'vis-green', 'vis-blue'))
			.addBands(gndvi.float().select('GNDVI'))
			.addBands(brightness.float().select('brightness'));

			append_to_download(image);
	};

	//3 Create download object with image, region and description
	var append_to_download = function (image) {
		var l_id = landslide.get('landslide_id');
		l_id.evaluate(function (l_id_result) {
			var download_image = create_download_image(l_id_result, image, region, description);
			if (context === 'pre') {
				download_body.list_pre.push(download_image);
			} else if (context === 'post') {
				download_body.list_post.push(download_image);
			} else {
				print('Error Context not found');
			}
			download();
		});
	};
	//1 Run the cloud algorithm to get a set of clean images
	composite_image(images, 50, add_bands_callback);
};

var process_images = function (images, context, region, composite_case, landslide, description, download_body) {
	//4 download the images
	var download = function () {
		print('Waiting to complete');
		if (download_body.retrieve_done()) {
			download_body.calculate_difference();
			download_images_to_drive(download_body.list_pre);
			download_images_to_drive(download_body.list_post);
		}
	};

	//2 After cleaning the images, add the bands
	var add_bands_callback = function (image_input) {
		//calculate image texture
		var image_texture = texture(image_input);
			// Compute NDVI from the NAIP imagery.
			var naipNDVI = image_input.normalizedDifference(['B8', 'B4']);
		var test = naipNDVI.reduceNeighborhood({ // Compute standard deviation (SD) as texture of the NDVI.
				reducer : ee.Reducer.stdDev(),
				kernel : ee.Kernel.circle(7),
			});

		//     // Display the results.
		Map.addLayer(test, {
			min : 0,
			max : 0.3
		}, 'SD of   NDVI', false);

		var imageRGB = image_input.visualize({
				bands : ['B5', 'B4', 'B3'],
				min : 0.0,
				max : 3000
			});

		//calculate ndvi
		var nir = image_input.select('B8');
		var red = image_input.select('B4');
		var blue = image_input.select('B2');
		var ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI');

		//calculate gndvi
		var green = image_input.select('B3');
		var gndvi = nir.subtract(green).divide(nir.add(green)).rename('GNDVI');
		var brightness = (((red.add(green).add(blue)).divide(3)).divide(1000)).rename('brightness');
		var imageProjection = ndvi.projection(); //get input imagery projection
		var slope_alos = ee.Terrain.slope(dem_alos).rename('slope');

			var dem_projected = dem_alos.reproject({
				crs : imageProjection
			});

		var slope_projected = slope_alos.reproject({
				crs : imageProjection
			});

		//merge the bands
		var image = image_input.float().select('B4', 'B3', 'B2', 'B8').addBands(ndvi.float().select('NDVI'))
			.addBands(slope_projected.float().select('slope'))
			.addBands(dem_projected.float().select('AVE').rename('elevation'))
			// .addBands(image_texture.float().select('B8_contrast'))
			.addBands(test.float().select('nd_stdDev'))
			.addBands(imageRGB.float().select('vis-red', 'vis-green', 'vis-blue'))
			// .addBands(hsv2.float().select('vis-red', 'vis-green', 'vis-blue'))
			.addBands(gndvi.float().select('GNDVI'))
			.addBands(brightness.float().select('brightness'));
			append_to_download(image);

	};
	//3 Create download object with image, region and description
	var append_to_download = function (image) {
		var l_id = landslide.get('landslide_id');
		l_id.evaluate(function (l_id_result) {
			var download_image = create_download_image(l_id_result, image, region, description);
			if (context === 'pre') {
				download_body.list_pre.push(download_image);
			} else if (context === 'post') {
				download_body.list_post.push(download_image);
			} else {
				print('Error Context not found');
			}
			download();
		});
	};
	//1 Run the cloud algorithm to get a set of clean images
	find_less_cloudy_image(images, 0, composite_case, add_bands_callback, context);
};

// The image collector acts as a sychronization objects that, gather all the images from pre-and-post processes in GEE servers, once all images are cleared from clouds triggers, 
// runs the image difference algorithm, when all images are ready download the result to Google Drive.
var create_image_collector = function (min_images) {
	return {
		min_images : min_images,
		list_pre : [],
		list_post : [],

		retrieve_done : function () {
			return this.min_images <= this.list_pre.length && this.min_images <= this.list_post.length;
		},

		calculate_difference : function () {
			var list_band_ratio_pre = [];
			var list_band_ratio_post = [];
			var image_difference = [];

			var difference_ready = function () {
				if (image_difference.length === min_images) {
					print(image_difference);
					for (var x = 0; x < image_difference.length; x++) {
						export_to_drive(image_difference[x].image, image_difference[x].region, image_difference[x].description);
					}
				}
			};

			var run_difference = function () {
				// Functions to Normalize NDVI and RGB
				var subtract_band = function (image_pre_a, image_post_a, ndvi_change, brightness, region, l_id) {
					var ratio_after = image_post_a.subtract(image_pre_a).add(0.50); //add 0.50 if ratio is no normalized
					ratio_after = ratio_after.float().select('rg').addBands(ndvi_change.float().select('ndvi_change'))
						.addBands(brightness.float().select('brightness_change'));
						var description = 'diff_landslide';
						var image_difference_download = create_download_image(l_id, ratio_after, region, description);
					image_difference.push(image_difference_download);
					difference_ready();
				};

				var calculate_mean = function (image, polygon) {

					var buffer_processed = ee.Feature(polygon);
						var stats_values = image.reduceRegion({
							reducer : ee.Reducer.mean(), // calculate max
							geometry : buffer_processed.geometry(),
							scale : 10000,
							maxPixels : 1e9,
						});
						var values = stats_values;
						return values;
				};

				var calculate_ndvi = function (b4, b8) {
					var nir = b8;
					var red = b4;
					return nir.subtract(red).divide(nir.add(red)).rename('NDVI');
				};

				var calculate_brightness = function (b2, b3, b4) {
					var red = b4;
					var green = b3;
					var blue = b2;
					return (((red.add(green).add(blue)).divide(3)).divide(1000)).rename('brightness');
				};

				var run_normalization = function (image_valData_after, image_valData_before, region, l_id) {
					print(image_valData_before);
					//1. calculate mean of all pixels per image
					var mean_red_bands_after = calculate_mean(image_valData_after.select('B4', 'B3', 'B2', 'B8'), region).get('B4');
					var mean_red_bands_before = calculate_mean(image_valData_before.select('B4', 'B3', 'B2', 'B8'), region).get('B4');

					var mean_green_bands_after = calculate_mean(image_valData_after.select('B4', 'B3', 'B2', 'B8'), region).get('B3');
					var mean_green_bands_before = calculate_mean(image_valData_before.select('B4', 'B3', 'B2', 'B8'), region).get('B3');

					var mean_nir_bands_after = calculate_mean(image_valData_after.select('B4', 'B3', 'B2', 'B8'), region).get('B8');
					var mean_nir_bands_before = calculate_mean(image_valData_before.select('B4', 'B3', 'B2', 'B8'), region).get('B8');

					var mean_blue_bands_after = calculate_mean(image_valData_after.select('B4', 'B3', 'B2', 'B8'), region).get('B2');
					var mean_blue_bands_before = calculate_mean(image_valData_before.select('B4', 'B3', 'B2', 'B8'), region).get('B2');

					//2. calculate normalization factor
					var normalisation_factor_red = ee.Number(mean_red_bands_after).divide(ee.Number(mean_red_bands_before));
					var normalisation_factor_green = ee.Number(mean_green_bands_after).divide(ee.Number(mean_green_bands_before));
					var normalisation_factor_blue = ee.Number(mean_blue_bands_after).divide(ee.Number(mean_blue_bands_before));
					var normalisation_factor_nir = ee.Number(mean_nir_bands_after).divide(ee.Number(mean_nir_bands_before));

					//3. Apply normalization factor to image pre-event
					var image_valData_before_b2 = image_valData_before.select('B2').multiply(ee.Number(normalisation_factor_blue));
					var image_valData_before_b3 = image_valData_before.select('B3').multiply(ee.Number(normalisation_factor_green));
					var image_valData_before_b4 = image_valData_before.select('B4').multiply(ee.Number(normalisation_factor_red));
					var image_valData_before_b8 = image_valData_before.select('B8').multiply(ee.Number(normalisation_factor_nir));

					//4. Calculate NDVI Difference
					var ndvi_image_post = calculate_ndvi(image_valData_after.select('B4'), image_valData_after.select('B8'));
					var ndvi_image_pre = calculate_ndvi(image_valData_before_b4, image_valData_before_b8);
					var ndvi_change = ndvi_image_pre.subtract(ndvi_image_post).rename('ndvi_change');
					var brightness_image_post = calculate_brightness(image_valData_after.select('B2'), image_valData_after.select('B3'), image_valData_after.select('B4'));
					var brightness_image_pre = calculate_brightness(image_valData_before_b2, image_valData_before_b3, image_valData_before_b4);
					var brightness_change = brightness_image_pre.subtract(brightness_image_post).rename('brightness_change');

					image_valData_before.evaluate(function (result) {
							var band_ratio_image_pre = image_valData_before.select('B4').divide(image_valData_before.select('B3')).rename('rg'); //ration no normalized
							var band_ratio_image_post = image_valData_after.select('B4').divide(image_valData_after.select('B3')).rename('rg');
							subtract_band(band_ratio_image_pre, band_ratio_image_post, ndvi_change, brightness_change, region, l_id);
						});
				};

				if (list_band_ratio_pre.length === min_images && list_band_ratio_post.length === min_images) {
					for (var x = 0; x < list_band_ratio_post.length; x++) {
						var image_band_ratio_post = list_band_ratio_post[x];
						for (var y = 0; y < list_band_ratio_pre.length; y++) {
							var image_band_ratio_pre = list_band_ratio_pre[y];
							var l_id = image_band_ratio_pre.id;
								if (image_band_ratio_post.id === l_id) {
									var region = list_band_ratio_pre[y].region;
										run_normalization(image_band_ratio_post.image, image_band_ratio_pre.image, region, l_id);

								}
						}
					}
				}
			};

			if (this.retrieve_done()) {
				for (var i = 0; i < this.list_pre.length; i++) {
					var description_pre = this.list_pre[i].description + 'band_ratio';
					var image_pre = this.list_pre[i].image;
					var region_pre = this.list_pre[i].region;
					var band_ratio_image_pre_download = create_download_image(this.list_pre[i].id, image_pre, region_pre, description_pre);
					list_band_ratio_pre.push(band_ratio_image_pre_download);
					run_difference();
					var description_post = this.list_post[i].description + 'band_ratio';
					var image_post = this.list_post[i].image;
					var region_post = this.list_post[i].region;
						var band_ratio_image_post_download = create_download_image(this.list_post[i].id, image_post, region_post, description_post);
					list_band_ratio_post.push(band_ratio_image_post_download);
					run_difference();
				}
			}

		}
	};
};

var landslides = ee.FeatureCollection(fusion_table_id, 'latitude'); 
process_landslides_images(sentinel2, landslides, free_cloud_month_range, composite_image_search_range, download_prefix_description);
