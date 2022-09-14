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

def main():
    global exit_program

    data = common.init()
    monitoring_path = os.path.abspath(data["path"])
    with Pool(processes=cpu_count()) as pool:
        print("Monitoring ", monitoring_path) #Just an indicator that monitoring is active

        while(exit_program == False):#monitors if NINA is open
            print("Monitoring filepath {}".format(monitoring_path)) #Just an indicator that monitoring is active
            for file in common.get_fits_from_folder(data["path"]):
                pool.apply_async(common.handle_file,
                                (file, data["cropped_folder"],
                                 data["moved_originals_folder"],
                                 data["del_uncrop"],
                                 data["FWHMthresh"],
                                 data["perW"],
                                 data["perH"]))

            time.sleep(1)

        print("Stopping processes")
        # Wait for pool to finish
        pool.close()
        pool.join()

if __name__ == "__main__":
    main()
