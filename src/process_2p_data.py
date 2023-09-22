
import sys
import getopt
import os
import subprocess
import json
import logging
import shutil

from datetime import datetime

import pandas as pd

from suite2p import default_ops, run_s2p

sys.path.append("~/Github/azure")

# get and parse options
def parse_args(argv, config_data):
    args_dict = {}
    args_dict["metafile"] = False
    args_dict["animals"] = ""
    args_dict["dates"] = ""
    args_dict["imagej"] = False
    args_dict["suite2p"] = False
    args_dict["overwrite"] = False
    args_dict["project_dir"] = config_data["path_to_project_dir"]
    args_dict["get_data"] = False
    args_dict["get_behav_data"] = False
    args_dict["delete_intermediates"] = False
    arg_help = "{} -a <animals> -d <dates>".format(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "hmisogbXp:a:d:")
    except:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)
            sys.exit(2)
        elif opt in ("-m", "--get_metafile"):
            args_dict["metafile"] = True
        elif opt in ("-i", "--do_imagej"):
            args_dict["imagej"] = True
        elif opt in ("-s", "--do_suite2p"):
            args_dict["suite2p"] = True
        elif opt in ("-o", "--overwrite"):
            # add line to ask user to confirm overwrite
            args_dict["overwrite"] = True
        elif opt in ("-g", "--get_data"):
            args_dict["get_data"] = True
        elif opt in ("-b", "--get_behav_data"):
            args_dict["get_behav_data"] = True
        elif opt in ("-p", "--project_dir"):
            args_dict["project_dir"] = arg
        elif opt in ("-X", "--delete_intermediates"):
            args_dict["delete_intermediates"] = True
        elif opt in ("-a", "--animals"):
            args_dict["animals"] = arg
        elif opt in ("-d", "--dates"):
            args_dict["dates"] = arg

    print("Arguments parsed successfully")
    
    return args_dict

def check_existing_files(path_to_check, overwrite):
    if len(os.listdir(path_to_check)) > 0:
        if overwrite == False:
            logger.info("Files found in {}. If you want to re-download or re-analyze then run the command again with the -o option.".format(path_to_check))
            return False
        else:
            i = input("Overwrite option is selected. Do you want to try downloading the raw data again? (y/N)")
            if i != "y":
                return False
            else:
                return True
    else:
        return True

def get_session_string_from_df(row):
    day = str(int(row['day'].item())).zfill(3)
    date_prefix = "ses-{}".format(day)
    date_obj = datetime.strptime(row["date"].item(), "%d/%m/%Y")
    date_suffix = date_obj.strftime("%Y%m%d")
    return date_prefix + "-" + date_suffix

f = open("config.json")
config_data = json.load(f)
args_dict = parse_args(sys.argv, config_data)

if not os.path.isdir(args_dict["project_dir"]):
    os.mkdir(args_dict["project_dir"])

logdir = os.path.join(args_dict["project_dir"], "log")
if not os.path.isdir(logdir):
    os.mkdir(logdir)

## setting up logger
logfile = os.path.join(args_dict["project_dir"], "log", "{}.log".format(datetime.now().strftime('%Y-%m-%d_%H:%M:%S')))

logger = logging.getLogger(logfile)
logger.setLevel(level=logging.DEBUG)

logStreamFormatter = logging.Formatter(
  fmt=f"%(levelname)-8s %(asctime)s \t line %(lineno)s - %(message)s", 
  datefmt="%H:%M:%S"
)
consoleHandler = logging.StreamHandler(stream=sys.stdout)
consoleHandler.setFormatter(logStreamFormatter)
consoleHandler.setLevel(level=logging.DEBUG)

logger.addHandler(consoleHandler)

logFileFormatter = logging.Formatter(
    fmt=f"%(levelname)s %(asctime)s L%(lineno)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
fileHandler = logging.FileHandler(filename=logfile)
fileHandler.setFormatter(logFileFormatter)
fileHandler.setLevel(level=logging.DEBUG)

logger.addHandler(fileHandler)

logger.info("Created log file at {}".format(logfile))

if args_dict["metafile"]:
    logger.info("Downloading metafile from remote repo")
    path_to_azcopy = config_data["path_to_azcopy"]
    subprocess.call("{} cp {} {}".format(path_to_azcopy, config_data["metafile"], args_dict["project_dir"]), shell=True)

csv_file = os.path.join(args_dict["project_dir"], os.path.basename(config_data["metafile"]))
logger.info("Reading CSV file... {}".format(csv_file))
if not os.path.exists(csv_file):
    logger.info("CSV file cannot be found. Exiting.")
    sys.exit(2)

df = pd.read_csv(csv_file)
# print(df.head())

# inspect mouse and date options to produce list of files

if args_dict["animals"] == "all":
    args_dict["animals"] = df["animal"].unique()
elif args_dict["animals"] == "":
    logger.info("No animals given. Exiting")
    sys.exit(2)
else:
    args_dict["animals"] = args_dict["animals"].split()

if args_dict["dates"] == "all":
    args_dict["dates"] = df["date"].unique()
elif args_dict["dates"] == "":
    logger.info("No dates given. Exiting")
    sys.exit(2)
else:
    args_dict["dates"] = args_dict["dates"].split()

logger.info("Analysing {} on {}".format(args_dict["animals"], args_dict["dates"]))

# make directory structure
path_root = args_dict["project_dir"]
path_raw = os.path.join(path_root, "rawdata")
path_imaging = os.path.join(path_raw, "imaging")
path_behav = os.path.join(path_raw, "behav")
path_processed = os.path.join(path_root, "processeddata")
path_proc_ij = os.path.join(path_processed, "proc_ij")
path_proc_s2p = os.path.join(path_processed, "proc_s2p")

if not os.path.isdir(path_root):
    logger.info("Project path does not exist. Exiting.")
    sys.exit(2)

if not os.path.isdir(path_raw):
    os.mkdir(path_raw)
    os.mkdir(path_imaging)
    os.mkdir(path_behav)
    logger.info("Creating directories for raw data.")

if not os.path.isdir(path_processed):
    os.mkdir(path_processed)
    os.mkdir(path_proc_ij)
    os.mkdir(path_proc_s2p)

    logger.info("Creating directories for processed data.")

for animal in args_dict["animals"]:

    animal_imaging_path = os.path.join(path_imaging, "sub-{}".format(animal))
    animal_behav_path = os.path.join(path_behav, "sub-{}".format(animal))
    animal_ij_path = os.path.join(path_proc_ij, "sub-{}".format(animal))
    animal_s2p_path = os.path.join(path_proc_s2p, "sub-{}".format(animal))
    
    for path in [animal_imaging_path, animal_behav_path, animal_ij_path, animal_s2p_path]:
        if not os.path.isdir(path):
            os.mkdir(path)

    for date in args_dict["dates"]:
        print("\n***********************************\n")
        logger.info("Now analysing {}, {}".format(animal, date))
        row = df[(df["animal"] == animal) & (df["date"] == date)]
        
        try:
            ses_path = get_session_string_from_df(row)
            day = str(row['day'].item()).zfill(3)
        except:
            logger.info("Cannot find matching values for {} on {}. Continuing to next animal/date combination.".format(animal, date))
            continue

        ses_imaging_path = os.path.join(animal_imaging_path, ses_path)
        ses_behav_path = os.path.join(animal_behav_path, ses_path)
        ses_ij_path = os.path.join(animal_ij_path, ses_path)
        ses_s2p_path = os.path.join(animal_s2p_path, ses_path)

        imaging_file_remote = os.path.join(config_data["remote"], row["folder"].item(), row["scanimagefile"].item())
        imaging_file_local = os.path.join(ses_imaging_path, "sub-{}_ses-{}_2p.tif".format(animal, day))

        event_file_remote = os.path.join(config_data["remote"], "bonsai", row["eventfile"].item())
        event_file_local = os.path.join(ses_behav_path, "sub-{}_ses-{}_events.csv".format(animal, day))

        frame_file_remote = os.path.join(config_data["remote"], "bonsai", row["framefile"].item())
        frame_file_local = os.path.join(ses_behav_path, "sub-{}_ses-{}_frames.csv".format(animal, day))

        lick_file_remote = os.path.join(config_data["remote"], "bonsai", row["licks"].item())
        lick_file_local = os.path.join(ses_behav_path, "sub-{}_ses-{}_licks.csv".format(animal, day))       

        if os.path.isdir(ses_s2p_path):
            if not check_existing_files(ses_s2p_path, args_dict["overwrite"]):
                logger.info("Suite2p analysis files exist. If you want to re-analyze then either use the overwrite option or delete suite2p analysis files.")
                continue

        for path in [ses_imaging_path, ses_behav_path, ses_ij_path, ses_s2p_path]:
            if not os.path.isdir(path):
                 os.mkdir(path)

        if args_dict["get_data"]:
            if not check_existing_files(ses_imaging_path, args_dict["overwrite"]):
                print("exiting")
                continue

            logger.info("Downloading imaging data...")
            path_to_azcopy = config_data["path_to_azcopy"]

            subprocess.call("{} cp {}.tif {}".format(path_to_azcopy, imaging_file_remote, imaging_file_local), shell=True)
            if not os.path.exists(imaging_file_local):
                logger.debug("Failed to get file using azcopy. Check azcopy log.")

        if args_dict["get_behav_data"]:
            logger.info("Downloading behavioral data...")
            path_to_azcopy = config_data["path_to_azcopy"]

            subprocess.call("{} cp {} {}".format(path_to_azcopy, event_file_remote, event_file_local), shell=True)
            # subprocess.call("{} cp {} {}".format(path_to_azcopy, frame_file_remote, frame_file_local), shell=True)
            # subprocess.call("{} cp {} {}".format(path_to_azcopy, lick_file_remote, lick_file_local), shell=True)
  
        # do imagej if needed
        if args_dict["imagej"]:
            if not check_existing_files(ses_ij_path, args_dict["overwrite"]):
                print("exiting")
                continue
            logger.info("Processing with ImageJ...")
            path_to_imagej = config_data["path_to_imagej"]
            proj = config_data["imagej_settings"]["projection"]
            z = config_data["imagej_settings"]["zplanes"]
            chunks = config_data["imagej_settings"]["framesperchunk"]

            subprocess.call("{} -macro split_2p_tiff.ijm '{}, {}, {}, {}, {}' -batch ".format(path_to_imagej, imaging_file_local, ses_ij_path, proj, chunks, z), shell=True)

            if args_dict["delete_intermediates"]:
                logger.info("Delete intermediates selected so removing {}".format(ses_imaging_path))
                shutil.rmtree(ses_imaging_path)

        if args_dict["suite2p"]:
            if not check_existing_files(ses_s2p_path, args_dict["overwrite"]):
                print("exiting")
                continue
            logger.info("Processing with suite2p...")
            db = {'data_path': [ses_ij_path]}
            ops = default_ops()
            ops["save_path0"] = ses_s2p_path
            ops["anatomical_only"] = 3
            ops["diameter"] = 15

            run_s2p(ops=ops,db=db)

            if args_dict["delete_intermediates"]:
                logger.info("Delete intermediates selected so removing {}".format(ses_ij_path))
                shutil.rmtree(ses_ij_path)

logger.info("Emptying trash...")
subprocess.call("trash-empty", shell=True)
