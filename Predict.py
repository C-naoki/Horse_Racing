import sys
sys.dont_write_bytecode = True

import module as m
import module._class as c
import _dat
from environment.variables import *

import pandas as pd
import optuna.integration.lightgbm as lgb_o
import lightgbm as lgb

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
    print("<finish making race results>\n")

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
    venue_id_list = ["2021060508"]
    for venue in venue_id_list:
        race_id_list = [venue + str(i).zfill(2) for i in range(1, 13)]
        st = c.ShutubaTable.scrape(race_id_list=race_id_list, date='2021/12/26')
        st.preprocessing()
        st.merge_horse_results(hr)
        st.merge_peds(p.peds_e)
        st.process_categorical(r.le_horse, r.le_jockey, r.data_pe)
        print("<finish making race card>\n")

        # ModelEvaluator
        me = c.ModelEvaluator(lgb_clf, ['_dat/pickle/overall/return_tables.pickle'])
        # X_fact = st.data_c.drop(['date', '体重', '体重変化'], axis=1)
        X_fact = st.data_c.drop(['date'], axis=1)

        # 各レースの本命馬、対抗馬、単穴馬、連下馬の出力
        venue_name = [k for k, v in place_dict.items() if v == race_id_list[0][4:6]][0]
        pred = me.predict_proba(X_fact, train=False)
        proba_table = st.data_c[['馬番']].copy()
        proba_table['score'] = pred
        print("~Expected results~")
        for proba in proba_table.groupby(level=0):
            if proba[0][-2] == "0":
                race_num = proba[0][-1]
            else:
                race_num = proba[0][-2:]
            print("\n<" + venue_name + race_num + "R>")
            race_proba = proba[1].sort_values('score', ascending = False).head(6)
            print("本命◎ : 馬番 {} ({:.3f})".format(race_proba.iat[0, 0], race_proba.iat[0, 1]))
            print("対抗○ : 馬番 {} ({:.3f})".format(race_proba.iat[1, 0], race_proba.iat[1, 1]))
            print("単穴▲ : 馬番 {} ({:.3f})".format(race_proba.iat[2, 0], race_proba.iat[2, 1]))
            print("連下△ : 馬番 {} ({:.3f}), 馬番 {} ({:.3f}), 馬番 {} ({:.3f})".format(race_proba.iat[3, 0], race_proba.iat[3, 1], race_proba.iat[4, 0], race_proba.iat[4, 1], race_proba.iat[5, 0], race_proba.iat[5, 1]))
