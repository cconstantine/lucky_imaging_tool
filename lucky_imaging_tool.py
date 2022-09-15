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
from multiprocessing import Pool, cpu_count
import tqdm
import signal

exit_program = False
def handler(signum, frame):
    global exit_program

    if exit_program == False:
        exit_program = True

signal.signal(signal.SIGINT, handler)

def backup_or_remove_file(original, fwhm_above_threshold, do_crop, del_uncrop, moved_orignals_folder):
    # Remove files where fwhm is too high or if user has specified the original to be deleted after cropping
    if fwhm_above_threshold or (do_crop and (del_uncrop[0] == 'y')):
        os.remove(original)
    else:
        #Backup original uncropped file.
        common.backup_file(original, moved_orignals_folder)

# Called before pool._cache is empty
def callback(*args):
    original, fwhm_above_threshold, do_crop, del_uncrop, moved_orignals_folder = args[0]
    backup_or_remove_file(original, fwhm_above_threshold, do_crop, del_uncrop, moved_orignals_folder)


def main():
    global exit_program

    data = common.init()
    monitoring_path = os.path.abspath(data["path"])
    with Pool(processes=cpu_count()) as pool:
        print("Monitoring filepath {}".format(monitoring_path))

        while(exit_program == False):#monitors if NINA is open
            for file in common.get_fits_from_folder(data["path"]):
                pool.apply_async(common.handle_file,
                                (file,
                                 data["cropped_folder"],
                                 data["moved_originals_folder"],
                                 data["del_uncrop"],
                                 data["FWHMthresh"],
                                 data["perW"],
                                 data["perH"]),
                                callback=callback)

            # Wait for tasks to complete before running new batch.
            while len(pool._cache) > 0:
                print("number of jobs pending: ", len(pool._cache))
                time.sleep(1)

            # Sleep some time between work
            time.sleep(1)

        print("Stopping processes")
        # Wait for pool to finish
        pool.close()
        pool.join()

if __name__ == "__main__":
    main()
