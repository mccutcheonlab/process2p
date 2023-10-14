### This file will have all the main functions and classes needed for the different types of preprocessing scripts
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import logging
import shutil

import pandas as pd

# from suite2p import default_ops, run_s2p

# the base class used for most scripts in this package
class Preprocess():
  
  def __init__(self, config_data, use_fast_dir, overwrite, delete_intermediates):
    self.config_data = config_data
    self.use_fast_dir = use_fast_dir
    self.overwrite = overwrite
    self.delete_intermediates = delete_intermediates
    print("class initialized")

  def set_project_dir(self):
    self.project_dir = Path(self.config_data["path_to_project_dir"])

    if not os.path.isdir(self.project_dir):
        print("does not exist")
        os.makedirs(self.project_dir, exist_ok=True)
  
  def set_logger(self):
    self.logger = setup_logger(self.project_dir)

  def get_metafile(self):
    self.logger.info("Downloading metafile from remote repo")
    path_to_azcopy = self.config_data["path_to_azcopy"]
    subprocess.call("{} cp {} {}".format(path_to_azcopy, self.config_data["metafile"], self.project_dir), shell=True)

  def read_metafile(self):
    self.csv_file = self.project_dir / Path(self.config_data["metafile"]).name
    if not self.csv_file.is_file():
        self.logger.info("Exiting as metafile does not exist in project directory")
        sys.exit(2)

    self.metadata = pd.read_csv(self.csv_file, encoding = "ISO-8859-1")

  def parse_animals(self, animal_string):
    print("parsing animals")
    if animal_string == "all":
        self.animals = self.metadata["animal"].unique()
    elif animal_string == "":
        self.logger.info("No animals given. Exiting")
        sys.exit(2)
    else:
        self.animals = animal_string.split()
    
    self.logger.info(f"Animals being analyzed are {self.animals}")

  def parse_dates(self, date_string):

    if date_string == "all":
        self.dates = self.metadata["date"].unique()
    elif date_string == "":
        self.logger.info("No dates given. Exiting")
        sys.exit(2)
    else:
        self.dates = date_string.split()
    
    self.logger.info(f"Dates being analyzed are {self.dates}")
    
  def define_root(self):
    if self.use_fast_dir:
        self.logger.info("Using specified fast data disk. Will not save intermediates, only suite2p files.")
        self.path_root = Path(self.config_data["path_to_fast_dir"])
    else:
        self.path_root = self.project_dir

  def define_nwb_paths(self, fast_dir): 
    self.path_raw = self.path_root / "rawdata"
    self.path_imaging = self.path_raw / "imaging"
    self.path_behav = self.path_raw / "behav"
    self.path_processed = self.path_root / "processeddata"
    self.path_proc_ij = self.path_processed / "proc_ij"
    self.path_proc_s2p = self.path_processed / "proc_s2p"

    if not os.path.isdir(self.path_raw):
        os.makedirs(self.path_raw, exist_ok=True)
        os.makedirs(self.path_imaging, exist_ok=True)
        os.makedirs(self.path_behav, exist_ok=True)
        self.logger.info("Creating directories for raw data.")

    if not os.path.isdir(self.path_processed):
        os.makedirs(self.path_processed, exist_ok=True)
        os.makedirs(self.path_proc_ij, exist_ok=True)
        os.makedirs(self.path_proc_s2p, exist_ok=True)
        self.logger.info("Creating directories for processed data.")

  def define_multisession_paths(self):
    print("defining multisession path")
    

  def loop_animals(self, get_behav, get_data, do_imagej_zproject, do_suite2p):
    for self.animal in self.animals:
        self.define_animal_paths()
        
        for self.date in self.dates:
            print("\n***********************************\n")
            self.logger.info("Now analysing {}, {}".format(self.animal, self.date))
            self.row = self.metadata.query("animal == @self.animal & date == @self.date")
            if len(self.row) > 1:
               self.logger.info(f"Too many values in metafile for {self.animal} on {self.date}")
               continue

            try:
                self.ses_path = get_session_string_from_df(self.row)
                self.day = str(self.row['day'].item()).zfill(3)
            except:
                self.logger.info(f"Cannot find matching values for {self.animal} on {self.date}")
                continue

            self.define_session_paths()

            # if self.do_suite2p_files_exist():
            #    continue

            self.make_session_dirs()

            if get_behav:
               self.get_behav()
               
            if get_data:
               self.get_data()

            if do_imagej_zproject:
               self.imagej_zproject()

            # if do_suite2p:
            #    self.run_suite2p()

            if self.use_fast_dir:
               self.copy_from_fast_disk()
    
    self.logger.info("Emptying trash...")
    subprocess.call("trash-empty", shell=True)

  def define_animal_paths(self):
    self.animal_imaging_path = self.path_imaging / "sub-{}".format(self.animal)
    self.animal_behav_path = self.path_behav / "sub-{}".format(self.animal)
    self.animal_ij_path = self.path_proc_ij / "sub-{}".format(self.animal)
    self.animal_s2p_path = self.path_proc_s2p / "sub-{}".format(self.animal)
        
    for path in [self.animal_imaging_path, self.animal_behav_path, self.animal_ij_path, self.animal_s2p_path]:
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)

  def define_session_paths(self):
    self.ses_imaging_path = self.animal_imaging_path / self.ses_path
    self.ses_behav_path = self.animal_behav_path / self.ses_path
    self.ses_ij_path = self.animal_ij_path / self.ses_path
    self.ses_s2p_path = self.animal_s2p_path / self.ses_path

    self.remote = Path(self.config_data["remote"])
    self.imaging_file_remote = self.remote / self.row["folder"].item() / self.row["scanimagefile"].item()
    self.imaging_file_local = self.ses_imaging_path / f"sub-{self.animal}_ses-{self.day}_2p.tif"

    self.event_file_remote = self.remote / "bonsai" / self.row["eventfile"].item()
    self.event_file_local = self.ses_behav_path / f"sub-{self.animal}_ses-{self.day}_events.csv"

    self.frame_file_remote = self.remote / "bonsai" / self.row["framefile"].item()
    self.frame_file_local = self.ses_behav_path / f"sub-{self.animal}_ses-{self.day}_frames.csv"

    self.final_ses_s2p_path = self.project_dir / "processeddata" / "proc_s2p" / f"sub-{self.animal}" / f"ses-{self.day}"

  def do_suite2p_files_exist(self):
    if os.path.isdir(self.final_ses_s2p_path):
        if not self.check_existing_files(self.final_ses_s2p_path):
            self.logger.info("Suite2p analysis files exist. If you want to re-analyze then either use the overwrite option or delete suite2p analysis files.")
            return True
        else:
           return False
    else:
        return False

  def check_existing_files(self, path_to_check):
    # returns True if it's fine to go ahead and perform analysis
    if len(os.listdir(path_to_check)) > 0:
        if self.overwrite == False:
            self.logger.info(f"Files found in {path_to_check}. If you want to re-download or re-analyze then run the command again with the -o option.")
            return False
        else:
            i = input("Overwrite option is selected. Do you want to analyze again? (y/N)")
            if i != "y":
                return False
            else:
                return True
    else:
        return True

  def make_session_dirs(self):
    for path in [self.ses_imaging_path, self.ses_behav_path, self.ses_ij_path, self.ses_s2p_path]:
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)

  def get_behav(self):
    self.logger.info("Downloading behavioral data...")
    self.path_to_azcopy = self.config_data["path_to_azcopy"]

    subprocess.call("{} cp {} {}".format(self.path_to_azcopy, self.event_file_remote, self.event_file_local), shell=True)
    # subprocess.call("{} cp {} {}".format(path_to_azcopy, frame_file_remote, frame_file_local), shell=True)
    # subprocess.call("{} cp {} {}".format(path_to_azcopy, lick_file_remote, lick_file_local), shell=True)

  
  def get_data(self):
    if not self.check_existing_files(self.ses_imaging_path):
        return

    self.logger.info("Downloading imaging data...")
    self.path_to_azcopy = self.config_data["path_to_azcopy"]

    azcopy_command = "{} cp {}.tif {}".format(self.path_to_azcopy, self.imaging_file_remote, self.imaging_file_local)
    self.logger.info(f"Trying this... {azcopy_command}")

    subprocess.call(azcopy_command, shell=True)
    if not os.path.exists(self.imaging_file_local):
        self.logger.debug("Failed to get file using azcopy. Check azcopy log.")

  def imagej_zproject(self):
    if not self.check_existing_files(self.ses_ij_path):
        return
    self.logger.info("Processing with ImageJ...")
    self.path_to_imagej = self.config_data["path_to_imagej"]
    proj = self.config_data["imagej_settings"]["projection"]
    z = self.config_data["imagej_settings"]["zplanes"]
    chunks = self.config_data["imagej_settings"]["framesperchunk"]

    subprocess.call(f"{self.path_to_imagej} -macro split_2p_tiff.ijm '{self.imaging_file_local}, {self.ses_ij_path}, {proj}, {chunks}, {z}' -batch ", shell=True)

    if self.delete_intermediates:
        self.logger.info("Delete intermediates selected so removing {}".format(self.ses_imaging_path))
        shutil.rmtree(self.ses_imaging_path)

  def run_suite2p(self):
    if not self.check_existing_files(self.ses_s2p_path):
        return
    self.logger.info("Processing with suite2p...")
    db = {'data_path': [self.ses_ij_path]}
    ops = default_ops()
    ops["save_path0"] = self.ses_s2p_path
    ops["anatomical_only"] = 3
    ops["diameter"] = 15
            
    try:
        run_s2p(ops=ops,db=db)
    except:
        self.logger.warning("Suite2p has failed. Continuing to next session.")
        shutil.rmtree(self.ses_ij_path)
        subprocess.call("trash-empty", shell=True)
        return
    
    if self.delete_intermediates:
        self.logger.info("Delete intermediates selected so removing {}".format(self.ses_ij_path))
        shutil.rmtree(self.ses_ij_path)

  def copy_from_fast_disk(self):
    os.makedirs(self.final_ses_s2p_path, exist_ok=True)

    subprocess.call("cp {} {} -r".format(self.ses_s2p_path / "suite2p",
                                         self.final_ses_s2p_path), shell=True)

    self.logger.info("Removing files from fast disk {}")
    shutil.rmtree(self.path_processed)
    shutil.rmtree(self.path_raw)

    self.logger.info("Emptying trash...")
    subprocess.call("trash-empty", shell=True)

def get_session_string_from_df(row):
    day = str(int(row['day'].item())).zfill(3)
    date_prefix = "ses-{}".format(day)
    date_obj = datetime.strptime(row["date"].item(), "%d/%m/%Y")
    date_suffix = date_obj.strftime("%Y%m%d")
    return date_prefix + "-" + date_suffix


    
def setup_logger(project_dir):
    """Sets up logging by creating a logger object and making a directory if needed.

    Use by calling logger.info() or logger.debug()

    Args:
        project_dir (Str or Path object): Path to folder where log directory will be created.

    Returns:
        logger: Object allowing lines to be added to log. 
    """
    if type(project_dir) == "str":
        project_dir = Path(project_dir)

    logdir = project_dir / "log"
    
    if not os.path.isdir(logdir):
        os.mkdir(logdir)

    ## setting up logger
    logfile = logdir / "{}.log".format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

    logger = logging.getLogger(logfile.as_posix())
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

    return logger