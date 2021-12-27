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

    # 出馬表データのスクレイピング
    # 欲しい出馬表のrace_id, 日付を引数とする。
    # "https://db.netkeiba.com/race/" + race_id (データベース)
    # "https://race.netkeiba.com/race/shutuba.html?race_id=" + race_id (出馬表)
    race_id_list = ['2021060508{}'.format(str(i).zfill(2)) for i in range(1, 13)]
    st = c.ShutubaTable.scrape(race_id_list=race_id_list, date='2021/12/26')
    st.preprocessing()
    st.merge_horse_results(hr)
    st.merge_peds(p.peds_e)
    st.process_categorical(r.le_horse, r.le_jockey, r.data_pe)
    print("<finish making race card>\n")

    X = r.data_c.drop(['rank', 'date', '単勝', '体重', '体重変化'], axis=1)
    # X = rr.data_c.drop(['rank', 'date', '単勝'], axis=1)
    y = r.data_c['rank']

    train, valid = m.split_data(r.data_c)
    X_train = train.drop(['rank', 'date', '単勝'], axis=1)
    y_train = train['rank']
    X_valid = valid.drop(['rank', 'date', '単勝'], axis=1)
    y_valid = valid['rank']

    params = {'bagging_fraction': 1.0,
    'bagging_freq': 0,
    'feature_fraction': 0.4,
    'feature_pre_filter': False,
    'lambda_l1': 9.073888467934557,
    'lambda_l2': 4.497950393394061,
    'min_child_samples': 25,
    'num_leaves': 31,
    'objective': 'binary',
    'random_state': 100}

    lgb_clf = lgb.LGBMClassifier(**params)
    lgb_clf.fit(X.values, y.values)

    # ModelEvaluator
    me = c.ModelEvaluator(lgb_clf, ['_dat/pickle/overall/return_tables.pickle'])
    # X_fact = st.data_c.drop(['date', '体重', '体重変化'], axis=1)
    X_fact = st.data_c.drop(['date'], axis=1)

    # MLが予想する信憑性が高い馬n選
    # pred = me.predict_proba(st.data_c.drop(['date'], axis=1), train=False)
    print("\n開催地 = {}".format([k for k, v in place_dict.items() if v == race_id_list[0][4:6]][0]))
    pred = me.predict_proba(X_fact, train=False)
    proba_table = st.data_c[['馬番']].copy()
    proba_table['score'] = pred
    print(proba_table.sort_values('score', ascending = False).head(30))