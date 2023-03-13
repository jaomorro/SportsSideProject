import requests
from datetime import datetime, timedelta
import time
import pandas as pd
import os
import random
from pathlib import Path
from utility.helper_functions import extract_from_url, read_json_file
from utility.logging_utils import create_logger
import argparse
from utility.sports_betting import SportsBetting


logger = create_logger()


class Bovada(SportsBetting):
    def __init__(
            self, 
            sport: str
        ):
        super().__init__(sport)
        self.website = "bovada"


    def extract_bet_data_from_json(
            self,
            bets_json_data: dict,
            extracted_data_files_directory: str
    ):
        """
        Parse the json with betting lines

        :param bets_json_data: json from bovada API to be parsed
        :param extracted_data_files_directory: directory where extracted data files are stored
        :return: two lists - one with metadata about the games and one for all the bet info
        """

        data_records = []
        event_list = []

        logger.info(f"Length of bets list = {len(bets_json_data)}")
        for i in range(len(bets_json_data)):
            logger.info(f'i = {i}, {bets_json_data[i]["path"][0]["link"]}')
            if bets_json_data[i]["path"][0]["link"] == f"/{self.sport}/nba":
                competition = bets_json_data[i]["path"][0]["link"].split("/")[-1]
                logger.info(f'Number of events = {len(bets_json_data[i]["events"])}')
                for event in bets_json_data[i]["events"]:
                    event_id = event["id"]
                    event_date = datetime.fromtimestamp(event["startTime"]/1000).strftime('%Y-%m-%d')
                    is_live = event["displayGroups"][0]["markets"][0]["period"]["live"]
                    logger.info(f"is_live = {is_live} : {event_id, event_date, competition}")
                    if is_live == False:

                        for teams in event["competitors"]:
                            if teams["home"] is True:
                                home_team = teams["name"]
                            else:
                                away_team = teams["name"]

                        event_record = [event_id, event_date, competition, away_team, home_team]
                        logger.info(f"event_record : {event_record}")
                        event_list.append(event_record)

                        for dg in event["displayGroups"]:
                            if dg["description"] in ("Game Lines", "Alternate Lines"):
                                for market in dg["markets"]:

                                    if market["period"]["description"] == "Game" and is_live is False:
                                        insert_record = False

                                        if dg["description"] == "Game Lines":
                                            logger.info("Game Lines exist")
                                            if market["period"]["description"] == "Game" and \
                                                ((market["descriptionKey"] == "Head To Head" and market["description"] == "Moneyline") \
                                                or (market["descriptionKey"] == "Main Dynamic Over/Under" and market["description"] == "Total") \
                                                or (market["descriptionKey"] == "Main Dynamic Asian Runline" and market["description"] == "Runline")):

                                                insert_record = True
                                                if market["description"] == "Moneyline":  # Game lines Moneyline
                                                    bet_type = "moneyline"
                                                elif market["description"] == "Total":  # Game lines O/U
                                                    bet_type = "over_under"
                                                elif market["description"] == "Runline":  # Game lines handicap
                                                    bet_type = "handicap"

                                        elif dg["description"] == "Alternate Lines":
                                            logger.info("Alternate Lines exist")
                                            if (market["descriptionKey"] == "Total Runs O/U" and market["description"] == "Total Runs O/U") \
                                                    or (market["descriptionKey"] == "Handicap - Asian" and market["description"] == "Spread"):
                                                # print("alternate lines")
                                                # print(market)
                                                insert_record = True
                                                if market["description"] == "Spread":  # Alternate handicap
                                                    bet_type = "handicap"
                                                elif market["description"] == "Total Runs O/U":  # Alternate O/U
                                                    bet_type = "over_under"

                                        logger.info(f"insert_record = {insert_record}")
                                        if insert_record is True:
                                            for line in market["outcomes"]:
                                                # Status can be O or S (based on what I've seen). No documentation but I believe O means open
                                                # Some lines will have O and S which causes dupes and the O corresponds with what I see on front-end
                                                # For example, O/U of 11.5 may have 4 records, 2 with status O and 2 with status S
                                                # We only want one of these and O appears to be the right one
                                                if line["status"] == "O":

                                                    single_line = [
                                                        self.website,
                                                        event_id,
                                                        bet_type, # bet type
                                                        None if bet_type == "over_under" else line["description"],  # team
                                                        line["price"]["american"],  # american line
                                                        line["price"]["decimal"], # decimal line
                                                        line["price"]["fractional"], # fractional line
                                                        line["price"].get("handicap",None),  # handicap_spread
                                                        line["description"].lower() if bet_type == "over_under" else None  # over_under
                                                    ]

                                                    logger.info(f"single_line = {single_line}")
                                                    data_records.append(single_line)

                            insert_record = False

        return event_list, data_records


    def create_df_bovada(
            self,
            bets_json_data: dict,
            extracted_data_files_directory: str
    ):
        """
        Create a dataframe with betting lines

        :param bets_json_data: json from bovada API to be parsed
        :param extracted_data_files_directory: directory where extracted data files are stored
        :return: dataframe with betting info
        """

        event_list, data_records = self.extract_bet_data_from_json(bets_json_data, extracted_data_files_directory)

        # Retrieve the dataframe headers
        df_headers = read_json_file(f"{Path(__file__).parents[1]}/constants/dataframe_headers.json")
        df_event_headers = df_headers["df_event_headers"]
        logger.info(f"df_event_headers = {df_event_headers}")
        df_records_headers = df_headers["df_records_headers"]
        logger.info(f"df_records_headers = {df_records_headers}")

        df_events = pd.DataFrame(data=event_list, columns=df_event_headers)
        df_records = pd.DataFrame(data=data_records, columns=df_records_headers)

        df_bovada = pd.merge(df_events, df_records, how="inner", on="event_id")

        return df_bovada


    def create_df_with_lines(
            self, 
            uid_timestamp: int=None
        ):
        """
        Create pandas dataframe of betting info

        :param uid_timestamp: YYYYMMDDHHMMSS timestamp folder that files are saved to
        :return: pandas dataframe of betting info
        """

        uid_timestamp_none = False

        if uid_timestamp is None:
            logger.info("uid_timestamp is not provided so setting it")
            uid_timestamp_none = True
            uid_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        logger.info(f"uid_timestamp = {uid_timestamp}")

        extracted_data_files_directory = self.get_data_directory(self.website, self.sport, uid_timestamp)

        logger.info(f"extracted_data_files_directory = {extracted_data_files_directory}")

        sports_betting_info = read_json_file(f"{Path(__file__).parents[1]}/constants/betting_sites_info.json")[self.website]
        website_base_url = sports_betting_info["website_base_url"]
        logger.info(f"website_base_url = {website_base_url}")

        all_games_file_name = "all_games.txt"

        if uid_timestamp_none is True:
            # If uid timestamp is not provided then call URL to get new data
            # If uid timestamp is provided, then we will be reading cached data from the directory
            #   of provided timestamp, and not calling the url

            logger.info(f"uid_timestamp_none is True so calling url")
            extract_from_url(
                url=f"{website_base_url}/{self.sport}",
                file_path=os.path.join(extracted_data_files_directory, all_games_file_name)
            )
        else:
            logger.info("uid_timestamp_none is False so NOT calling url")

        bets_json_data = read_json_file(
            file_path=os.path.join(extracted_data_files_directory, all_games_file_name)
        )

        df_bet_info = self.create_df_bovada(
            bets_json_data=bets_json_data,
            extracted_data_files_directory=extracted_data_files_directory
        )

        return df_bet_info
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--uid-timestamp", dest="uid_timestamp", required=False, type=int,
                        help="YYYYMMDDHHMMSS timestamp folder that files are saved to")
    args = parser.parse_args()
    uid_timestamp = args.uid_timestamp

    logger.info(f"UID_TIMESTAMP = {uid_timestamp}")

    bovada_basketball = Bovada("basketball")
    # output_directory = bovada_basketball.get_output_directory()

    df_bet_info = bovada_basketball.create_df_with_lines(uid_timestamp)
    df_bet_info.to_csv(os.path.join(bovada_basketball.output_directory, "bovada.csv"), index=False)