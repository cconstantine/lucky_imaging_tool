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
    data = parse_args()

    data["cropped_folder"] = os.path.join(data["monitoring_folder"], "CroppedGoodImages")
    data["moved_unsupported_folder"] = os.path.join(data["monitoring_folder"], "MovedUnsupportedImages")
    data["moved_originals_folder"] = os.path.join(data["monitoring_folder"], "MovedOriginalImages")
    data["moved_rejects_folder"] = os.path.join(data["monitoring_folder"], "MovedRejectedImages")

    print("Saving config to file: {}".format(CONFIG_FILE))
    print(data)
    save_config_to_file(data)
    print("You can rerun this tool any time or manually adapt the config file.")
    return data

def parse_args():
    print("This script will automatically delete image files if they exceed a certain full width half maximum")
    print("This is set up for fits files only")
    pixel_size=float(input("Pixel size: "))
    focal_length=float(input("Focal Length: "))
    detect_number_of_stars_target=int(input("Enter the number of stars you want detected: "))
    crop_factor_width=float(input("Fraction of the width to keep (0 - 1, where 0 crops all, 1 keeps full image), ex: 70%=0.7: "))
    crop_factor_height=float(input("Fraction of the height to keep (0 - 1, where 0 crops all, 1 keeps full image),, ex: 70%=0.7: "))
    monitoring_folder=input("Enter Filepath for monitoring images (e.g. C:\Astrophotography\M31 ): ")
    print("Next select the FWHM in arcsecond threshold over which images will be deleted. Any image with a value larger then X (Example: 3.0) will be deleted.")
    print("Note that this is the FWHM in arc seconds, not pixels")
    fwhm_arcsec_threshold=float(input("Rejection threshold (FWHM in arcseconds, or HFR in arcseconds) above which to delete files: "))
    delete_uncropped_original=str(input("Delete original uncropped images (Y/N):"))
    delete_uncropped_original=delete_uncropped_original.lower()

    json_result = {
        "crop_factor_width": crop_factor_width,
        "crop_factor_height": crop_factor_height,
        "monitoring_folder": monitoring_folder,
        "fwhm_arcsec_threshold": fwhm_arcsec_threshold,
        "delete_uncropped_original": delete_uncropped_original,
        "detect_number_of_stars_target": detect_number_of_stars_target,
        "pixel_size": pixel_size,
        "focal_length": focal_length
    }

    return json_result

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_fits_from_folder(path):
    return glob.glob(os.path.join(path,"*.fit*"))

# After a capture the file might still be in use. This ensures that the file has been written fully.
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

 
def calculate_fwhm(context, data):
    # Use calculator to get fwhm from image.
    objects, fwhm_px, fwhm_arcsec = Calculator(context).fwhm(data)

    return fwhm_px, fwhm_arcsec

def does_FWHM_exceed_threshold(fwhm_arcsec, fwhm_arcsec_threshold):
    # If the fwhm is above the threshold it shall be removed.
    is_fwhm_above_threshold = fwhm_arcsec > fwhm_arcsec_threshold
    # if is_fwhm_above_threshold:
    #     print("fwhm {:2.5f} > threshold {:2.5f}".format(fwhm_arcsec, fwhm_arcsec_threshold))
    # else:
    #     print("fwhm {:2.5f} <= threshold {:2.5f}".format(fwhm_arcsec, fwhm_arcsec_threshold))
    return is_fwhm_above_threshold

def crop_file(file, fits_data, fits_header, crop_factor_width, crop_factor_height, destination_folder):
    # Where to store the cropped file.
    cropped_fits_file = os.path.join(destination_folder, os.path.basename(file))
    # print("Cropping to {}.  ".format(destination_folder))

    # Crop file.
    cropped_fitsdata = crop.crop(fits_data, crop_factor_width, crop_factor_height)

    # Save cropped image.
    fits.writeto(cropped_fits_file, cropped_fitsdata, fits_header, overwrite=True)

def backup_file(file, destination_folder):
    # Move original to backup location. Required so that script does not rehandle the same file.
    moved_file = os.path.join(destination_folder, os.path.basename(file))
    # print("Moving to {}".format(destination_folder))
    os.rename(file, moved_file)

def is_file_a_fits_file(fitsheader):
    is_fits_file = False

    try:
        is_fits_file = fitsheader["SIMPLE"] #Boolean answer.
    except Exception as e:
        pass

    return is_fits_file

# If the cropping percentage differs from the original, crop it.
# 1 equals original size, so no cropping shall occur.
def is_crop_enabled(context):
    return (context["crop_factor_width"] != 1 or context["crop_factor_height"] != 1)

def get_bayer_pattern(fitsheader):
    bayer_pattern = None
    try:
        bayer_pattern = header["BAYERPAT"]
    except Exception:
        pass

    return bayer_pattern

def debayer(data, bayer_pattern):
    if bayer_pattern != None:
        if bayer_pattern == "RGGB":
            data = cv2.cvtColor(data, cv2.COLOR_BayerRG2BGR)
            data = cv2.normalize(data, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_16U)
        else:
            print("Unsupported debayer pattern {}".format(bayer_pattern))
            print("Please create an issue on https://github.com/cconstantine/lucky_imaging_tool/issues.")
            print("Or share you image in discord in any of the lucky imaging chats.")
            print("Currently only RGGB is supported, share and yours will be added.")
            print("Debayering is not performed.")

    return data

# This file is called by multithreading threads/procs, any prints/exceptions will only be printed from a try catch.
def process_fits_image(fits_filepath, context):
    # print("Process: {}".format(fits_filepath))

    # Default values for an unprocessed non valid fits file.
    # Any passing processing step will update the result accordingly.
    result = {
        "fits_filepath": fits_filepath,
        "cropped": False,
        "processed": False,
        "rejected": False,
        "valid_fits_file": False,
        "fwhm": {
            "px": float(-1),
            "arcsec": float(-1)
        },
    }

    try:
        do_crop = is_crop_enabled(context)
        do_process = is_file_safe_to_handle(fits_filepath)

        if do_process:
            with fits.open(fits_filepath) as f_fits:
                result["valid_fits_file"] = is_file_a_fits_file(f_fits[0].header)

                if result["valid_fits_file"]:
                    bayer_pattern = get_bayer_pattern(f_fits[0].header)
                    data = debayer(f_fits[0].data, bayer_pattern)

                    # Convert to float64 for sep library in calculate fwhm
                    # int32 is also possible but is less compatible. There have been images which won't work if converted to int32.
                    data=np.array(data,dtype='float64')

                    #Calculate fwhm
                    try:
                        result["fwhm"]["px"], result["fwhm"]["arcsec"]  = calculate_fwhm(context, data)
                    except Exception as e:
                        print("\n\n\n\n\nERROR: {}".format(fits_filepath))
                        raise Exception(e)

                    # Determine if the quality is OK.
                    result["rejected"] = does_FWHM_exceed_threshold(result["fwhm"]["arcsec"], context["fwhm_arcsec_threshold"])

                    # The file has been processed at least.
                    result["processed"] = True

                    if result["rejected"] == False:
                        if do_crop == True:
                            crop_file(fits_filepath, f_fits[0].data, f_fits[0].header, context["crop_factor_width"], context["crop_factor_height"], context["cropped_folder"])
                            result["cropped"] = True

        return context, result
    except Exception as e:
        traceback.print_exc()
        return context, result

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
 
    # Create folders for cropped and moved images according to their state.
    create_folder(data["cropped_folder"])
    create_folder(data["moved_unsupported_folder"])
    create_folder(data["moved_originals_folder"])
    create_folder(data["moved_rejects_folder"])

     # Return parsed arguments.
    return data
