import requests
from datetime import datetime, timedelta
import time
import pandas as pd
import os
import random
from pathlib import Path
from utility.helper_functions import extract_from_url, read_html_data, read_json_file, get_data_directory
from utility.logging_utils import create_logger
import argparse


logger = create_logger()

WEBSITE = "betfair"
SPORT = "basketball"


def bet_type_finder(
        single_event_soup: str,
        bet_type: str,
        event_id: list
):
    """
    Find handicap and price info for given bet type

    :param single_event_soup: html for a given game
    :param bet_type: class within the html to search for
    :return: list of lists where each list is a record for the given bet type
    """

    list_of_bet_info = []
    for elem in single_event_soup.select(f'div[class*="{bet_type["bet_type"]}-"]'):
        logger.info(f"Parsing the element")
        logger.info(f"\tevent_id = {event_id}")
        logger.info(f"\tbet_type = {bet_type}")

        # Contains total runs over/under and the spread
        ui_runner_handicap = [i.text for i in elem.find_all("span", class_="ui-runner-handicap")]
        logger.info(f"\tui_runner_handicap = {ui_runner_handicap}")

        # Contains total score over/under, spread and moneyline prices
        ui_runner_price = [i.text.strip("\n") for i in elem.find_all("span", class_="ui-runner-price")]
        logger.info(f"\tui_runner_price = {ui_runner_price}")

        # Contains teams
        teams = [i.text for i in elem.find_all("span", class_="runner-name")]
        logger.info(f"\tteams = {teams}")

        for i in range(2):
            # 0 is away team and 1 is home team
            single_line = [
                WEBSITE,
                event_id,
                bet_type["bet_type_normalized"], # bet_type
                teams[i] if bet_type["has_teams"] is True else None, # team
                None,  # american line
                ui_runner_price[i],  # decimal line
                None,  # fractional line
                ui_runner_handicap[i] if bet_type["has_handicap"] is True else None,  # handicap_spread
                teams[i].lower() if bet_type["has_teams"] is False else None # over_under
            ]
            logger.info(f"\tsingle_line = {single_line}")
            list_of_bet_info.append(single_line)

        # logger.info(list_of_bet_info)
        return list_of_bet_info


def extract_bet_data_from_html(
        elements,
        extracted_data_files_directory: str,
        website_base_url: str
):
    """

    :param elements: HTML li elements from betfair website to be parsed
    :param extracted_data_files_directory: directory where extracted data files are stored
    param website_base_url: base url for the website
    :return: two lists - one with metadata about the games and one for all the bet info
    """

    search_elems = read_json_file(f"{Path(__file__).parents[1]}/constants/betfair_search_elems.json")["search_elems"]
    logger.info(f"search_elems = {search_elems}")

    event_list = []
    data_records = []
    for elem in elements:
        # Find the event date
        # If event date element does not exist then that means the event is "IN PLAY" so we want to skip
        event_date_element = elem.find("span", class_="date ui-countdown")
        if event_date_element is not None:
            if "Tomorrow" in event_date_element.text:
                event_date = str(datetime.today().date() + timedelta(days=1))
            else:
                event_date = str(datetime.today().date())

            event_info = elem.find("div", class_="avb-col avb-col-runners")
            event_id_href = event_info.find_all("a", href=True)

            event_info = elem.find("div", class_="avb-col avb-col-runners")
            event_id_href = event_info.find_all("a", href=True)
            for e in event_id_href:
                if e.get("data-competition") is not None:
                    data_competition = e["data-competition"]
                else:
                    data_competition = None

                if data_competition in ["NBA"]:
                    if e.get("href") is not None:
                        event_href = e["href"]
                        event_id = e["href"].split("/")[-1]
                    if e.get("data-event") is not None:
                        away_team = e["data-event"].split("@")[0].strip()
                        home_team = e["data-event"].split("@")[1].strip()

                    logger.info(f"event_info = {event_id, event_date, data_competition, away_team, home_team}")

                    event_list.append([
                        event_id,
                        event_date,
                        data_competition,
                        away_team,
                        home_team
                    ])
                    file_name = f"{event_date.replace('-', '')}-{event_id}-{away_team}-{home_team}"

                    sleep_seconds = random.randrange(10, 20)
                    logger.info(f"Sleeping for {sleep_seconds} seconds...")
                    time.sleep(sleep_seconds)
                    extract_from_url(
                        url=f"{website_base_url}{event_href}",
                        file_path=os.path.join(extracted_data_files_directory, file_name)
                    )

                    single_event_soup = read_html_data(
                        file_path=os.path.join(extracted_data_files_directory, file_name)
                    )

                    for search_elem in search_elems:
                        logger.info(f"search_elem = {search_elem}")
                        try:
                            data_records.extend(
                                bet_type_finder(
                                    single_event_soup,
                                    search_elem,
                                    event_id
                                ))
                        except Exception as e:
                            logger.info(f"Exception : {e}")
                            logger.info(f"Bad {search_elem} record")
                            continue

    return event_list, data_records


def create_df_betfair(
        all_games_soup,
        extracted_data_files_directory: str,
        website_base_url: str
):
    """
    Create a dataframe with betting info

    :param all_games_soup: Beautiful soup of games to be parsed / included in dataframe
    :param extracted_data_files_directory: directory where extracted data files are stored
    :param website_base_url: base url for the website
    :return: dataframe with betting info
    """

    elements = all_games_soup.find_all("li", class_="com-coupon-line-new-layout")
    event_list, data_records = extract_bet_data_from_html(elements, extracted_data_files_directory, website_base_url)

    # Retrieve the dataframe headers
    df_headers = read_json_file(f"{Path(__file__).parents[1]}/constants/dataframe_headers.json")
    df_event_headers = df_headers["df_event_headers"]
    logger.info(f"df_event_headers = {df_event_headers}")
    df_records_headers = df_headers["df_records_headers"]
    logger.info(f"df_records_headers = {df_records_headers}")

    df_events = pd.DataFrame(data=event_list, columns=df_event_headers)
    df_records = pd.DataFrame(data=data_records, columns=df_records_headers)

    df_betfair = pd.merge(df_events, df_records, how="inner", on="event_id")

    return df_betfair


def create_df_with_lines(extracted_data_files_directory: str):
    """
    Create pandas dataframe of betting info

    :param extracted_data_files_directory: directory where extracted data files are stored
    :return: pandas dataframe of betting info
    """

    sports_betting_info = read_json_file(f"{Path(__file__).parents[1]}/constants/betting_sites_info.json")[WEBSITE]
    website_base_url = sports_betting_info["website_base_url"]

    all_games_file_name = "all_games.txt"

    extract_from_url(
        url=f"{website_base_url}/sport/{SPORT}/nba/10547864",
        file_path=os.path.join(extracted_data_files_directory, all_games_file_name)
    )

    all_games_soup = read_html_data(
        file_path=os.path.join(extracted_data_files_directory, all_games_file_name)
    )

    df_bet_info = create_df_betfair(
        all_games_soup=all_games_soup,
        extracted_data_files_directory=extracted_data_files_directory,
        website_base_url=website_base_url
    )

    return df_bet_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--uid-timestamp", dest="uid_timestamp", required=False, type=int,
                        help="YYYYMMDDHHMMSS timestamp folder that files are saved to")
    args = parser.parse_args()
    if args.uid_timestamp is None:
        uid_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    else:
        uid_timestamp = args.uid_timestamp

    extracted_data_files_directory, output_directory = get_data_directory(WEBSITE, SPORT, uid_timestamp)

    logger.info(f"UID_TIMESTAMP = {uid_timestamp}")
    logger.info(f"EXTRACTED_DATA_FILES_DIRECTORY = {extracted_data_files_directory}")

    df_bet_info = create_df_with_lines(extracted_data_files_directory)
    df_bet_info.to_csv(os.path.join(output_directory, "betfair.csv"), index=False)