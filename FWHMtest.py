import sep
from astropy.io import fits
import numpy as np
from math import sqrt
import matplotlib.pyplot as plt
import statistics
data=fits.open("2022-09-08_22-11-19_L-Extreme_-10.00_300.00s_1x1_0015.fits")
data=data[0].data
data=np.array(data,dtype='float64')
bkg = sep.Background(data)
data_sub=data-bkg
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
