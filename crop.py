import glob,os
from astropy.nddata import Cutout2D
from astropy.io import fits

def crop(file, newfile, perW, perH):
    img=fits.open(file)
    header=img[0].header
    img_data=img[0].data

    # print(repr(header))
    # print(header["SIMPLE"])

    if header["SIMPLE"] == False: #File does conform to FITS standard
        print("File {} does not conform to FITS standard. Corrupted file?".format(file))
        img.close()
        return

    height,width=img_data.shape
    position=(width//2,height//2)
    #size=(int(width*perW)+height//2,int(height*perH)+height//2)
    size=(int(height*perH),int(width*perW))
    print("Cropping ", file)
    cutout=Cutout2D(img_data,position,size)
    #print(cutout.data)
    img.close() #release the file so we can delete it
    fits.writeto(newfile,cutout.data,header,overwrite=True)

if __name__ == "__main__":
    path="H:\MyWorkPythonAll"
    newpath=os.path.join(path,"CroppedGoodImages")
    
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    
    for file in glob.glob(os.path.join(path,"*.fits")):
        file2 = os.path.join(newpath, os.path.basename(file))
        crop(file, file2, 0.7, 0.7)
