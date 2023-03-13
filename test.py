import duckdb
import pandas as pd
import os
from utility.helper_functions import get_output_directory


def query_duckdb(query, con):
    result = con.execute(query).fetchall()
    return result


output_directory = get_output_directory()


df_bovada = pd.read_csv(os.path.join(output_directory, "bovada.csv"))
df_betfair = pd.read_csv(os.path.join(output_directory, "betfair.csv"))


con = duckdb.connect(database=':memory:')
websites = ["bovada","betfair"]
for website in websites:
    query_create_website_data = f"""
        create table {website}_data as
        select * from df_{website}
    """
    query_duckdb(query_create_website_data, con)

    result = query_duckdb(f"select count(1) from {website}_data", con)
    print(result[0][0])


query = """
    select 
        bov.event_date,
        bov.away_team,
        bov.home_team,
        bov.bet_type,
        bov.handicap_spread,
        bov.team,
        bov.decimal as decimal_bovada,
        bet.decimal as decimal_betfair
    from bovada_data as bov
    join betfair_data as bet
        on bov.home_team = bet.home_team
        and bov.away_team = bet.away_team
        and bov.event_date = bet.event_date
        and bov.bet_type = bet.bet_type
        and bov.team = bet.team
    where bov.bet_type = 'moneyline'
    and bet.bet_type = 'moneyline'

    union all

    select 
        bov.event_date,
        bov.away_team,
        bov.home_team,
        bov.bet_type,
        bov.handicap_spread,
        bov.team,
        bov.decimal as decimal_bovada,
        bet.decimal as decimal_betfair
    from bovada_data as bov
    join betfair_data as bet
        on bov.home_team = bet.home_team
        and bov.away_team = bet.away_team
        and bov.event_date = bet.event_date
        and bov.bet_type = bet.bet_type
        and bov.team = bet.team
        and bov.handicap_spread = bet.handicap_spread
    where bov.bet_type = 'handicap'
    and bet.bet_type = 'handicap'

    union all

    select 
        bov.event_date,
        bov.away_team,
        bov.home_team,
        bov.bet_type,
        bov.handicap_spread,
        bov.home_team, --over/under displayed will be based on the home team
        bov.over_under,
        bov.decimal as decimal_bovada,
        bet.decimal as decimal_betfair

    from bovada_data as bov
    join betfair_data as bet
        on bov.home_team = bet.home_team
        and bov.away_team = bet.away_team
        and bov.event_date = bet.event_date
        and bov.bet_type = case when bet.bet_type = 'over' then 'under'
                                when bet.bet_type = 'under' then 'over'
                                else 'NA' end
        and bov.team = bet.team
    where bov.bet_type = 'over_under'
    and bet.bet_type = 'over_under'
"""

(1/row['decimal_bovada_x']) + (1/row['decimal_betfair_y'])


event_date",
                                "away_team",
                                "home_team",
                                "bet_type",
                                "handicap_spread",
                                "team",
                                "over_under",
                                "website",
                                "decimal_line"