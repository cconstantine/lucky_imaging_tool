import glob,os
import time
import crop

print_debug=False
def debug(str):
    if print_debug:
        print(str)

def parse_args():
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

    newpath=os.path.join(path, "CroppedGoodImages")

    return perW, perH, path, FWHMthresh, del_uncrop, newpath

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_fits_from_folder(path):
    return glob.glob(os.path.join(path,"*.fit*"))

def is_file_save_to_handle(file):
    DELTA = 15 #seconds
    f_time = os.path.getmtime(file)
    now = time.time()
    if (now - f_time) > DELTA: 
        return True
    else:
        return False

    # Set priority to the lowes value so that astro-capture software will run with a higher priority.
    # Goal is not to hinder any astro-capture software.
def set_process_priority():
    # Currently only implemented for windows.
    if sys.platform == "win32":
        # Get PID of the current process (This python script)
        PID = psutil.Process(os.getpid())

        # Set IO (disk) priority low.
        PID.ionice(psutil.IOPRIO_VERYLOW)

        # Set cpu execution priority
        PID.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

def handle_file(original, cropped_folder, moved_orignals_folder, del_uncrop, FWHMthresh, perW, perH):
    if is_file_save_to_handle == False:
        return #Skip it

    if(fwhm_from_filename(original)>FWHMthresh):#Checks of the front part of the file before word "pixels" is above the indicated threshold
        if (del_uncrop[0]=="y"):
            print("High HFR/FWHM detected, deleted ",original)  #Indicates file being deleted
            os.remove(original)   #Removes the offending file
    else:
        if(perW!=1 and perH!=1):
            timcr=os.path.getmtime(original)
            timenow=time.time()
            delta=abs(timcr-timenow)
            if(delta>15):
                cropped_file = os.path.join(cropped_folder, os.path.basename(original))
                crop.crop(original, cropped_file, perW, perH)
                if (del_uncrop[0]=="y"):
                    debug("Image cropped, original deleted {}".format(original))  #Indicates file being deleted
                    os.remove(original)
                else:
                    moved_original_file = os.path.join(moved_orignals_folder, os.path.basename(original))
                    os.rename(original, moved_original_file)

def fwhm_from_filename(filename):
    return float(os.path.basename(filename).split("pixels")[0])

def test_args():
    return float(0.7), float(0.7), str("C:\\Users\\Thomas\\Downloads\\lucky_imaging_tool\\MyWorkPythonAll"), float(10), str("n"), 

test=False
def init():
    # Parse arguments
    perW, perH, path, FWHMthresh, del_uncrop = None, None, None, None, None

    if test:
        perW, perH, path, FWHMthresh, del_uncrop = test_args()
    else:
        perW, perH, path, FWHMthresh, del_uncrop = parse_args()

    # Create destination folder for cropped images.
    cropped_folder=os.path.join(path, "CroppedGoodImages")
    print("Cropped: {}".format(cropped_folder))
    create_folder(cropped_folder)

    moved_originals_folder=os.path.join(path, "MovedOriginalImages")
    if del_uncrop:
        create_folder(moved_originals_folder)

    # Return parsed arguments.
    return perW, perH, path, FWHMthresh, del_uncrop, cropped_folder, moved_originals_folder
