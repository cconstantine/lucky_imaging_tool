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

def get_stars_from_data(focal_length, pixel_size, data, threshold):

    # Plot raw image data
    m, s = np.mean(data), np.std(data)
    org_plt = plt.figure("Raw data")
    plt.imshow(data, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    plt.colorbar();

    # Representation of spatially variable image background and noise.
    bkg = sep.Background(data)

    # evaluate background as 2-d array, same size as original image
    bkg_image = bkg.back()
    # Plot background data
    # m, s = np.mean(bkg_image), np.std(bkg_image)
    bkg_plot = plt.figure("Background data")
    plt.imshow(bkg_image, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    plt.colorbar();

    # Get backround noise
    # Plot background data
    bkg_rms = bkg.rms()
    # m, s = np.mean(bkg_rms), np.std(bkg_rms)
    bkg_plot = plt.figure("Background RMS data")
    plt.imshow(bkg_rms, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    plt.colorbar();


    # Subtract the background from an existing array. Like data = data - bkg, but avoids making a copy of the data.
    bkg.subfrom(data)

    # Plot background subtracketed data
    # m, s = np.mean(data), np.std(data)
    bkg_sub_plot = plt.figure("Background subtrackted data")
    plt.imshow(data, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    plt.colorbar();

    # Create a filter-kernal with the shape of a star (round point ;))
    kernel = np.array([[1., 2., 3., 2., 1.],
    [2., 3., 5., 3., 2.],
    [3., 5., 8., 5., 3.],
    [2., 3., 5., 3., 2.],
    [1., 2., 3., 2., 1.]])
    objects = sep.extract(data, threshold, err=bkg.globalrms, filter_type="matched", filter_kernel=kernel)
    print(len(objects))
    # exit()

    # Plot found objects
    # bkg_sub_plot = plt.figure("Found stars")
    fig, ax = plt.subplots()

    fig.canvas.set_window_title('Detect starts in data')
    # m, s = np.mean(data), np.std(data)
    ## Add the background subtrackted data.
    im = ax.imshow(data, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
    ## Plot an ellipse for each object
    for i in range(len(objects)):
        # print(objects['a'])
        # print(objects['cxx'])
        e = Ellipse(xy=(objects['x'][i], objects['y'][i]),
                    width=10*objects['a'][i],
                    height=10*objects['b'][i],
                    angle=objects['theta'][i] * 180. / np.pi)
        e.set_facecolor('none')
        e.set_edgecolor('red')
        ax.add_artist(e)

        # w = Ellipse(xy=(objects['x'][i], objects['y'][i]),
        #             width=6*objects['cxx'][i],
        #             height=6*objects['cyy'][i],
        #             angle=objects['cxy'][i] * 180. / np.pi)
        # w.set_facecolor('none')
        # w.set_edgecolor('magenta')
        # ax.add_artist(w)

        # q = Ellipse(xy=(objects['x'][i], objects['y'][i]),
        #             width=60*objects['a'][i],
        #             height=60*objects['b'][i],
        #             angle=objects['theta'][i] * 180. / np.pi)
        # q.set_facecolor('none')
        # q.set_edgecolor('pink')

        # ax.add_artist(q)

        # break

    # plt.colorbar();

    # Try add kron radius (to estimate magnitude)
    kronrad, krflag = sep.kron_radius(data, objects["x"], objects["y"], objects["a"], objects["b"], objects["theta"], 6.0)
    flux, fluxerr, flag = sep.sum_ellipse(data, objects["x"], objects["y"], objects["a"], objects["b"], objects["theta"], 2.5*kronrad,
                                          subpix=1)
    flag |= krflag  # combine flags into 'flag'        
    # print(flux)

    # Ignore too small values (zero)
    r_min = 1.75  # minimum diameter = 3.5
    use_circle = kronrad * np.sqrt(objects["a"], objects["b"]) < r_min
    cflux, cfluxerr, cflag = sep.sum_circle(data, objects["x"][use_circle], objects["y"][use_circle],
                                            r_min, subpix=1)
    flux[use_circle] = cflux
    fluxerr[use_circle] = cfluxerr
    flag[use_circle] = cflag

    # Try to calculate flux radius
    r_half, r_half_flag = sep.flux_radius(data, objects['x'], objects['y'], 6.*objects['a'], 0.5,
                              normflux=flux, subpix=5)
    r_full, r_full_flag = sep.flux_radius(data, objects['x'], objects['y'], 6.*objects['a'], 1.0,
                              normflux=flux, subpix=5)

    print("----------------------")
    print(r_half)
    print(r_full)
    print("----------------------")

    # Calculate the FWHMs of the stars:
    fwhm = 2.0 * (np.log(2) * (objects['a'] ** 2.0 + objects['b'] ** 2.0)) ** 0.5

    # for i in range(len(objects)):
    #     thing=(float(objects['a'][i])**2) + (float(objects['b'][i])**2)
    #     fwhm2 = 2 * (sqrt((np.log(2)) * thing))
    #     print(fwhm)
    #     print(fwhm2)
    #     print("print fwhm ({}) vs fwhm2 ({})".format(fwhm[i], fwhm2))

    #     # This value is useless
    #     z = Ellipse(xy=(objects['x'][i], objects['y'][i]),
    #                 width=60*objects['a'][i],
    #                 height=60*objects['b'][i],
    #                 angle=objects['theta'][i] * 180. / np.pi)
    #     z.set_facecolor('none')
    #     z.set_edgecolor('purple')

    #     ax.add_artist(z)


    arcsec_constant = 206.265
    # pixel_size = 4.63
    reducer = 1.0
    # focal_length = 1000 * reducer
    pixel_scale = ((pixel_size / focal_length) * arcsec_constant)
    perfect_arcsec_per_px = 122 / focal_length
    image_scale = arcsec_constant * pixel_size / focal_length

    # Get more accurate x and y coordinates.
    x = sep.winpos(data, objects["x"], objects["y"], (2.0 / 2.35 * r_full))
    print(x)
    for i in range(len(objects)):
        z = Ellipse(xy=(x[0][i], x[1][i]),
                    width=1,
                    height=1,
                    angle=objects['theta'][i] * 180. / np.pi)
        z.set_facecolor('red')
        z.set_edgecolor('red')
        ax.add_artist(z)

        print("flux radius is {}".format(r_full[i]))
        # print("a is {}".format(objects['a'][i]))
        # print("b is {}".format(objects['b'][i]))

        c = Circle(xy=(x[0][i], x[1][i]), radius = r_full[i])
        c.set_facecolor('none')
        c.set_edgecolor('blue')
        ax.add_artist(c)

        d = Circle(xy=(x[0][i], x[1][i]), radius= r_half[i])
        d.set_facecolor('none')
        d.set_edgecolor('lime')
        ax.add_artist(d)



        text_offset = 15
        plt.text(x[0][i] + text_offset, x[1][i] + text_offset, "Star [{}] fwhm: {:.2f}".format(i, fwhm[i]), bbox=dict(facecolor='red'))

        fwhm_arcsec = pixel_scale * fwhm[i]
        print("This star has an fwhm in arcsec of {}".format(fwhm_arcsec))

    legend_elements = [ Line2D([0], [0], color='blue', lw=4, label='Full width of star'),
                        Line2D([0], [0], color='lime', lw=4, label='FMHW of star'),
                        Line2D([0], [0], color='red', lw=4, label='Blown up shape. Shows roundness of star')]
    plt.legend(handles=legend_elements)


    print("pixel_scale in arcsec is {}".format(pixel_scale))
    print("image_scale in arcsec is {}".format(image_scale))
    print("Found {} objects".format(len(objects)))
    print("Average fwhm is {}".format(np.average(fwhm)))
    print("Average acsec is {}".format(pixel_scale * np.average(fwhm)))

    print("mean fwhm is {}".format(np.mean(fwhm)))
    print("mean acsec is {}".format(pixel_scale * np.mean(fwhm)))

    print("median fwhm is {}".format(np.median(fwhm)))
    print("median acsec is {}".format(pixel_scale * np.median(fwhm)))

    print("max fwhm is {}".format(np.max(fwhm)))
    print("max acsec is {}".format(pixel_scale * np.max(fwhm)))

    print("min fwhm is {}".format(np.min(fwhm)))
    print("min acsec is {}".format(pixel_scale * np.min(fwhm)))

    sigma = np.median(fwhm/(2*sqrt(2*log(2))))
    r_full_sigma = np.median(r_full/(2*sqrt(2*log(2))))
    print("sigma is {}".format(sigma))

    print("fwhm + sigma is {}".format(sigma + np.mean(fwhm)))
    print("r_full + sigma is {}".format(r_full_sigma + np.mean(r_full)))
    print("fwhm + sigma in arcsec {}".format((sigma + np.mean(fwhm)) * image_scale))

    mean, stdev = np.mean(fwhm), np.std(fwhm)
    print("The one fwhm is {}".format(mean))
    print("The one dev is {}".format(stdev))
    print("The one is {}".format(mean + stdev))
    print("The one arcsec is {}".format((mean + stdev) * image_scale))

    # Print a comparable string as test-my-scope
    final_fwhm = mean + stdev
    final_arcsec = (mean + stdev) * image_scale
    print("FWHM: {} px / {} arcsec".format(final_fwhm, final_arcsec))

    return objects


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

threshold, image, header_inserts = test_image1()

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

    print(focal_length)
    print(pixel_size)

    try:
        bayer_pattern = header["BAYERPAT"]
        print("bayer_pattern is {}".format(bayer_pattern))

        debayered_image = cv2.cvtColor(data, cv2.COLOR_BayerRG2BGR)
        data = cv2.normalize(debayered_image, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_16U)

    except Exception as e:
        bayer_pattern = None

    # Convert to 32 bit integer
    data=np.array(data,dtype='int32')

    objects = get_stars_from_data(focal_length, pixel_size, data, threshold)


    # Show all plots
    plt.show()

