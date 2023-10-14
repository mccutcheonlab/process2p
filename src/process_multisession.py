### This script will be run from the command line to get cross-session registration
import sys
import os
from pathlib import Path
import click
import json
import subprocess

from helper_fx import Preprocess, setup_logger

@click.command()
@click.option("--config-file", type=str, default="config.json", help="A file containing config options. If not present are parsed correctly the script will exit.")
@click.option("--get-metafile", "-m", type=bool, is_flag=True, help="If selected attempts to download metafile from Azure")
@click.option("--animals", "-a", type=str, default="", help="List of animals to be processed")
@click.option("--dates", "-d", type=str, default="", help="List of dates to be processed")
@click.option("--use-fast-dir", "-f", type=bool, is_flag=True, help="Path to fast directory, important when using with a VM and file share to speed up")
@click.option("--overwrite", type=bool, is_flag=True, help="Choose if you want the option to overwrite files")
@click.option("--delete_intermediates", "-X", type=bool, is_flag=True, help="When selected, will delete raw data and imageJ files")
def run_processing(config_file, get_metafile, animals, dates, use_fast_dir, overwrite, delete_intermediates):
    print("run")

        # finds and opens config file
    print(f"The config file is {config_file}")
    f = open(config_file)
    config_data = json.load(f)

    # Initializes class
    preprocess = Preprocess(config_data, use_fast_dir, overwrite, delete_intermediates)

    # Sets project_dir (and create if does not exist)
    preprocess.set_project_dir()

    # Sets up logger and make directory if needed
    preprocess.set_logger()

    # Gets metafile if requested
    if get_metafile:
        preprocess.get_metafile()
    
        # Reads metafile in
    preprocess.read_metafile()

    # Parses animals and check to make sure only one is given
    preprocess.parse_animals(animals)
    if len(preprocess.animals) > 1:
        preprocess.logger.info("Exiting as more than one animal given. This script can only process one at a time")
        sys.exit(2)

    # Parses dates and checks to make sure >1 given
    preprocess.parse_dates(dates)
    if len(preprocess.dates) < 2:
        preprocess.logger.info("Exiting as only one date given. Script is designed to look at 2 or more sessions")
        sys.exit(2)

    # Sets up paths and directories
    preprocess.define_root()
    preprocess.define_nwb_paths()
    preprocess.define_multisession_paths() # need to define multiple paths for rawdata and imagej data using dates


# need to decide on file structure
# function to create 
# then look for existing registered tiffs



if __name__ == "__main__":
    print("processing stuff")
    run_processing()