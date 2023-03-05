import logging
import sys

# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

def create_logger():
    """
    Create logger which will stream logs to console
    """

    logger = logging.getLogger()
    logger.handlers = []
    sh = logging.StreamHandler(stream=sys.stderr)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    logger.setLevel(logging.INFO)
    
    return logger


def create_logger_to_file(file_path):
    """
    Add file to logger so that logs output to file path provided as well as the console

    file_path: full file path to where logs are output
    return: logger
    """

    logger = create_logger()
    sh_file = logging.FileHandler(file_path, mode="w")
    sh_file.setFormatter(formatter)
    logger.addHandler(sh_file)

    return logger
