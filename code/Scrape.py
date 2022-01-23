import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import module as m
import module._class as c
import _dat
from environment.variables import *

import pandas as pd

race_id_list_2022 = {}
for place in range(1, 11, 1):
    race_id_place = []
    for kai in range(1, 13, 1):
        for day in range(1, 13, 1):
            for r in range(1, 13, 1):
                race_id = "2022" + str(place).zfill(2) + str(kai).zfill(2) + str(day).zfill(2) + str(r).zfill(2)
                race_id_place.append(race_id)
    race_id_list_2022[place] = race_id_place

# Resultsのスクレイピング
new_race_results = c.Results.scrape(race_id_list_2022,
                                    pre_race_results=_dat.race_results_2022
                                    )
print(new_race_results)
new_race_results.to_pickle("../_dat/train_data/2022/race_results.pickle")
horse_id_list_2022 = new_race_results['horse_id'].unique()

# Pedsのスクレイピング
new_ped_results = c.Peds.scrape(horse_id_list_2022,
                                pre_ped_results=_dat.ped_results_2022
                                )
print(new_ped_results)
new_ped_results.to_pickle("../_dat/train_data/2022/ped_results.pickle")

# horse_resultsのスクレイピング
new_horse_results = c.HorseResults.scrape(horse_id_list_2022,
                                        pre_horse_results=_dat.horse_results_2022
                                        )
print(new_horse_results)
new_horse_results.to_pickle("../_dat/train_data/2022/horse_results.pickle")

# return_tablesのスクレイピング
new_return_tables, _ = c.Return.scrape(race_id_list_2022,
                                    pre_return_tables=_dat.return_tables_2022
                                    )
print(new_return_tables)
new_return_tables.to_pickle("../_dat/train_data/2022/return_tables.pickle")

m.update_data(_dat.race_results, _dat.race_results_2022).to_pickle("../_dat/train_data/overall/race_results.pickle")
m.update_data(_dat.horse_results, _dat.horse_results_2022).to_pickle("../_dat/train_data/overall/horse_results.pickle")
m.update_data(_dat.ped_results, _dat.ped_results_2022).to_pickle("../_dat/train_data/overall/ped_results.pickle")
m.update_data(_dat.return_tables, _dat.return_tables_2022).to_pickle("../_dat/train_data/overall/return_tables.pickle")