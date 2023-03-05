import requests
import os
from bs4 import BeautifulSoup
import json
from pathlib import Path
from utility.logging_utils import create_logger


logger = create_logger()


def create_directory(
        file_path: str,
        is_file: bool=True
):
    """
    Check if directory exists and create it if it doesn't exist

    :param file_path: full path to a file
    :param is_file: True if file_path includes the actual file name
                False if file_path is just the path of the directory (no file name included)
    :return: None
    """

    if is_file is True:
        file_path_split = os.path.normpath(file_path).split(os.path.sep)
        logger.info(f"file_path_split = {file_path_split}")
        if len(file_path_split) > 1:
            # Set the file_path to be the directory of the path received
            file_path = "/".join(file_path_split[:-1])
        else:
            logger.info("file_path is current directory")
            return
    
    if not os.path.exists(file_path):
        logger.info(f"Created path at : {file_path}")
        os.makedirs(file_path)
    else:
        logger.info(f"Path already exists : {file_path}")


def extract_from_url(
        url: str,
        file_path: str
):
    """
    Call the url and save to file

    :param url: url of the website to be called by requests
    :param file_path: full name of the file path where extracted data is to be saved
    :return: True
    """

    create_directory(file_path)

    logger.info(f"Calling url : {url}")
    page = requests.get(url)

    with open(file_path, "w") as f:
        f.write(page.text)
        logger.info(f"HTML written to {file_path}")

    return True


def read_data(
        file_path: str
):
    """

    :param file_path: full name of file path where the file to be read resides
    :return: html file parsed with Beautiful Soup
    """

    with open(file_path, "r") as f:
        logger.info(f"Reading data from : {file_path}")
        html = f.read()

    return BeautifulSoup(str.encode(html), "html.parser")


def read_json_file(file_path: str):
    """
    Read json file and return data

    :param file_path: full file path of the json file (directory + file name)
    :return: contents of the file
    """

    with open(file_path) as f:
        logger.info(f"Reading JSON from : {file_path}")
        data = json.loads(f.read())

    return data


def get_data_directory(
        website: str,
        sport: str,
        uid_timestamp: int
):
    """
    Retrieve the data directories for extracted data files and csv outputs

    :param extracted_data_files_directory: directory where extracted data files are stored
    :return: data directories for extracted data files and csv outputs
    """

    sports_arbitrage_data_directory = os.path.join(os.path.expanduser('~'), "sports_arbitrage_data")

    extracted_data_files_directory = os.path.join(sports_arbitrage_data_directory, f"{website}/{sport}/{uid_timestamp}")
    output_directory = os.path.join(sports_arbitrage_data_directory, "output")

    create_directory(
        extracted_data_files_directory, 
        False
    
    )
    create_directory(
        output_directory, 
        False
    )

    return extracted_data_files_directory, output_directory