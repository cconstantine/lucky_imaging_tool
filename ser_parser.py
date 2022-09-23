import common
from astropy.io import fits
import numpy as np
import sep
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.patches import Circle
from math import sqrt, log
from matplotlib.lines import Line2D
import cv
import glob
import os
import shutil

def get_stars_from_data(focal_length, pixel_size, data, threshold):

    # Plot raw image data
    # m, s = np.mean(data), np.std(data)
    # org_plt = plt.figure("Raw data")
    # plt.imshow(data, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    # plt.colorbar();

    # Representation of spatially variable image background and noise.
    bkg = sep.Background(data)

    # evaluate background as 2-d array, same size as original image
    bkg_image = bkg.back()
    # Plot background data
    # m, s = np.mean(bkg_image), np.std(bkg_image)
    # bkg_plot = plt.figure("Background data")
    # plt.imshow(bkg_image, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    # plt.colorbar();

    # Get backround noise
    # Plot background data
    bkg_rms = bkg.rms()
    # m, s = np.mean(bkg_rms), np.std(bkg_rms)
    # bkg_plot = plt.figure("Background RMS data")
    # plt.imshow(bkg_rms, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    # plt.colorbar();


    # Subtract the background from an existing array. Like data = data - bkg, but avoids making a copy of the data.
    bkg.subfrom(data)

    # Plot background subtracketed data
    # m, s = np.mean(data), np.std(data)
    # bkg_sub_plot = plt.figure("Background subtrackted data")
    # plt.imshow(data, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    # plt.colorbar();

    # Create a filter-kernal with the shape of a star (round point ;))
    kernel = np.array([[1., 2., 3., 2., 1.],
    [2., 3., 5., 3., 2.],
    [3., 5., 8., 5., 3.],
    [2., 3., 5., 3., 2.],
    [1., 2., 3., 2., 1.]])
    objects = sep.extract(data, threshold, err=bkg.globalrms, filter_type="matched", filter_kernel=kernel)

    # Required in calculating the radius of the circles
    kronrad, krflag = sep.kron_radius(data, objects["x"], objects["y"], objects["a"], objects["b"], objects["theta"], 6.0)
    # flux, fluxerr, flag = sep.sum_ellipse(data, objects["x"], objects["y"], objects["a"], objects["b"], objects["theta"], 2.5*kronrad,
    #                                       subpix=1)
    # flag |= krflag  # combine flags into 'flag'        


    # The following section removes any stars which are too small.
    # It will remove from objects if they are smaller then 1.75 px in diameter.
    r_min = 1.75  # minimum diameter = 3.5
    use_circle = kronrad * np.sqrt(objects["a"], objects["b"]) < r_min

    # cflux, cfluxerr, cflag = sep.sum_circle(data, objects["x"][use_circle], objects["y"][use_circle],
    #                                         r_min, subpix=1)

    # flux[use_circle] = cflux
    # fluxerr[use_circle] = cfluxerr
    # flag[use_circle] = cflag

    # r_half, r_half_flag = sep.flux_radius(data, objects['x'], objects['y'], 6.*objects['a'], 0.5,
    #                           normflux=flux, subpix=5)
    # r_full, r_full_flag = sep.flux_radius(data, objects['x'], objects['y'], 6.*objects['a'], 1.0,
    #                           normflux=flux, subpix=5)

    # Calculate the FWHMs of the stars:
    fwhm = 2.0 * (np.log(2) * (objects['a'] ** 2.0 + objects['b'] ** 2.0)) ** 0.5

    # Remove any larger than.
    fwhm = fwhm[fwhm < 30]

    # print(fwhm)
    # exit()
    arcsec_constant = 206.265
    # pixel_size = 4.63
    # reducer = 1.0
    # focal_length = 1000 * reducer
    pixel_scale = ((pixel_size / focal_length) * arcsec_constant)
    perfect_arcsec_per_px = 122 / focal_length
    image_scale = arcsec_constant * pixel_size / focal_length

    # sigma = np.median(fwhm/(2*sqrt(2*log(2))))
    # r_full_sigma = np.median(r_full/(2*sqrt(2*log(2))))

    # Print a comparable string as test-my-scope
    mean, stdev = np.mean(fwhm), np.std(fwhm)
    final_fwhm = mean + stdev
    final_arcsec = (mean + stdev) * image_scale
    print("FWHM: {} px / {} arcsec".format(final_fwhm, final_arcsec))
    # exit()
    return objects, final_fwhm, final_arcsec


# image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\3.99arcsec_0.27eccs_2022-09-18_22-56-26_B5.00s_0208.fits"
# test-my-scope gives: FWHM: 4.09 px / 15.12 arcsec
# Our script:          FWHM: 4.32420311845506 px / 2.3176664847393083 arcsec (This is better, it ignores that galaxy and core.)
# threshold = 18
def test_image1():
    image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\2022-09-19_01-20-40__7.30_0.75s_0000.fits"
    header_inserts = []
    threshold = 18
    return threshold, image, header_inserts

# test-my-scope gives: FWHM: 3.89 px / 2.08 arcsec
# Our script:          FWHM: 4.269569240676068 px / 2.2883840703866376 arcsec
def test_image2():
    image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\2022-09-19_01-20-40__7.30_0.75s_0000.fits"
    header_inserts = []
    threshold = 14
    return threshold, image, header_inserts

# test-my-scope gives: FWHM: 3.34 px / 3.2 arcsec 
# Our script:          FWHM: 3.114770601218944 px / 2.9746275718197697 arcsec
def test_image3():
    image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\0000_300.00s_2x2_2.18.fits"
    header_inserts = []
    threshold = 153
    return threshold, image, header_inserts

# test-my-scope gives: FWHM: 3.5 px / 5.57 arcsec
# Our script:          FWHM: 3.476923764191491 px / 5.534143932371725 arcsec
def test_image4():
    image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\Light_hdf_2sec_Bin1_-14.8C_gain390_2022-08-28_012338_frame0053.fit"
    header_inserts = [("FOCALLEN", 600)]
    threshold = 12
    return threshold, image, header_inserts

# discord: https://discord.com/channels/794642864218439681/863299203848994837/1020211156729737236
# test-my-scope gives: FWHM: 4.09 px / 15.12 arcsec
# Our script:          FWHM: 4.468815291357455 px / 2.8247489573169453 arcsec
def test_image5():
    image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\3.99arcsec_0.27eccs_2022-09-18_22-56-26_B5.00s_0208.fits"
    header_inserts = []
    threshold = 18
    return threshold, image, header_inserts

# discord: https://discord.com/channels/794642864218439681/1020211156729737236
# test-my-scope gives: FWHM: 3.73 px / 1.07 arcsec
# Manual:              FWHM  6.84 px / 1.958801564
# Our script:          FWHM: 6.26995799093193 px / 1.7955560697838449 arcsec
def test_image6():
    image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\2022-07-19-2344_1-L-DSO_pipp_f0001.fit"
    header_inserts = []
    threshold = 8
    return threshold, image, header_inserts

# threshold, image, header_inserts = test_image3()

path="C:\\Users\\Thomas\\Downloads\\MrCrazyPhys\\tiffs\\pipp_20220921_113856\\2022-07-19-2344_1-L-DSO_pipp"
images = glob.glob(os.path.join(path,"*.fit*"))
print("Found {} images".format(len(images)))
exit
threshold = 6 # TODO: test for CrazyMr
header_inserts = [("FOCALLEN", 2737), ("XPIXSZ", 3.8), ("YPIXSZ", 3.8)]

# fwhms = [3.0, 1.0, 1.5, 2.0, 1.0]
# arcsecs = [0.30, 0.10, 0.15, 0.20, 0.10]
fwhms = []
arcsecs = []

with open("{}/{}".format(path, "calculate_fwhm_arcsec.log"), 'w+') as log_f:
    for image in images:
        # image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\2022-07-19-2344_1-L-DSO_pipp_f0001.fit"
        with fits.open(image) as f:
            data = f[0].data
            header = f[0].header

            # Insert header missing info.
            for key, val in header_inserts:
                header[key] = val

            focal_length = header["FOCALLEN"]
            pixel_size = header["XPIXSZ"]

            if header["XPIXSZ"] != header["YPIXSZ"]:
                print("No support for non-rectangular pixel sizes yet")
                exit()

            if focal_length <= 0:
                print("Invalid focal_length {}".format(focal_length))

            if pixel_size <= 0:
                print("Invalid pixel_size {}".format(pixel_size))

            # print(focal_length)
            # print(pixel_size)

            try:
                bayer_pattern = header["BAYERPAT"]
                print("bayer_pattern is {}".format(bayer_pattern))

                debayered_image = cv2.cvtColor(data, cv2.COLOR_BayerRG2BGR)
                data = cv2.normalize(debayered_image, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_16U)

            except Exception as e:
                bayer_pattern = None

            # Convert to 32 bit integer
            data=np.array(data,dtype='int32')

            objects, final_fwhm, final_arcsec = get_stars_from_data(focal_length, pixel_size, data, threshold)
            fwhms.append(final_fwhm)
            arcsecs.append(final_arcsec)

            if (final_arcsec <= 1.7):
                new = os.path.join(path,"to_stack_{}.fit".format(os.path.basename(image)))
                print("added {}".format(new))
                shutil.copy(image, new)

            log_entry = "{}\n\tfwhm_px: {}\n\tfwhm_arcsec: {}\n\n".format(image, final_fwhm, final_arcsec)
            log_f.write(log_entry)

fig = plt.figure()
fig.suptitle("BIG PLOT")

fig.canvas.set_window_title('MrCrazyPhys data')

ax0 = plt.subplot(211)
ax1 = plt.subplot(212)
# ax2 = plt.subplot(413)
# ax3 = plt.subplot(414)

ax0.set(xlabel='Frame index', ylabel='FWHM arcsec')
ax1.set(xlabel='FWHM arcsec', ylabel='Total frames')
# ax2.set(xlabel='Frame index', ylabel='FWHM px')
# ax3.set(xlabel='FWHM px', ylabel='Total frames')

## Add the background subtrackted data.
m, s = np.mean(arcsecs), np.std(arcsecs)
im = ax0.plot(arcsecs, 'tab:orange')
im = ax1.hist(arcsecs, bins=200, color="orange")
# im = ax2.plot(fwhms, 'tab:blue')
# im = ax3.hist(fwhms, bins=200, color="blue")

# legend_elements = [ Line2D([0], [0], color='orange', lw=4, label='FWHM in arcsec'),
#                     Line2D([0], [0], color='blue', lw=4, label='FWHM in pixels')]
# plt.legend(handles=legend_elements)


# Show all plots
plt.show()

