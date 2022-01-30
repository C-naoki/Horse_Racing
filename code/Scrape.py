import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import module as m
import module._class as c
import _dat
from environment.variables import *

import pandas as pd
year = "2022"
race_id_list = {}
for place in range(1, 11):
    race_id_place = {}
    for kai in range(1, 13):
        race_id_kai = []
        for day in range(1, 13):
            for r in range(1, 13):
                race_id = year + str(place).zfill(2) + str(kai).zfill(2) + str(day).zfill(2) + str(r).zfill(2)
                race_id_kai.append(race_id)
        race_id_place[kai] = race_id_kai
    race_id_list[place] = race_id_place

# Resultsのスクレイピング
new_race_results = c.Results.scrape(race_id_list,
                                    pre_race_results=_dat.race_results[year]
                                    )
print(new_race_results)
new_race_results.to_pickle("../_dat/train_data/"+year+"/race_results.pickle")
new_horse_id_list = new_race_results['horse_id'].unique()

# Pedsのスクレイピング
new_ped_results = c.Peds.scrape(new_horse_id_list,
                                pre_ped_results=_dat.ped_results[year]
                                )
print(new_ped_results)
new_ped_results.to_pickle("../_dat/train_data/"+year+"/ped_results.pickle")

# horse_resultsのスクレイピング
new_horse_results = c.HorseResults.scrape(new_horse_id_list,
                                        pre_horse_results=_dat.horse_results[year]
                                        )
print(new_horse_results)
new_horse_results.to_pickle("../_dat/train_data/"+year+"/horse_results.pickle")

# return_tablesのスクレイピング
new_return_tables, _ = c.Return.scrape(race_id_list,
                                    pre_return_tables=_dat.return_tables[year]
                                    )
print(new_return_tables)
new_return_tables.to_pickle("../_dat/train_data/"+year+"/return_tables.pickle")

m.update_data(_dat.race_results["overall"], _dat.race_results["2022"]).to_pickle("../_dat/train_data/overall/race_results.pickle")
m.update_data(_dat.horse_results["overall"], _dat.horse_results["2022"]).to_pickle("../_dat/train_data/overall/horse_results.pickle")
m.update_data(_dat.ped_results["overall"], _dat.ped_results["2022"]).to_pickle("../_dat/train_data/overall/ped_results.pickle")
m.update_data(_dat.return_tables["overall"], _dat.return_tables["2022"]).to_pickle("../_dat/train_data/overall/return_tables.pickle")