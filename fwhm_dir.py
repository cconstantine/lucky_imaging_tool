#!/usr/bin/env python

import argparse
import common
import fwhm
import timeit
import sys


parser = argparse.ArgumentParser(description='Calculate fwhm of a directory of images')
parser.add_argument('directory', metavar='directory', type=str)

args = parser.parse_args()

fwhm_calc = fwhm.Calculator()

for filename in common.get_fits_from_folder(args.directory):
	def do_it():
		sys.stdout.write("{:2.5f}: ".format(fwhm_calc.fwhm(filename)))
	print("{:2.3f}".format(timeit.Timer(do_it).timeit(number=1)))