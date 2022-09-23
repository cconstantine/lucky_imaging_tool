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
    def __init__(self, star=100, thr=10):
        self.low = 0.0
        self.high = 500.0
        self.star=star
        self.thr=thr


    def binary_search(self, func, data, target, margin, background, kernel):
        low = self.low
        high = self.high

        while True:
            cur = (low + high) / 2.0

            a, result = func(data, cur, background, kernel)
            delta = target - a
            if abs(delta) <= margin:
                return result
            elif delta < 0:
                low = cur
            else:
                high = cur

            if high - low < 0.2:
                return None

    def search_func(self, data, threshold, bkg, kernel):
        objects = sep.extract(data, threshold, err=bkg.globalrms, filter_type="matched", filter_kernel=kernel)
        return len(objects), objects

    def fwhm(self, focal_length, pixel_size, data):
        # Representation of spatially variable image background and noise.
        bkg = sep.Background(data)

        # evaluate background as 2-d array, same size as original image
        bkg_image = bkg.back()

        # Get backround noise
        bkg_rms = bkg.rms()

        # Subtract the background from an existing array. Like data = data - bkg, but avoids making a copy of the data.
        bkg.subfrom(data)

        # Create a filter-kernal with the shape of a star (round point ;))
        kernel = np.array([[1., 2., 3., 2., 1.],
        [2., 3., 5., 3., 2.],
        [3., 5., 8., 5., 3.],
        [2., 3., 5., 3., 2.],
        [1., 2., 3., 2., 1.]])

        objects = self.binary_search(self.search_func, data, self.star, self.thr, bkg, kernel)
        if objects is None:
            return None

        # Required in calculating the radius of the circles
        kronrad, krflag = sep.kron_radius(data, objects["x"], objects["y"], objects["a"], objects["b"], objects["theta"], 6.0)

        # The following section removes any stars which are too small.
        # It will remove from objects if they are smaller then 1.75 px in diameter.
        r_min = 1.75  # minimum diameter = 3.5
        use_circle = kronrad * np.sqrt(objects["a"], objects["b"]) < r_min

        # Calculate the FWHMs of the stars:
        fwhm = 2.0 * (np.log(2) * (objects['a'] ** 2.0 + objects['b'] ** 2.0)) ** 0.5

        # Remove any larger than.
        fwhm = fwhm[fwhm < 30]

        # print(fwhm)
        # exit()
        arcsec_constant = 206.265
        pixel_scale = ((pixel_size / focal_length) * arcsec_constant)
        perfect_arcsec_per_px = 122 / focal_length
        image_scale = arcsec_constant * pixel_size / focal_length

        # Print a comparable string as test-my-scope
        mean, stdev = np.mean(fwhm), np.std(fwhm)
        final_fwhm = mean + stdev
        final_arcsec = (mean + stdev) * image_scale
        print("FWHM: {} px / {} arcsec".format(final_fwhm, final_arcsec))
        # exit()
        return objects, final_fwhm, final_arcsec

# Broken fix fwhm params
if __name__ == "__main__":
    calc = Calculator()
    path = os.path.join("test", "images")
    print("DSS,FWHM,filename")
    with open(os.path.join(path, "image_data.csv")) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # # print(row)
            # def timed():
            #   fwhms(os.path.join(path, row['filename']))
            # print(timeit.Timer(timed).timeit(number=1))

            # Open a file to use
            with fits.open(row['filename']) as fitsdata:
                result = calc.fwhm(os.path.join(path, fitsdata))
                # print(timeit.Timer())
                # temp=statistics.mean(results)+statistics.stdev(results)
                # result = (0.6188*temp) + 0.5301 if len(results) > 0 else 0.0
                print("{:2.5f},{:2.5f},{}".format(float(row['fwhm_pixels']), result, row['filename']))
