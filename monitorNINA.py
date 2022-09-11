import psutil
import os
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.io import fits
import numpy as np
import time
from datetime import datetime, timedelta
# from . import crop
from crop import crop
import common


def main():
    perW, perH, path, FWHMthresh, del_uncrop, cropped_folder, moved_orignals_folder = common.init()

    print("Monitoring ", os.path.abspath(path)) #Just an indicator that monitoring is active
    while(True):#monitors if NINA is open
        print("Monitoring filepath...") #Just an indicator that monitoring is active
        for file in common.get_fits_from_folder(path):
            common.handle_file(file, cropped_folder, moved_orignals_folder, del_uncrop, FWHMthresh, perW, perH)

        time.sleep(1)

if __name__ == "__main__":
    main()
