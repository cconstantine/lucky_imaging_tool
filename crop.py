import glob,os
import cv2
import math
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.io import fits
import pyfits
import numpy as np

path="H:\MyWorkPythonAll"
newpath=path+"\\"+"CroppedGoodImages"
os.chdir(path)
if not os.path.exists(newpath):
    os.makedirs(newpath)
for file in glob.glob("*.fits"):
    img=fits.open(file)
    img_data=img[0].data
    width,height=img_data.shape
    position=(width//2,height//2)
    size=(int(width*1)+height//2,int(height*1)+height//2)
    print(position,size,img_data)
    cutout=Cutout2D(img_data,position,size)
    print(cutout.data)
    file2=file
    file2=file2.split(".fits")
    file2[0]=file2[0]+"goodimg"
    file2=file2[0]+".fits"
    os.chdir(newpath)
    fits.writeto(file2,cutout.data,overwrite=True)
    os.chdir(path)
