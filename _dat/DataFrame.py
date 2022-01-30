import pandas as pd
horse_results = {}
ped_results = {}
race_results = {}
return_tables = {}
horse_id_list = {}

horse_results["overall"] = pd.read_pickle("../_dat/train_data/overall/horse_results.pickle")
ped_results["overall"] = pd.read_pickle("../_dat/train_data/overall/ped_results.pickle")
race_results["overall"] = pd.read_pickle("../_dat/train_data/overall/race_results.pickle")
return_tables["overall"] = pd.read_pickle("../_dat/train_data/overall/return_tables.pickle")
horse_id_list["overall"] = race_results["overall"]['horse_id'].unique()

horse_results["2022"] = pd.read_pickle("../_dat/train_data/2022/horse_results.pickle")
ped_results["2022"] = pd.read_pickle("../_dat/train_data/2022/ped_results.pickle")
race_results["2022"] = pd.read_pickle("../_dat/train_data/2022/race_results.pickle")
return_tables["2022"] = pd.read_pickle("../_dat/train_data/2022/return_tables.pickle")
horse_id_list["2022"] = race_results["2022"]['horse_id'].unique()

horse_results["2021"] = pd.read_pickle("../_dat/train_data/2021/horse_results.pickle")
ped_results["2021"] = pd.read_pickle("../_dat/train_data/2021/ped_results.pickle")
race_results["2021"] = pd.read_pickle("../_dat/train_data/2021/race_results.pickle")
return_tables["2021"] = pd.read_pickle("../_dat/train_data/2021/return_tables.pickle")
horse_id_list["2021"] = race_results["2021"]['horse_id'].unique()

horse_results["2020"] = pd.read_pickle("../_dat/train_data/2020/horse_results.pickle")
ped_results["2020"] = pd.read_pickle("../_dat/train_data/2020/ped_results.pickle")
race_results["2020"] = pd.read_pickle("../_dat/train_data/2020/race_results.pickle")
return_tables["2020"] = pd.read_pickle("../_dat/train_data/2020/return_tables.pickle")
horse_id_list["2020"] = race_results["2020"]['horse_id'].unique()

horse_results["2019"] = pd.read_pickle("../_dat/train_data/2019/horse_results.pickle")
ped_results["2019"] = pd.read_pickle("../_dat/train_data/2019/ped_results.pickle")
race_results["2019"] = pd.read_pickle("../_dat/train_data/2019/race_results.pickle")
return_tables["2019"] = pd.read_pickle("../_dat/train_data/2019/return_tables.pickle")
horse_id_list["2019"] = race_results["2019"]['horse_id'].unique()

horse_results["2018"] = pd.read_pickle("../_dat/train_data/2018/horse_results.pickle")
ped_results["2018"] = pd.read_pickle("../_dat/train_data/2018/ped_results.pickle")
race_results["2018"] = pd.read_pickle("../_dat/train_data/2018/race_results.pickle")
return_tables["2018"] = pd.read_pickle("../_dat/train_data/2018/return_tables.pickle")
horse_id_list["2018"] = race_results["2018"]['horse_id'].unique()

horse_results["2017"] = pd.read_pickle("../_dat/train_data/2017/horse_results.pickle")
ped_results["2017"] = pd.read_pickle("../_dat/train_data/2017/ped_results.pickle")
race_results["2017"] = pd.read_pickle("../_dat/train_data/2017/race_results.pickle")
return_tables["2017"] = pd.read_pickle("../_dat/train_data/2017/return_tables.pickle")
horse_id_list["2017"] = race_results["2017"]['horse_id'].unique()