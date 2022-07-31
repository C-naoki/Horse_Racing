import pandas as pd
horse_results = {}
ped_results = {}
race_results = {}
return_tables = {}
jockey_results = {}
trainer_results = {}
owner_results = {}
breeder_results = {}
horse_id_list = {}

for key in ['overall', '2017', '2018', '2019', '2020', '2021', '2022']:
    horse_results[key] = pd.read_pickle("../_dat/train_data/"+key+"/horse_results.pickle")
    ped_results[key] = pd.read_pickle("../_dat/train_data/"+key+"/ped_results.pickle")
    race_results[key] = pd.read_pickle("../_dat/train_data/"+key+"/race_results.pickle")
    return_tables[key] = pd.read_pickle("../_dat/train_data/"+key+"/return_tables.pickle")
    jockey_results[key] = pd.read_pickle("../_dat/train_data/"+key+"/jockey_results.pickle")
    trainer_results[key] = pd.read_pickle("../_dat/train_data/"+key+"/trainer_results.pickle")
    owner_results[key] = pd.read_pickle("../_dat/train_data/"+key+"/owner_results.pickle")
    breeder_results[key] = pd.read_pickle("../_dat/train_data/"+key+"/breeder_results.pickle")
    horse_id_list[key] = race_results[key]['horse_id'].unique()
