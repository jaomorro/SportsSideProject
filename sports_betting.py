import os
from pathlib import Path
import argparse
import requests
from datetime import datetime
from utility.helper_functions import read_json_file
from utility.logging_utils import create_logger
from bovada.bovada_basketball import create_df_with_lines as bovada_create_df_with_lines
from betfair.betfair_basketball import create_df_with_lines as betfair_create_df_with_lines

logger = create_logger()



def main(
        website_filter: str=None,
        uid_timestamp: str=None
):
    """
    Loop through websites/sports and call API for each website/sport

    :param website: website to call API for
    :param uid_timestamp: specific timestamp from a prior run to load data for.
        When this is provided, new data will not be extracted, rather data will be read
            from the folder with the given website / timestamp
        This can be used for testing / when you don't want to make an actual call to the
            given website, so instead you just read in the data from a prior run
    :return: None
    """

    sports_betting_info = read_json_file(f"{Path(__file__).parents[0]}/constants/betting_sites_info.json")

    for website, website_info in sports_betting_info.items():

        if website_filter is not None:
            if website != website_filter:
                print(f"website = {website} so skipping!!")
                continue

        logger.info(f"website = {website}")
        website_base_url = website_info["website_base_url"]
        logger.info(f"base_url = {website_base_url}")
        if uid_timestamp is None:
            uid_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info(f"uid_timestamp = {uid_timestamp}")

        for sport in website_info["sports"]:
            logger.info(f"sport = {sport}")
            extracted_data_files_directory = f"{Path(__file__).parents[0]}/extracted_data_files/{website}/{sport}/{uid_timestamp}"
            logger.info(f"extracted_data_files_directory = {extracted_data_files_directory}")

            if website == "bovada":
                bovada_create_df_with_lines(extracted_data_files_directory)
            elif website == "betfair":
                betfair_create_df_with_lines(extracted_data_files_directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--website", dest="website_filter", required=False, type=str,
                        help="Website to pull data from")
    parser.add_argument("--uid-timestamp", dest="uid_timestamp", required=False, type=int,
                        help="YYYYMMDDHHMMSS timestamp folder that files are saved to")
    args = parser.parse_args()
    website_filter = args.website_filter
    if args.uid_timestamp is None:
        uid_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    else:
        uid_timestamp = args.uid_timestamp

    logger.info(f"UID_TIMESTAMP = {uid_timestamp}")

    main(website_filter, uid_timestamp)