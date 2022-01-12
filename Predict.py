import module as m
import module._class as c
import _dat

import pandas as pd
import numpy as np
import optuna.integration.lightgbm as lgb_o
import lightgbm as lgb
import openpyxl as xl
import datetime

from environment.variables import *
from tabulate import tabulate
from openpyxl.styles import PatternFill
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import Font
from openpyxl.styles.alignment import Alignment

if __name__ == '__main__':
    venue_id_list = ["2022060101", "2022070101"] # race_id_list
    date = '2022/01/05' # レース日
    year = date[0:4]
    month = date[5:7]
    day = date[8:10]
    dt_now = datetime.datetime.now() # 今の日付
    race_date = datetime.date(int(year), int(month), int(day)) # レース日
    today = datetime.date(dt_now.year, dt_now.month, dt_now.day)
    if month[0] == '0': month = month[1]
    if day[0] == '0': day = day[1]
    excel_path = 'results/'+year+'/'+month+'月.xlsx'

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
    for venue in venue_id_list:
        race_id_list = [venue + str(i).zfill(2) for i in range(1, 13)]
        st = c.ShutubaTable.scrape(race_id_list=race_id_list, date=date)
        st.preprocessing()
        st.merge_horse_results(hr)
        st.merge_peds(p.peds_e)
        st.process_categorical(r.le_horse, r.le_jockey, r.data_pe)
        print("\n<finish making race card>\n")

        today_return_tables, arrival_tables_df = c.Return.scrape(race_id_list)

        # ModelEvaluator
        me = c.ModelEvaluator(lgb_clf, ['_dat/pickle/overall/return_tables.pickle'])
        # X_fact = st.data_c.drop(['date', '体重', '体重変化'], axis=1)
        X_fact = st.data_c.drop(['date'], axis=1)

        # 各レースの本命馬、対抗馬、単穴馬、連下馬の出力
        venue_name = [k for k, v in place_dict.items() if v == race_id_list[0][4:6]][0]
        sheet_name = day+"日"+venue_name
        pred = me.predict_proba(X_fact, train=False)
        proba_table = st.data_c[['馬番']].copy()
        proba_table['score'] = pred
        print("\n~Expected results~")
        pd.options.display.float_format = '{:.4f}'.format
        predict_df = pd.DataFrame(
                                    index = [], 
                                    columns = ["三連複ランク", "本命馬ランク", "本命馬◎", "対抗馬○", "単穴馬▲", "連下馬1△", "連下馬2△", "連下馬3△", "本命馬着順"]
                                )
        print("<"+venue_name+">")
        for proba in proba_table.groupby(level=0):
            if proba[0][-2] == "0":
                race_num = " "+proba[0][-1]
            else:
                race_num = proba[0][-2:]
            race_proba = proba[1].sort_values('score', ascending = False).head(6)
            # 三連複のランクの決定
            if race_proba.iat[5, 1] < 0:
                triple_rank = "C"
            elif race_proba.iat[5, 1] < 0.5:
                triple_rank = "B"
            else:
                triple_rank = "A"
            # 本命馬のランクの決定
            if race_proba.iat[0, 1] - race_proba.iat[1, 1] < 0.4:
                favorite_rank = "C"
            elif race_proba.iat[0, 1] - race_proba.iat[1, 1] < 1:
                favorite_rank = "B"
            else:
                favorite_rank = "A"
            real_arrival = int(arrival_tables_df.loc[proba[0],:][arrival_tables_df.loc[proba[0],"馬番"]==race_proba.iat[0, 0]]["着順"].iat[0])
            predict_df.loc[race_num+"R"] = [triple_rank, favorite_rank, race_proba.iat[0, 0], race_proba.iat[1, 0], race_proba.iat[2, 0], race_proba.iat[3, 0], race_proba.iat[4, 0], race_proba.iat[5, 0], real_arrival]
        print(tabulate(predict_df, predict_df.columns, tablefmt="presto", showindex=True))
        # データの追加
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode="a", if_sheet_exists="replace") as writer:
            predict_df.to_excel(writer, sheet_name=day+"日"+venue_name)
        # 追加したデータの修正
        wb = xl.load_workbook(excel_path)
        ws = wb[sheet_name]
        ws['A1'] = venue_name
        ws['A1'].font = Font(bold=True)
        side = Side(style='thin', color='000000')
        border = Border(top=side, bottom=side, left=side, right=side)
        for col in ws.columns:
            max_length = 0
            for cell in col:
                max_length = max(max_length, len(str(cell.value)))
                ws[cell.coordinate].border = border
                # ランクA及び着順の予想が的中した時、セルをオレンジ色にする
                if ws[cell.coordinate].value == 'A' or (cell.coordinate[0] == 'J' and cell.value == 1):
                    ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='ffa500')
                # ランクB及び着順の予想が2着だった時、セルを水色にする
                if ws[cell.coordinate].value == 'B' or (cell.coordinate[0] == 'J' and cell.value == 2):
                    ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='87ceeb')
                if cell.coordinate[0] == 'A' or cell.coordinate[1:] == '1':
                    ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='d3d3d3')
                cell.alignment = Alignment(horizontal = 'center', 
                                    vertical = 'center',
                                    wrap_text = False)
            adjusted_width = max_length * 2.08
            ws.column_dimensions[col[0].column_letter].width = adjusted_width
        wb.save(excel_path)


    print(me.feature_importance(X))