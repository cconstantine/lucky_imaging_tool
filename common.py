import glob,os,sys
import time
import crop
from fwhm import Calculator
import psutil

def parse_args():
    print("This script will automatically delete image files if they exceed a certain full width half maximum")
    print("This is set up for fits files only")
    pixelSize=float(input("Pixel size: "))
    fl=float(input("Focal Length: "))
    perW=float(input("Fraction of the width to keep (0 - 1, where 0 crops all, 1 keeps full image), ex: 70%=0.7: "))
    perH=float(input("Fraction of the height to keep (0 - 1, where 0 crops all, 1 keeps full image),, ex: 70%=0.7: "))
    path=input("Enter Filepath for monitoring images (e.g. C:\Astrophotography\M31 ): ")
    print("Next select the FWHM or half-flux radius over which images will be deleted")
    print("Note that this is not the FWHM in arc seconds, but in pixels")
    FWHMthresh=float(input("Rejection threshold (FWHM in arcseconds, or HFR in arcseconds) above which to delete files: "))
    del_uncrop=str(input("Delete original uncropped images (Y/N):"))
    del_uncrop=del_uncrop.lower()

    newpath=os.path.join(path, "CroppedGoodImages")

    return perW, perH, path, FWHMthresh, del_uncrop

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_fits_from_folder(path):
    return glob.glob(os.path.join(path,"*.fit*"))

def is_file_safe_to_handle(file):
    DELTA = 3 #seconds
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
    if is_file_safe_to_handle(original) == False:
        return #Skip it
    fwhm = Calculator().fwhm(original,fl,pixelSize)
    sys.stdout.write("{} fwhm: ".format(original))
    sys.stdout.write("{:2.5f}.  ".format(fwhm, original))
    if(fwhm>FWHMthresh):
        if (del_uncrop[0]=="y"):
            print("Above threshold of {:2.5f} detected, deleting.".format(FWHMthresh))  #Indicates file being deleted
            os.remove(original)   #Removes the offending file
    else:
        if(perW!=1 and perH!=1):
            cropped_file = os.path.join(cropped_folder, os.path.basename(original))
            sys.stdout.write("Cropping to {}.  ".format(cropped_folder))
            crop.crop(original, cropped_file, perW, perH)
            if (del_uncrop[0]=="y"):
                sys.stdout.write("Deleting original file.")  #Indicates file being deleted
                os.remove(original)
            print()
        else:
            moved_original_file = os.path.join(moved_orignals_folder, os.path.basename(original))
            print("Moving to {}".format(moved_orignals_folder))
            os.rename(original, moved_original_file)


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
