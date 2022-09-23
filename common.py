import glob,os,sys
import time
import crop
from fwhm import Calculator
import psutil
import shutil
import json
from astropy.io import fits
import traceback
import gc
import numpy as np

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
    pixelSize=float(input("Pixel size: "))
    fl=float(input("Focal Length: "))
    numStar=int(input("Enter the number of stars you want detected: "))
    perW=float(input("Fraction of the width to keep (0 - 1, where 0 crops all, 1 keeps full image), ex: 70%=0.7: "))
    perH=float(input("Fraction of the height to keep (0 - 1, where 0 crops all, 1 keeps full image),, ex: 70%=0.7: "))
    path=input("Enter Filepath for monitoring images (e.g. C:\Astrophotography\M31 ): ")
    print("Next select the FWHM in arcsecond threshold over which images will be deleted. Any image with a value larger then X (Exmaple: 3.0) will be deleted.")
    print("Note that this is not the FWHM in arc seconds, but in pixels")
    FWHMthresh=float(input("Rejection threshold (FWHM in arcseconds, or HFR in arcseconds) above which to delete files: "))
    del_uncrop=str(input("Delete original uncropped images (Y/N):"))
    del_uncrop=del_uncrop.lower()

    json_result = {
        "perW": perW,
        "perH": perH,
        "path": path,
        "FWHMthresh": FWHMthresh,
        "del_uncrop": del_uncrop,
        "numStar": numStar,
        "pixelSize": pixelSize,
        "fl": fl
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

 
def calculate_fwhm(data, FWHMthresh, numStar, focal_length, pixel_size):
    # Use calculator to get fwhm from image.
    objects, fwhm_px, fwhm_arcsec = Calculator(numStar, FWHMthresh).fwhm(focal_length, pixel_size, data)
    
    # If the fwhm is above the threshold it shall be removed.
    is_fwhm_above_threshold = fwhm_px > FWHMthresh
    if is_fwhm_above_threshold:
        print("fwhm {:2.5f} > threshold {:2.5f}".format(fwhm_px, FWHMthresh))
    else:
        print("fwhm {:2.5f} <= threshold {:2.5f}".format(fwhm_px, FWHMthresh))

    return fwhm_px, fwhm_arcsec, is_fwhm_above_threshold

def crop_file(file, fits_data, fits_header, perW, perH, destination_folder):
    # Where to store the cropped file.
    cropped_fits_file = os.path.join(destination_folder, os.path.basename(file))
    print("Cropping to {}.  ".format(destination_folder))

    # Crop file.
    cropped_fitsdata = crop.crop(fits_data, perW, perH)

    # Save cropped image.
    fits.writeto(cropped_fits_file, cropped_fitsdata, fits_header, overwrite=True)

def backup_file(file, destination_folder):
    # Move original to backup location. Required so that script does not rehandle the same file.
    moved_file = os.path.join(destination_folder, os.path.basename(file))
    print("Moving to {}".format(destination_folder))
    os.rename(file, moved_file)

def is_file_a_fits_file(fitsheader):
    return fitsheader["SIMPLE"] #Boolean answer.

# This file is called by multithreading threads/procs, any prints/exceptions will only be printed from a try catch.
def handle_file(original, cropped_folder, moved_orignals_folder, del_uncrop, FWHMthresh, perW, perH, numStar, pixelSize, fl):
    try:
        # If the cropping percentage differs from the original, crop it.
        # 1 equals original size, so no cropping shall occur.
        do_crop = (perW != 1 or perH != 1)

        # After a capture the file might still be in use. This ensures that the file has been written fully.
        if is_file_safe_to_handle(original) == False:
            print("Skipping unsafe file")
            return False, original, False, do_crop, del_uncrop, moved_orignals_folder, False

        print("File: {}".format(original))
        is_fwhm_above_threshold = False

        with fits.open(original) as f_fits:
            is_fits_file = is_file_a_fits_file(f_fits[0].header)

            if is_fits_file:
                data = f_fits[0].data

                # TODO: add all other bayer patterns
                try:
                    bayer_pattern = header["BAYERPAT"]
                    print("bayer_pattern is {}".format(bayer_pattern))

                    debayered_image = cv2.cvtColor(data, cv2.COLOR_BayerRG2BGR)
                    data = cv2.normalize(debayered_image, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_16U)

                except Exception as e:
                    bayer_pattern = None

                # Convert to 32 bit integer
                data=np.array(data,dtype='int32')

                #Calculate fwhm
                fwhm_px, fwhm_arcsec, is_fwhm_above_threshold = calculate_fwhm(data, FWHMthresh, numStar, fl, pixelSize)

                # Crop image is cropping parameters are set (unset is equal to original) and fwhm is OK
                if(do_crop and not is_fwhm_above_threshold):
                    crop_file(original, f_fits[0].data, f_fits[0].header, perW, perH, cropped_folder)
        return True, original, is_fwhm_above_threshold, do_crop, del_uncrop, moved_orignals_folder, is_fits_file
    except Exception as e:
        # traceback.print_exc()
        return False, original, False, False, 'n', moved_orignals_folder, is_fits_file


def test_args():
    return float(0.7), float(0.7), str("C:\\Users\\Thomas\\Downloads\\lucky_imaging_tool\\MyWorkPythonAll"), float(10), str("n"), 10, float(4.63), 1000

_INFO = '''
______                             __          _   _            _                              _   ___  
|  _  \                           / _|        | | | |          | |                            | | |__ \ 
| | | |___    _   _  ___  _   _  | |_ ___  ___| | | |_   _  ___| | ___   _   _ __  _   _ _ __ | | __ ) |
| | | / _ \  | | | |/ _ \| | | | |  _/ _ \/ _ \ | | | | | |/ __| |/ / | | | | '_ \| | | | '_ \| |/ // / 
| |/ / (_) | | |_| | (_) | |_| | | ||  __/  __/ | | | |_| | (__|   <| |_| | | |_) | |_| | | | |   <|_|  
|___/ \___/   \__, |\___/ \__,_| |_| \___|\___|_| |_|\__,_|\___|_|\_\\__, | | .__/ \__,_|_| |_|_|\_(_)  
               __/ |                                                  __/ | | |                         
              |___/                                                  |___/  |_|                         
 _    _      _ _              _                    ___                                                  
| |  | |    | | |            | |                  |__ \                                                 
| |  | | ___| | |          __| | ___    _   _  __ _  ) |                                                
| |/\| |/ _ \ | |         / _` |/ _ \  | | | |/ _` |/ /                                                 
\  /\  /  __/ | |_ _ _   | (_| | (_) | | |_| | (_| |_|                                                  
 \/  \/ \___|_|_(_|_|_)   \__,_|\___/   \__, |\__,_(_)                                                  
                                         __/ |                                                          
                                        |___/                                                           

IMPORTANT: This script will overwrite any files from a previous session when the same capture folder is used and new images match those of a previous session.
Ensure that the captured files have a different name by adding a prefix or add the timestamp to the filenames.")
Pressing both CTRL and the 'C' character (CTRL+C) exits the applicaton. Prevents corruption in images.")
'''
test=False
def init():
    set_process_priority()


     # Parse arguments
    data = load_config_from_file()
 
    # Set console size.
    os.system("mode con cols=120 lines=50")

    # Print info.
    print(_INFO)
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
