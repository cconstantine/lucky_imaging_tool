import psutil
import glob,os
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.io import fits
import numpy as np
import time

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
os.chdir(path)
newpath=path+"\\"+"CroppedGoodImages"
if not os.path.exists(newpath):
    os.makedirs(newpath)
while(True):#monitors if NINA is open
    time.sleep(0.1)
    print("NINA status, true if open, false if closed")
    print("NINA.exe" in (i.name() for i in psutil.process_iter()))#prints true if nina is open, false if not
    while("NINA.exe" in (i.name() for i in psutil.process_iter())): #Activates monitoring while nina is open
        print("Monitoring filepath...") #Just an indicator that monitoring is active
        for file in glob.glob("*.fits"):
            if(float(file.split("pixels")[0])>FWHMthresh):#Checks of the front part of the file before word "pixels" is above the indicated threshold
                print("High HFR/FWHM detected, deleted ",file)  #Indicates file being deleted
                os.remove(file)   #Removes the offending file
            else:
                if(perW!=1 and perH!=1):
                    #This would be more efficient if it didn't keep cropping already cropped files.
                    time.sleep(3)
                    img=fits.open(file)
                    header=img[0].header
                    img_data=img[0].data
                    height,width=img_data.shape
                    position=(width//2,height//2)
                    #size=(int(width*perW)+height//2,int(height*perH)+height//2)
                    size=(int(height*perH),int(width*perW))
                    print("Cropping ", file)
                    cutout=Cutout2D(img_data,position,size)
                    #print(cutout.data)
                    file2=file
                    img.close() #release the file so we can delete it
                    file2=file2.split(".fits")
                    file2[0]=file2[0]+"goodimg"
                    file2=file2[0]+".fits"
                    os.chdir(newpath)
                    fits.writeto(file2,cutout.data,header,overwrite=True)
                    os.chdir(path)
                    if (del_uncrop[0]=="y"):
                        print("Image cropped, original deleted ",file)  #Indicates file being deleted
                        os.remove(file)
