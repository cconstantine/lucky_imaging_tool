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
from multiprocessing import Pool, cpu_count, freeze_support
import signal
import sys
import traceback

exit_program = False
def handler(signum, frame):
    global exit_program
    if exit_program == False:
        exit_program = True

signal.signal(signal.SIGINT, handler)

def backup_or_remove_file(original, fwhm_above_threshold, do_crop, del_uncrop, moved_orignals_folder, is_fits_file):
    # Remove files where fwhm is too high or if user has specified the original to be deleted after cropping
    if is_fits_file and (fwhm_above_threshold or (do_crop and (del_uncrop[0] == 'y'))):
        print("Removed file {}".format(original))
        os.remove(original)
    else:
        #Backup original uncropped file or files which are not a fits file.
        print("Moved file {} to {}".format(original, moved_orignals_folder))
        common.backup_file(original, moved_orignals_folder)

# Called before pool._cache is empty
def callback(*args):
    try:
        result, original, fwhm_above_threshold, do_crop, del_uncrop, moved_orignals_folder, is_fits_file = args[0]
        backup_or_remove_file(original, fwhm_above_threshold, do_crop, del_uncrop, moved_orignals_folder, is_fits_file)
    except Exception as e:
        print("Failed to handle file {}, Going to move it".format(original))
        backup_or_remove_file(original, False, False, 'n', moved_orignals_folder, False)
        # traceback.print_exc()
        pass

def main(argv):
    global exit_program

    freeze_support()

    context = common.init()

    monitoring_path = os.path.abspath(context["path"])
    with Pool(processes=cpu_count()) as pool:
        print("Monitoring filepath {}".format(monitoring_path))

        while(exit_program == False):#monitors if NINA is open
            for file in common.get_fits_from_folder(context["path"]):
                pool.apply_async(common.handle_file,
                                (file,
                                 context["cropped_folder"],
                                 context["moved_originals_folder"],
                                 context["del_uncrop"],
                                 context["FWHMthresh"],
                                 context["perW"],
                                 context["perH"],
                                 context["numStar"],
                                 context["pixelSize"],
                                 context["fl"]),
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
    print("Starting {}".format(sys.argv[0]))
    main(sys.argv[1:])

