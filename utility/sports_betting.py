from abc import ABC, abstractmethod
from datetime import datetime
import os
from utility.helper_functions import create_directory


class SportsBetting(ABC):
    def __init__(
            self, 
            sport: str
    ):
        self.sport = sport
        self.sports_arbitrage_data_directory = os.path.join(os.path.expanduser('~'), "sports_arbitrage_data")
        

    def get_data_directory(
            self,
            website: str,
            sport: str,
            uid_timestamp: int
    ):
        """
        Retrieve the data directories for extracted data files

        :return: data directory for extracted data files
        """

        # sports_arbitrage_data_directory = os.path.join(os.path.expanduser('~'), "sports_arbitrage_data")

        extracted_data_files_directory = os.path.join(self.sports_arbitrage_data_directory, f"{website}/{sport}/{uid_timestamp}")

        create_directory(
            extracted_data_files_directory, 
            False
        
        )

        return extracted_data_files_directory
    

    def get_output_directory(
            self
    ):
        """
        Retrieve the data directory for csv outputs

        :return: data directory for csv outputs
        """

        # sports_arbitrage_data_directory = os.path.join(os.path.expanduser('~'), "sports_arbitrage_data")

        output_directory = os.path.join(self.sports_arbitrage_data_directory, "output")

        create_directory(
            output_directory, 
            False
        )

        return output_directory


    @abstractmethod
    def create_df_with_lines(self):
        pass
