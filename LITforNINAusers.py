import psutil
import glob,os
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.io import fits
import numpy as np
import time
import common

def main():
    perW, perH, path, FWHMthresh, del_uncrop, cropped_folder, moved_orignals_folder = common.init()

    os.chdir(path)

    while(True):#monitors if NINA is open
        time.sleep(0.1)
        print("NINA status, true if open, false if closed")
        print("NINA.exe running: {}".format("NINA.exe" in (i.name() for i in psutil.process_iter())))#prints true if nina is open, false if not
        while("NINA.exe" in (i.name() for i in psutil.process_iter())): #Activates monitoring while nina is open
            print("Monitoring filepath...") #Just an indicator that monitoring is active
            for file in common.get_fits_from_folder(path):
                if(common.fwhm_from_filename(file) > FWHMthresh): #Checks of the front part of the file before word "pixels" is above the indicated threshold
                    print("High HFR/FWHM detected, deleted {}".format(file))  #Indicates file being deleted
                    os.remove(file)   #Removes the offending file
                else:
                    if(perW!=1 and perH!=1):
                        common.handle_file(file, cropped_folder, moved_orignals_folder, del_uncrop, FWHMthresh, perW, perH)

            time.sleep(1)

if __name__ == "__main__":
    main()
