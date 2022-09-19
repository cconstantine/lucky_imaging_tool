import common
from astropy.io import fits
import numpy as np
import sep
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

def get_stars_from_data(data):

    # Plot raw image data
    m, s = np.mean(data), np.std(data)
    org_plt = plt.figure("Raw data")
    print(org_plt)
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
    objects = sep.extract(data, 500, err=bkg.globalrms, filter_type="matched", filter_kernel=kernel)

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
                    width=6*objects['a'][i],
                    height=6*objects['b'][i],
                    angle=objects['theta'][i] * 180. / np.pi)
        e.set_facecolor('none')
        e.set_edgecolor('red')
        ax.add_artist(e)

        w = Ellipse(xy=(objects['x'][i], objects['y'][i]),
                    width=6*objects['cxx'][i],
                    height=6*objects['cyy'][i],
                    angle=objects['cxy'][i] * 180. / np.pi)
        w.set_facecolor('none')
        w.set_edgecolor('yellow')
        ax.add_artist(w)

        q = Ellipse(xy=(objects['x'][i], objects['y'][i]),
                    width=60*objects['a'][i],
                    height=60*objects['b'][i],
                    angle=objects['theta'][i] * 180. / np.pi)
        q.set_facecolor('none')
        q.set_edgecolor('green')

        ax.add_artist(q)

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
    r, flag = sep.flux_radius(data, objects['x'], objects['y'], 6.*objects['a'], 0.5,
                              normflux=flux, subpix=5)
    print(r)

    for i in range(len(objects)):
        z = Ellipse(xy=(objects['x'][i], objects['y'][i]),
                    width=60*objects['a'][i],
                    height=60*objects['b'][i],
                    angle=objects['theta'][i] * 180. / np.pi)
        z.set_facecolor('none')
        z.set_edgecolor('purple')

        ax.add_artist(z)

    print("Found {} objects".format(len(objects)))
    return objects

image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\bin_2_Light_Luminance_0.500_secs_2022-09-09T22-17-57_001.fits"
# image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\t4_bin2.fits"
# image="C:\\Users\\Thomas\\Downloads\\thomas\\lucky_imaging_tool\\test\\images\\Light_ASIImg_0.2sec_Bin1_-14.1C_gain390_2022-09-02_020039_frame0004.fit"
with fits.open(image) as f:
    data = f[0].data

    # Convert to 32 bit integer
    data=np.array(data,dtype='int32')

    objects = get_stars_from_data(data)


    # Show all plots
    plt.show()

