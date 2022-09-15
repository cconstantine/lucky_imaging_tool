import psutil
import glob,os
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.io import fits
import numpy as np
import time
import common

def main():
    data = common.init()

    os.chdir(data["path"])

    while(True):#monitors if NINA is open
        time.sleep(0.1)
        print("NINA status, true if open, false if closed")
        print("NINA.exe running: {}".format("NINA.exe" in (i.name() for i in psutil.process_iter())))#prints true if nina is open, false if not
        while("NINA.exe" in (i.name() for i in psutil.process_iter())): #Activates monitoring while nina is open
            print("Monitoring filepath...") #Just an indicator that monitoring is active
            for file in common.get_fits_from_folder(data["path"]):
                if(common.fwhm_from_filename(file) > data["FWHMthresh"]): #Checks of the front part of the file before word "pixels" is above the indicated threshold
                    print("High HFR/FWHM detected, deleted {}".format(file))  #Indicates file being deleted
                    os.remove(file)   #Removes the offending file
                else:
                    if(perW!=1 and perH!=1):
                        with fits.open(row['filename']) as fitsdata:
                            common.handle_file(file, data["cropped_folder"], data["moved_orignals_folder"], data["del_uncrop"], data["FWHMthresh"], data["perW"], data["perH"])

            time.sleep(1)

if __name__ == "__main__":
    main()
