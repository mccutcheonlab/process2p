### This script will be run from the command line when a series of individual files want to be processed
import sys
import os
from pathlib import Path
import click
import json
import subprocess

from helper_fx import Preprocess, setup_logger

# figure out better way of doing command line arguments
@click.command()
@click.option("--config-file", type=str, default="config.json", help="A file containing config options. If not present are parsed correctly the script will exit.")
@click.option("--get-metafile", "-m", type=bool, is_flag=True, help="If selected attempts to download metafile from Azure")
@click.option("--animals", "-a", type=str, default="", help="List of animals to be processed")
@click.option("--dates", "-d", type=str, default="", help="List of dates to be processed")
@click.option("--use-fast-dir", "-f", type=bool, is_flag=True, help="Path to fast directory, important when using with a VM and file share to speed up")
@click.option("--overwrite", type=bool, is_flag=True, help="Choose if you want the option to overwrite files")
@click.option("--get-behav", "-b", type=bool, is_flag=True, help="To download behavioral data from Azure")
@click.option("--get-data", "-g", type=bool, is_flag=True, help="To download imaging data from Azure")
@click.option("--imagej-z", "-i", type=bool, is_flag=True, help="Processes with image j and does z projection")
@click.option("--suite2p", "-s", type=bool, is_flag=True, help="Runs suite2p on processed tifs")
@click.option("--delete_intermediates", "-X", type=bool, is_flag=True, help="When selected, will delete raw data and imageJ files")
def run_processing(config_file, get_metafile, animals, dates, use_fast_dir, overwrite, get_behav, get_data, imagej_z, suite2p, delete_intermediates):

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

    # Parses animals
    preprocess.parse_animals(animals)

    # Parses dates
    preprocess.parse_dates(dates)

    # Sets up paths and directories
    preprocess.define_root()
    preprocess.define_nwb_paths()

    # Start looping through animals
    preprocess.loop_animals(get_behav, get_data, imagej_z, suite2p)

if __name__ == "__main__":
    print("processing stuff")
    run_processing()







