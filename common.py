import glob,os,sys
import time
import crop
from fwhm import Calculator
import psutil
import shutil
import json

CONFIG_FILE="lucky_imaging.cnf.json"
def save_config_to_file(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
      f.write(json.dumps(data, ensure_ascii=False, indent=4))

def load_config_from_file():
    if not os.path.isfile(CONFIG_FILE):
        return None

    with open(CONFIG_FILE) as f:
        return json.load(f)

def create_config_from_arguments():
    print("In order to create the config answer the following questions.")
    if test:
        data = test_args()
    else:
        data = parse_args()

    data["cropped_folder"] = os.path.join(data["path"], "CroppedGoodImages")
    data["moved_originals_folder"] = os.path.join(data["path"], "MovedOriginalImages")

    print("Saving config to file: {}".format(CONFIG_FILE))
    print(data)
    save_config_to_file(data)
    print("You can rerun this tool any time or manually adapt the config file.")
    return data

def parse_args():
    print("This script will automatically delete image files if they exceed a certain full width half maximum")
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
    del_uncrop=str(input("Delete original uncropped images (Y/N):")).lower()

    json_result = {
        "perW": perW,
        "perH": perH,
        "path": path,
        "FWHMthresh": FWHMthresh,
        "del_uncrop": del_uncrop
    }

    return json_result

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
    fwhm = Calculator().fwhm(original)
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
    set_process_priority()

    # Parse arguments
    data = load_config_from_file()

    if data != None:
        use_config=str(input("Use existing config file (Y/N) N means a new one will be created:")).lower()
        if use_config == "y":
            print("Reusing config file.")
        else:
            data = create_config_from_arguments()
    else:
        print("No config file found.. Creating one.")
        data = create_config_from_arguments()

    # Create destination folder for cropped images.
    print("Cropped: {}".format(data["cropped_folder"]))
    create_folder(data["cropped_folder"])

    if data["del_uncrop"]:
        create_folder(data["moved_originals_folder"])

    # Return parsed arguments.
    return data
