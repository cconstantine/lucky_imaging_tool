import sep
from astropy.io import fits
import numpy as np
from math import sqrt
import matplotlib.pyplot as plt
import statistics
import glob
import os
import csv
import timeit


class Calculator:
	def __init__(self):
		self.low = 0.0
		self.high = 500.0


	def binary_search(self, func, target, margin):
		low = self.low
		high = self.high

		while True:
			cur = (low + high) / 2.0

			a, result = func(cur)
			delta = target - a
			if abs(delta) <= margin:
				return result
			elif delta < 0:
				low = cur
			else:
				high = cur

			if high - low < 0.2:
				return None


	def fwhms(self, filename):
		# Open a file to use
		f_data=fits.open(filename)

		# Get reference to image data from FITS as numpyarray.
		data=f_data[0].data

		# Convert to 32 bit integer
		data=np.array(data,dtype='int32')

		# Representation of spatially variable image background and noise.
		bkg = sep.Background(data)

		# Subtract the background from an existing array. Like data = data - bkg, but avoids making a copy of the data.
		bkg.subfrom(data)

		def search_func(threshold):
			objects = sep.extract(data, threshold, err=bkg.globalrms)
			return len(objects), objects

		objects = self.binary_search(search_func, 100, 10)
		if objects is None:
			return []

		# Close fits image as we no longer need it.
		f_data.close()

		#### Determine FWHMs ####
		results=[]

		for i in range(len(objects)):
			thing=(float(objects['a'][i])**2) + (float(objects['b'][i])**2)
			results.append(2 * (sqrt((np.log(2)) * thing)))

		return results

	def fwhm(self, filename):
		f = self.fwhms(filename)
		return statistics.mean(f)+statistics.stdev(f)


if __name__ == "__main__":
	path = os.path.join("test", "images")
	print("DSS,FWHM,filename")
	with open(os.path.join(path, "image_data.csv")) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			# # print(row)
			# def timed():
			# 	fwhms(os.path.join(path, row['filename']))
			# print(timeit.Timer(timed).timeit(number=1))

			results = fwhms(os.path.join(path, row['filename']))
			# print(timeit.Timer())
			temp=statistics.mean(results)+statistics.stdev(results)
			result = (0.6188*temp) + 0.5301 if len(results) > 0 else 0.0
			print("{:2.5f},{:2.5f},{}".format(float(row['fwhm_pixels']), result, row['filename']))
