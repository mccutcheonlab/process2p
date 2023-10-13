### This script will be run from the command line when a series of individual files want to be processed
from pathlib import Path
import click
import json

from helper_fx import Preprocess, setup_logger

# figure out better way of doing command line arguments
@click.command()
@click.option("--config-file", type=str, default="config.json", help="A file containing config options. If not present are parsed correctly the script will exit.")
@click.option("--get-metafile", type=bool, default=False)
def run_processing(config_file, get_metafile):
    print(f"The config file is {config_file}")

    f = open(config_file)
    config_data = json.load(f)
    print(config_data)

    project_dir = Path(config_data["path_to_project_dir"])

    logger = setup_logger(project_dir)

    if get_metafile:
        print("Fetching metafile")
        # code for getting metafile using info from config file (project dir)



if __name__ == "__main__":
    print("processing stuff")

    run_processing()

    # parse args
    # include config file as option and if not included look for config.json
    # exit if no config file found



    # read config file

    # logger = setup_logger(project_dir)



    # loop through sessions to analyze adding jobs to worker
    ## include checks for existing data

    # execute queues






