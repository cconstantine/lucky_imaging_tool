import glob,os
from astropy.nddata import Cutout2D
from astropy.io import fits

def crop(data, perW, perH):
    height, width = data.shape
    position = (width//2, height//2)
    #size=(int(width*perW)+height//2,int(height*perH)+height//2)
    size=(int(height*perH),int(width*perW))

    # Crop
    cutout=Cutout2D(data, position, size)

    # Return cropped data
    return cutout.data

if __name__ == "__main__":
    path="H:\MyWorkPythonAll"
    newpath=os.path.join(path,"CroppedGoodImages")
    
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    
    for file in glob.glob(os.path.join(path,"*.fits")):
        with fits.open(file) as fits:
            fitsdata = fits[0].data
            fitsheader = fits[0].header
            cropped_file = os.path.join(newpath, os.path.basename(file))

            cropped_fits_data = crop(fitsdata, file2, 0.7, 0.7)
            #print(cutout.data)
            fits.writeto(cropped_file, cropped_fits_data, header, overwrite=True)
