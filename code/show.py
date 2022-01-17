import module as m
import module._class as c
import _dat
from environment.variables import *

import pandas as pd
import numpy as np
import requests
import re
import datetime

from bs4 import BeautifulSoup
from urllib.request import urlopen
from tabulate import tabulate

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

# m.update_data(m.update_data(m.update_data(m.update_data(_dat.ped_results_2017, _dat.ped_results_2018), _dat.ped_results_2019), _dat.ped_results_2020), _dat.ped_results_2021).to_pickle("_dat/pickle/overall/ped_results.pickle")

# venue_id_list = ["2022060101", "2022070101"] # race_id_list
# # race_id_list = ["2022060101" + str(i).zfill(2) for i in range(1, 13)]
# today_return_tables = c.Return.scrape(["202206010101"])
# rt = c.Return(today_return_tables)
# print(rt.fukusho)

# url = "https://db.netkeiba.com/race/202206010101"
# f = urlopen(url)
# html = f.read()
# html = html.replace(b'<br />', b'br')
# dfs1 = pd.read_html(html, match='単勝')[1]
# dfs2 = pd.read_html(html, match='三連複')[0]
# df_arrival = pd.read_html(html, match='単勝')[0].iloc[:,[0,2]]
# df = pd.concat([dfs1, dfs2])
# df.index = ["202206010101"] * len(df)
# df_arrival.index = ["202206010101"] * len(df_arrival)
# df_arrival.columns = ["着順", "馬番"]
# print(df_arrival[df_arrival["着順"]==1]["馬番"])

# print(tabulate(_dat.horse_results, _dat.horse_results.columns, tablefmt="presto", showindex=True))
r = c.Results(_dat.race_results)
# 前処理
r.preprocessing()
# 馬の過去成績の追加
hr = c.HorseResults(_dat.horse_results)
r.merge_horse_results(hr)
# 5世代分の血統データの追加
p = c.Peds(_dat.ped_results)
p.encode()
r.merge_peds(p.peds_e)
# カテゴリ変数の処理
r.process_categorical()
for col in r.data_c.columns:
    print(col)