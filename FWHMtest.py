import sep
from astropy.io import fits
import numpy as np
from math import sqrt
import matplotlib.pyplot as plt
import statistics

# Openb a file to use
data=fits.open("2022-09-08_22-11-19_L-Extreme_-10.00_300.00s_1x1_0015.fits")

# Extract the image data from FITS as numpyarray.
data=data[0].data

# Convert to 32 bit integer
data=np.array(data,dtype='int')

# Representation of spatially variable image background and noise.
bkg = sep.Background(data)

# Subtract the background from an existing array. Like data = data - bkg, but avoids making a copy of the data.
bkg.subfrom(data)

objects = sep.extract(data_sub, 25, err=bkg.globalrms)
print(len(objects))
FWHM=[]
#2*sqrt((ln(2)))
count=[]
for i in range(len(objects)):
    thing=(float(objects['a'][i])**2) + (float(objects['b'][i])**2)
    FWHM.append(2 * (sqrt((np.log(2)) * thing)))
print(statistics.median(FWHM))
for i in range(len(FWHM)):
    count.append(i)
plt.scatter(count,FWHM)
plt.show()
