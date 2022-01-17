import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import module as m
import module._class as c
import _dat
from environment.variables import *

import pandas as pd

race_id_list_2021 = []
for place in range(1, 11, 1):
    for kai in range(1, 13, 1):
        for day in range(1, 13, 1):
            for r in range(1, 13, 1):
                race_id = "2021" + str(place).zfill(2) + str(kai).zfill(2) + str(day).zfill(2) + str(r).zfill(2)
                race_id_list_2021.append(race_id)

# # Resultsのスクレイピング
# new_race_results = c.Results.scrape(race_id_list_2021,
#                                     pre_race_results=_dat.race_results_2021
#                                     )
# print(new_race_results.shape)
# print(_dat.race_results_2021.shape)
# new_race_results.to_pickle("_dat/pickle/2021/race_results.pickle")

# # Pedsのスクレイピング
# new_ped_results = c.Peds.scrape(_dat.horse_id_list_2021,
#                                 pre_ped_results=_dat.ped_results_2021
#                                 )
# print(new_ped_results)
# # print(_dat.ped_results_2021.shape)
# new_ped_results.to_pickle("_dat/pickle/2021/ped_results.pickle")

# # horse_resultsのスクレイピング
# new_horse_results = c.HorseResults.scrape(_dat.horse_id_list_2021,
#                                         pre_horse_results=_dat.horse_results_2021
#                                         )
# print(new_horse_results.shape)
# print(_dat.horse_results_2021.shape)
# new_horse_results.to_pickle("_dat/pickle/2021/horse_results.pickle")

# # return_tablesのスクレイピング
# new_return_tables, _ = c.Return.scrape(race_id_list_2021,
#                                     pre_return_tables=_dat.return_tables_2021
#                                     )
# print(new_return_tables.shape)
# print(_dat.return_tables_2021.shape)
# new_return_tables.to_pickle("_dat/pickle/2021/return_tables.pickle")