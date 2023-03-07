import logging
import sys

# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

def create_logger(
        file_path: str=None
):
    """
    Create logger which will stream logs to console

    file_path: full file path to where logs are output
    return: logger
    """

    logger = logging.getLogger()
    logger.handlers = []
    sh = logging.StreamHandler(stream=sys.stderr)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    if file_path is not None:
        sh_file = logging.FileHandler(file_path, mode="w")
        sh_file.setFormatter(formatter)
        logger.addHandler(sh_file)

    logger.setLevel(logging.INFO)
    
    return logger
