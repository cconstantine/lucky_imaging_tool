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

def backup_or_remove_file(context, result):
    if (result["processed"] == False) or (result["valid_fits_file"] == False):
        print("Unable to process file: {}. Please submit an error on https://github.com/cconstantine/lucky_imaging_tool/issues. Share the image.".format(result["fits_filepath"]))
        common.backup_file(result["fits_filepath"], context["moved_unsupported_folder"])
    elif result["rejected"]:
        common.backup_file(result["fits_filepath"], context["moved_rejects_folder"])
    elif result["cropped"] and context["delete_uncropped_original"]:
        os.remove(result["fits_filepath"])
    else:
        common.backup_file(result["fits_filepath"], context["moved_rejects_folder"])

# Called before pool._cache is empty
def callback(*args):
    try:
        context = args[0][0]
        processing_result = args[0][1]

        backup_or_remove_file(context, processing_result)
    except Exception as e:
        traceback.print_exc()
        pass

def main(argv):
    global exit_program

    freeze_support()

    context = common.init()

    monitoring_folder = os.path.abspath(context["monitoring_folder"])
    with Pool(processes=cpu_count()) as pool:
        print("Monitoring filepath {}".format(monitoring_folder))

        while(exit_program == False): #Until SIGINT is received keep monitoring.
            for file in common.get_fits_from_folder(context["monitoring_folder"]):
                print(file)
                pool.apply_async(common.process_fits_image, (file, context), callback=callback)

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

