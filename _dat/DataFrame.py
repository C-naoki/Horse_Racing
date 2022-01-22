import pandas as pd

horse_results = pd.read_pickle("../_dat/train_data/overall/horse_results.pickle")
ped_results = pd.read_pickle("../_dat/train_data/overall/ped_results.pickle")
race_results = pd.read_pickle("../_dat/train_data/overall/race_results.pickle")
return_tables = pd.read_pickle("../_dat/train_data/overall/return_tables.pickle")
horse_id_list = race_results['horse_id'].unique()

horse_results_2022 = pd.read_pickle("../_dat/train_data/2022/horse_results.pickle")
ped_results_2022 = pd.read_pickle("../_dat/train_data/2022/ped_results.pickle")
race_results_2022 = pd.read_pickle("../_dat/train_data/2022/race_results.pickle")
return_tables_2022 = pd.read_pickle("../_dat/train_data/2022/return_tables.pickle")
horse_id_list_2022 = race_results_2022['horse_id'].unique()

horse_results_2021 = pd.read_pickle("../_dat/train_data/2021/horse_results.pickle")
ped_results_2021 = pd.read_pickle("../_dat/train_data/2021/ped_results.pickle")
race_results_2021 = pd.read_pickle("../_dat/train_data/2021/race_results.pickle")
return_tables_2021 = pd.read_pickle("../_dat/train_data/2021/return_tables.pickle")
horse_id_list_2021 = race_results_2021['horse_id'].unique()

horse_results_2020 = pd.read_pickle("../_dat/train_data/2020/horse_results.pickle")
ped_results_2020 = pd.read_pickle("../_dat/train_data/2020/ped_results.pickle")
race_results_2020 = pd.read_pickle("../_dat/train_data/2020/race_results.pickle")
return_tables_2020 = pd.read_pickle("../_dat/train_data/2020/return_tables.pickle")
horse_id_list_2020 = race_results_2020['horse_id'].unique()

horse_results_2019 = pd.read_pickle("../_dat/train_data/2019/horse_results.pickle")
ped_results_2019 = pd.read_pickle("../_dat/train_data/2019/ped_results.pickle")
race_results_2019 = pd.read_pickle("../_dat/train_data/2019/race_results.pickle")
return_tables_2019 = pd.read_pickle("../_dat/train_data/2019/return_tables.pickle")
horse_id_list_2019 = race_results_2019['horse_id'].unique()

horse_results_2018 = pd.read_pickle("../_dat/train_data/2018/horse_results.pickle")
ped_results_2018 = pd.read_pickle("../_dat/train_data/2018/ped_results.pickle")
race_results_2018 = pd.read_pickle("../_dat/train_data/2018/race_results.pickle")
return_tables_2018 = pd.read_pickle("../_dat/train_data/2018/return_tables.pickle")
horse_id_list_2018 = race_results_2018['horse_id'].unique()

horse_results_2017 = pd.read_pickle("../_dat/train_data/2017/horse_results.pickle")
ped_results_2017 = pd.read_pickle("../_dat/train_data/2017/ped_results.pickle")
race_results_2017 = pd.read_pickle("../_dat/train_data/2017/race_results.pickle")
return_tables_2017 = pd.read_pickle("../_dat/train_data/2017/return_tables.pickle")
horse_id_list_2017 = race_results_2017['horse_id'].unique()

new_horse_results = pd.read_pickle("../_dat/train_data/temporary/horse_results.pickle")
new_ped_results = pd.read_pickle("../_dat/train_data/temporary/ped_results.pickle")
new_race_results = pd.read_pickle("../_dat/train_data/temporary/race_results.pickle")
new_return_tables = pd.read_pickle("../_dat/train_data/temporary/return_tables.pickle")
new_horse_id_list = new_race_results['horse_id'].unique()