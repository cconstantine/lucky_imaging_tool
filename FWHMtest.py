# import sep
# from astropy.io import fits
# import numpy as np
# from math import sqrt
import matplotlib.pyplot as plt
import statistics
from fwhm import Calculator

# fib_n1 = None
# fib_n2 = None
# def get_next_fibinacci(n1 = None, n2 = None ):
#     global fib_n1
#     global fib_n2

#     # Overrule globals with arguments if set
#     if n1 != None and n2 != None:
#         fib_n1 = n1
#         fib_n2 = n2

#     if fib_n1 == None or fib_n2 == None:
#         fib_n1 = 0
#         fib_n2 = 1
#     else:
#         tmp = fib_n1 + fib_n2
#         fib_n1 = fib_n2
#         fib_n2 = tmp

#     return fib_n1, fib_n2

# # Currently 100 objects detected seems to be desired for the best results.
# def determine_detection_threshold(data, background_rms_error):
#     TARGET = 100
#     objects_detected = None
#     detection_threshold = None

#     THRESHOLD_UPPER_LIMIT = 377 # A numebr this high does not make sense.

#     print("Determine threshold for detecting as close to {} objects as possible".format(TARGET))
#     while detection_threshold == None or detection_threshold < THRESHOLD_UPPER_LIMIT:
#         # Placeholder for the current threshold to be tested.
#         tmp_threshold = None

#         # The first iteration will have no results yet.
#         if objects_detected == None:
#             '''Prime sequence to start with 3.
#             If the threshold is lower we get way to many objects
#             with a good image and this will take very long on the cpu.'''
#             tmp_threshold, _ = get_next_fibinacci(2, 3)
#         else:
#             # Get next threshold in sequence.
#             tmp_threshold, _ = get_next_fibinacci()

#         # Detect how many objects are in the image.
#         nr_objects = len(extract_objects(data, tmp_threshold, background_rms_error))
#         print("Found {} objects with threshold {}".format(nr_objects, tmp_threshold))
        
#         # Check if we have reaced our TARGET
#         if nr_objects < TARGET:
#             # Stop iterating with increasing detection thresholds.
#             if objects_detected == None:
#                 # First iteration already yields < TARGET objects.
#                 # TODO: perhaps throw an error when this is true as this is likely the result of bad image.
#                 objects_detected = nr_objects
#                 detection_threshold = tmp_threshold
#             else:
#                 # Check which threshold is closer to out target.
#                 # Previous pass deviation will be >= TARGET
#                 prev_deviation = objects_detected - TARGET

#                 # current deviation will be <= TARGET
#                 curr_deviation = TARGET - nr_objects

#                 # If the current (higher threshold) yields better 
#                 # results, use this. A higher threshold is faster.
#                 if curr_deviation <= prev_deviation:
#                     # Update values to be retured from function.
#                     objects_detected = nr_objects
#                     detection_threshold = tmp_threshold

#             # End of while loop.
#             break
#         else:
#             # Remember how many were detected with the threshold.
#             objects_detected = nr_objects
#             detection_threshold = tmp_threshold

#     print("Returning detection threshold {}".format(detection_threshold))
#     return detection_threshold, objects_detected

# def extract_objects(data, detection_threshold, background_rms_error):
#     return sep.extract(data, detection_threshold, err=background_rms_error)

# # Openb a file to use
# f_data=fits.open("2022-09-08_22-11-19_L-Extreme_-10.00_300.00s_1x1_0015.fits")

# # Get reference to image data from FITS as numpyarray.
# data=f_data[0].data

# # Convert to 32 bit integer
# data=np.array(data,dtype='int')

# # Representation of spatially variable image background and noise.
# bkg = sep.Background(data)

# # Subtract the background from an existing array. Like data = data - bkg, but avoids making a copy of the data.
# bkg.subfrom(data)

# # Determine correct detection_threshold. (A bad image might lead to bad results, a good image is required)
# detection_threshold, objects_detected = determine_detection_threshold(data, bkg.globalrms);

# # Run object detection on the background-subtracted data.
# objects = extract_objects(data, detection_threshold, bkg.globalrms)

# # Close fits image as we no longer need it.
# f_data.close()

# # print(objects)
# print("Amount of objects found: {}".format(len(objects)))

#### Determine FWHM ####
calc = Calculator()

# Open a file to use
with fits.open("2022-09-08_22-11-19_L-Extreme_-10.00_300.00s_1x1_0015.fits") as fitsdata:
	FWHM=calc.fwhms(fitsdata)

#2*sqrt((ln(2)))
count=[]

#print(statistics.mean(FWHM)+statistics.stdev(FWHM))
print(FWHM)

#for i in range(len(FWHM)):
#   count.append(i)
#plt.scatter(count,FWHM)
#plt.show()
