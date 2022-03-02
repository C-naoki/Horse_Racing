## 1. ディレクトリ構造
<pre>
.
├── Notebook
│   ├── DL入門.ipynb
│   ├── ML.ipynb
│   ├── RL.ipynb
│   └── plot.ipynb
├── README.md
├── _dat
│   ├── DataFrame.py
│   ├── __init__.py
│   └── train_data
│       ├── 2017
│       ├── 2018
│       ├── 2019
│       ├── 2020
│       ├── 2021
│       ├── overall
│       ├── results
│       │   ├── g_proper.pickle
│       │   ├── g_sanrenpuku.pickle
│       │   ├── g_sanrentan.pickle
│       │   ├── g_sanrentan_nagashi.pickle
│       │   ├── g_tansho.pickle
│       │   ├── g_umaren.pickle
│       │   ├── g_umaren_nagashi.pickle
│       │   ├── g_umatan.pickle
│       │   ├── g_umatan_nagashi.pickle
│       │   ├── g_wide.pickle
│       │   └── g_wide_nagashi.pickle
│       └── temporary
├── code
│   ├── Predict.py
│   ├── Scrape.py
│   └── show.py
├── environment
│   ├── __init__.py
│   └── variables.py
├── module
│   ├── __init__.py
│   ├── _class
│   │   ├── DataProcessor.py
│   │   ├── HorseResults.py
│   │   ├── ModelEvaluator.py
│   │   ├── Peds.py
│   │   ├── Results.py
│   │   ├── Return.py
│   │   ├── ShutubaTable.py
│   │   └── __init__.py
│   └── functions.py
├── requirements.txt
└── results
    ├── 2022
    │   ├── pdf
    │   ├── png
    │   └── xlsx
    └── README.md
</pre>

## 2. データ量

|               |   2017   |   2018   |   2019   |   2020   |   2021   |   2022   | 
| ------------- | :------: | :------: | :------: | :------: | :------: | :------: | 
| race_results  |   49299  |   47571  |   46343  |   48282  |   47821  |          | 
| horse_results |  212928  |  309882  |  275246  |  221934  |  144484  |          | 
| ped_results   |   11277  |   11398  |   11557  |   11702  |   11567  |          | 
| return_tables |   27526  |   27471  |   27444  |   27505  |   27469  |          | 

## 3. 現在利用してるモデル
* drop_list = ['date', 'jockey_id', 'breeder_id', 'owner_id', 'trainer_id', 'birthday', 'horse_id']
* avg=False
* ped=False
* objective=lambdarank
* 'metric': 'ndcg'
* 'ndcg_eval_at': [1000]