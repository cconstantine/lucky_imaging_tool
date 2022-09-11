import psutil
import glob,os
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.io import fits
import numpy as np
import time
from datetime import datetime, timedelta
# from . import crop
from crop import crop

def fwhm_from_filename(filename):
    return float(os.path.basename(filename).split("pixels")[0])

def handle_file(file, newpath, del_uncrop, FWHMthresh, perW, perH):
    if(fwhm_from_filename(file)>FWHMthresh):#Checks of the front part of the file before word "pixels" is above the indicated threshold
        if (del_uncrop[0]=="y"):
            print("High HFR/FWHM detected, deleted ",file)  #Indicates file being deleted
            os.remove(file)   #Removes the offending file
    else:
        file2 = os.path.join(newpath, os.path.basename(file))
        if(perW!=1 and perH!=1):
            timcr=os.path.getmtime(file)
            timenow=time.time()
            delta=abs(timcr-timenow)
            if(delta>15):
                crop(file, file2, perW, perH)
                if (del_uncrop[0]=="y"):
                    print("Image cropped, original deleted ",file)  #Indicates file being deleted
                    os.remove(file)
                else:
                    os.rename(file, file2)
def main():
    print("This script will automatically delete image files if they exceed a certain full width half maximum")
    print("It runs as long as nina is open, and stops monitoring once NINA is closed")
    print("In NINA under options, find image file pattern.  Add '\$$FWHM$$pixels' at the start of the filename")
    print("If the filename does not include 'pixels', the program will throw an error about converting string to float")
    print("For example, $$TARGETNAME$$\$$DATEMINUS12$$\$$IMAGETYPE$$\$$FILTER$$\$$EXPOSURETIME$$\$$FWHM$$pixels_$$DATETIME$$_$$FILTER$$_$$EXPOSURETIME$$s_$$FRAMENR$$")
    print("This uses Hocus Focus for FWHM calculation, if not using this plug in then $$HFR$$pixels can be used instead based on half-flux radius")
    print("This is set up for fits files only")
    perW=float(input("Fraction of the width to keep (0 - 1, where 0 crops all, 1 keeps full image), ex: 70%=0.7: "))
    perH=float(input("Fraction of the height to keep (0 - 1, where 0 crops all, 1 keeps full image),, ex: 70%=0.7: "))
    path=input("Enter Filepath for monitoring images (e.g. C:\Astrophotography\M31 ): ")
    print("Next select the FWHM or half-flux radius over which images will be deleted")
    print("Note that this is not the FWHM in arc seconds, but in pixels")
    print("To convert, take the intended maximum FWHM in arc seconds, and multiply by the focal length (mm) and divide by the pixel size (um) times 206.25")
    print("e.g. 3.0 arcsecs threshold*1200mm/3.75um/206.25 yields a threshold FWHM in pixels of 4.8 pixels")
    print("HFR is correlated to FWHM but doesn't have a direct conversion.  To use assess the variability of values and select an appropriate threshold")
    FWHMthresh=float(input("Rejection threshold (FWHM in pixels, or HFR in pixels) above which to delete files: "))
    del_uncrop=str(input("Delete original uncropped images (Y/N):"))
    del_uncrop=del_uncrop.lower()
    print("Monitoring ", os.path.abspath(path)) #Just an indicator that monitoring is active

    newpath=os.path.join(path, "CroppedGoodImages")
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    while(True):#monitors if NINA is open
        time.sleep(0.1)
        for file in glob.glob(os.path.join(path,"*.fits")):
            handle_file(file, newpath, del_uncrop, FWHMthresh, perW, perH)



if __name__ == "__main__":
    main()
