import glob,os
import cv2
import math
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.io import fits
import pyfits
import numpy as np
from PIL import Image
path="H:\MyWorkPythonAll"
newpath=path+"\\"+"CroppedGoodImages"
perH=0.7
perW=0.7
os.chdir(path)
if not os.path.exists(newpath):
    os.makedirs(newpath)
for file in glob.glob("*.fits"):
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
