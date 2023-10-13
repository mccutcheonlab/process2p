### This file will have all the main functions and classes needed for the different types of preprocessing scripts
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# the base class used for most scripts in this package
class Preprocess():
  def __init__(self, args, logger):
    self.args = args
    self.logger = logger

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