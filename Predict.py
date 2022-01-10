import sys
sys.dont_write_bytecode = True

import module as m
import module._class as c
import _dat

import pandas as pd
import numpy as np
import optuna.integration.lightgbm as lgb_o
import lightgbm as lgb
import openpyxl

from environment.variables import *
from tabulate import tabulate

if __name__ == '__main__':
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
    print("\n<finish making race results>\n")

    X = r.data_c.drop(['rank', 'date', '単勝', '体重', '体重変化'], axis=1)
    # X = rr.data_c.drop(['rank', 'date', '単勝'], axis=1)
    y = r.data_c['rank']

    params={'objective': 'binary',
            'random_state': 100,
            'feature_pre_filter': False,
            'lambda_l1': 5.656720411334836,
            'lambda_l2': 0.0008932155945833474,
            'num_leaves': 31,
            'feature_fraction': 0.4,
            'bagging_fraction': 1.0,
            'bagging_freq': 0,
            'min_child_samples': 20}
    lgb_clf = lgb.LGBMClassifier(**params)
    lgb_clf.fit(X.values, y.values)

    # 出馬表データのスクレイピング
    # 欲しい出馬表のrace_id, 日付を引数とする。
    # "https://db.netkeiba.com/race/" + race_id (データベース)
    # "https://race.netkeiba.com/race/shutuba.html?race_id=" + race_id (出馬表)
    venue_id_list = ["2022060101", "2022070101"]
    for venue in venue_id_list:
        race_id_list = [venue + str(i).zfill(2) for i in range(1, 13)]
        st = c.ShutubaTable.scrape(race_id_list=race_id_list, date='2022/01/05')
        st.preprocessing()
        st.merge_horse_results(hr)
        st.merge_peds(p.peds_e)
        st.process_categorical(r.le_horse, r.le_jockey, r.data_pe)
        print("\n<finish making race card>\n")

        # ModelEvaluator
        me = c.ModelEvaluator(lgb_clf, ['_dat/pickle/overall/return_tables.pickle'])
        # X_fact = st.data_c.drop(['date', '体重', '体重変化'], axis=1)
        X_fact = st.data_c.drop(['date'], axis=1)

        # 各レースの本命馬、対抗馬、単穴馬、連下馬の出力
        venue_name = [k for k, v in place_dict.items() if v == race_id_list[0][4:6]][0]
        pred = me.predict_proba(X_fact, train=False)
        proba_table = st.data_c[['馬番']].copy()
        proba_table['score'] = pred
        print("\n~Expected results~")
        pd.options.display.float_format = '{:.4f}'.format
        predict_df = pd.DataFrame(
                                    index = [], 
                                    columns = ["本命馬◎", "本命馬(score)", "対抗馬○", "対抗馬(score)", "単穴馬▲", "単穴馬(score)", "連下馬1△", "連下馬1(score)", "連下馬2△", "連下馬2(score)", "連下馬3△", "連下馬3(score)"]
                                )
        print("<"+venue_name+">")
        for proba in proba_table.groupby(level=0):
            if proba[0][-2] == "0":
                race_num = " "+proba[0][-1]
            else:
                race_num = proba[0][-2:]
            race_proba = proba[1].sort_values('score', ascending = False).head(6)
            predict_df.loc[race_num+"R"] = [race_proba.iat[0, 0], race_proba.iat[0, 1], race_proba.iat[1, 0], race_proba.iat[1, 1], race_proba.iat[2, 0], race_proba.iat[2, 1], race_proba.iat[3, 0], race_proba.iat[3, 1], race_proba.iat[4, 0], race_proba.iat[4, 1], race_proba.iat[5, 0], race_proba.iat[5, 1]]
        # print(tabulate(predict_df, predict_df.columns, tablefmt="presto", showindex=True))
        with pd.ExcelWriter('_dat/results.xlsx', mode='a', if_sheet_exists="replace") as writer:
            predict_df.to_excel(writer, sheet_name=venue_name)
        print(me.feature_importance(X))