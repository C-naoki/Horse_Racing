import sys
sys.dont_write_bytecode = True

import module as m
import module._class as c
import _dat
from environment.variables import *
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re

# print(_dat.ped_results_2021.index)
# print(_dat.horse_id_list_2021)
# print(_dat.new_race_results)
# _dat.new_race_results.to_pickle("_dat/pickle/2021/race_results.pickle")
# _dat.new_horse_results.to_pickle("_dat/pickle/2021/horse_results.pickle")
# _dat.new_ped_results.to_pickle("_dat/pickle/2021/ped_results.pickle")
# _dat.new_return_tables.to_pickle("_dat/pickle/2021/return_tables.pickle")

# m.update_data(_dat.race_results, _dat.race_results_2021).to_pickle("_dat/pickle/overall/race_results.pickle")
# m.update_data(_dat.horse_results, _dat.horse_results_2021).to_pickle("_dat/pickle/overall/horse_results.pickle")
# m.update_data(_dat.ped_results, _dat.ped_results_2021).to_pickle("_dat/pickle/overall/ped_results.pickle")
# m.update_data(_dat.return_tables, _dat.return_tables_2021).to_pickle("_dat/pickle/overall/return_tables.pickle")