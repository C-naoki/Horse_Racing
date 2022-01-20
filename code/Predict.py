import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import module as m
import module._class as c
import _dat
from environment.variables import *

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
    # race_dataの取得
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

    # 訓練データと検証データに分割
    X = r.data_c.drop(['rank', 'date', '単勝'], axis=1)
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
    # lightgbmでの学習
    lgb_clf = lgb.LGBMClassifier(**params)
    lgb_clf.fit(X.values, y.values)

    # 出馬表データのスクレイピング
    # 欲しい出馬表のrace_id, 日付を引数とする。
    # "https://db.netkeiba.com/race/" + race_id (データベース)
    # "https://race.netkeiba.com/race/shutuba.html?race_id=" + race_id (出馬表)
    for venue_id in venue_id_list:
        race_id_list = [venue_id + str(i).zfill(2) for i in range(1, 13)]
        # 出馬表のスクレイピング
        st = c.ShutubaTable.scrape(race_id_list=race_id_list, date=date)
        st.preprocessing()
        st.merge_horse_results(hr)
        st.merge_peds(p.peds_e)
        st.process_categorical(r.le_horse, r.le_jockey, r.data_pe)
        # ModelEvaluator
        me = c.ModelEvaluator(lgb_clf, tables_path, kind=1)
        X_fact = st.data_c.drop(['date'], axis=1)
        # 開催地名と記入するシート名
        venue_name = [k for k, v in place_dict.items() if v == race_id_list[0][4:6]][0]
        sheet_name = day+"日"+venue_name
        # 各レースの本命馬、対抗馬、単穴馬、連下馬の出力
        pred = me.predict_proba(X_fact, train=False)
        proba_table = st.data_c[['馬番']].astype('int').copy()
        proba_table['score'] = pred.astype('float64')
        pd.options.display.float_format = '{:.4f}'.format
        # 払い戻し表のスクレイピング(まだサイトが完成していない場合はexceptに飛ぶ)
        try:
            return_chk = 1
            today_return_tables, arrival_tables_df = c.Return.scrape(race_id_list)
            rt = c.Return(today_return_tables)
            tansho_df = rt.tansho
            fukusho_df = rt.fukusho
            sanrentan_df = rt.sanrentan
            sanrenpuku_df = rt.sanrenpuku
            predict_df = pd.DataFrame(
                                        index = [], 
                                        columns = predict_columns + result_columns
                                    )
        except:
            return_chk = 0
            predict_df = pd.DataFrame(
                                    index = [], 
                                    columns = predict_columns
                                )
        # 三連複が的中したかどうか記録する配列
        sanrenpuku_chk = [0] * (len(set(st.data_c.index))+1)
        for i, proba in enumerate(proba_table.groupby(level=0)):
            if proba[0][-2] == "0":
                race_num = " "+proba[0][-1]
            else:
                race_num = proba[0][-2:]
            race_proba = proba[1].sort_values('score', ascending = False).head(6)
            # 三連複のランクの決定
            if len(race_proba["score"][race_proba["score"]>=1.5])>=3:
                triple_rank = "A"
            elif len(race_proba["score"][race_proba["score"]>=1.5])>=2:
                triple_rank = "B"
            elif len(race_proba["score"][race_proba["score"]>=1.5])>=1:
                triple_rank = "C"
            else:
                triple_rank = "-"
            # 本命馬のランクの決定
            if race_proba.iat[0, 1] - race_proba.iat[1, 1] >= 1 and race_proba.iat[0, 1] >= 3:
                favorite_rank = "A"
            elif race_proba.iat[0, 1] - race_proba.iat[1, 1] >= 1 or race_proba.iat[0, 1] >= 3:
                favorite_rank = "B"
            elif race_proba.iat[0, 1] - race_proba.iat[1, 1] >= 0.4:
                favorite_rank = "C"
            else:
                favorite_rank = "-"
            # race_id_listの長さが6に満たない場合、"-"で埋める
            s = pd.Series(['-', '-'], index=race_proba.columns, name=race_proba.index[0])
            for j in range(6-len(race_proba)):
                race_proba=race_proba.append(s)
            if return_chk:
                # 本命馬の着順結果を取得
                real_arrival = list()
                for j in range(6):
                    if len(arrival_tables_df.loc[proba[0],:][arrival_tables_df.loc[proba[0],"馬番"]==race_proba.iat[j, 0]]["着順"]) == 1:
                        real_arrival.append(str(arrival_tables_df.loc[proba[0],:][arrival_tables_df.loc[proba[0],"馬番"]==race_proba.iat[j, 0]]["着順"].iat[0]))
                    else:
                        real_arrival.append("-")
                # 単勝オッズを取得
                tansho_odds = tansho_df.loc[proba[0], "return"] / 100
                # 単勝回収率の計算
                if int(real_arrival[0]) == 1: tansho_money = tansho_df.loc[proba[0], "return"]
                else: tansho_money = 0
                # 三連単の結果を取得
                sanrentan_results = str(sanrentan_df.loc[proba[0], "win_0"])+" → "+str(sanrentan_df.loc[proba[0], "win_1"])+" → "+str(sanrentan_df.loc[proba[0], "win_2"])
                # 三連単のオッズを取得
                sanrentan_odds = sanrentan_df.loc[proba[0], "return"] / 100
                # 三連複のオッズを取得
                sanrenpuku_odds = sanrenpuku_df.loc[proba[0], "return"] / 100
                # 三連複が的中したかどうか記録
                sanrenpuku_results_list = list(map(int, sanrenpuku_df.loc[proba[0], "win_0":"win_2"]))
                sanrenpuku_predict_list = [race_proba.iat[0, 0], race_proba.iat[1, 0], race_proba.iat[2, 0], race_proba.iat[3, 0], race_proba.iat[4, 0], race_proba.iat[5, 0]]
                for result in sanrenpuku_results_list:
                    if result in sanrenpuku_predict_list:
                        sanrenpuku_chk[i+1] += 1
                # 三連複の回収率の計算
                if sanrenpuku_chk[i+1] == 3: sanrenpuku_money = sanrenpuku_df.loc[proba[0], "return"]
                else: sanrenpuku_money = 0
                # 三連単の回収率の計算
                if sanrenpuku_chk[i+1] == 3 and real_arrival[0] == '1': sanrentan_money = sanrentan_df.loc[proba[0], "return"]
                else: sanrentan_money = 0
                # データをdfに追加
                predict_df.loc[race_num+"R"] = [favorite_rank, triple_rank, str(race_proba.iat[0, 0])+" ("+real_arrival[0]+")", str(race_proba.iat[1, 0])+" ("+real_arrival[1]+")", str(race_proba.iat[2, 0])+" ("+real_arrival[2]+")", str(race_proba.iat[3, 0])+" ("+real_arrival[3]+")", str(race_proba.iat[4, 0])+" ("+real_arrival[4]+")", str(race_proba.iat[5, 0])+" ("+real_arrival[5]+")", tansho_odds, sanrentan_results, sanrentan_odds, sanrenpuku_odds, tansho_money, sanrentan_money, sanrenpuku_money]
            else:
                # データをdfに追加
                predict_df.loc[race_num+"R"] = [favorite_rank, triple_rank, race_proba.iat[0, 0], race_proba.iat[1, 0], race_proba.iat[2, 0], race_proba.iat[3, 0], race_proba.iat[4, 0], race_proba.iat[5, 0]]
        # (まだレースが開催されていない場合)xlsxファイルに保存するデータの表示
        if return_chk:
            # データをxlsxファイルに書き込む
            with pd.ExcelWriter(excel_path, engine='openpyxl', mode="a", if_sheet_exists="replace") as writer:
                predict_df.to_excel(writer, sheet_name=sheet_name)
            # 追加したデータの修正
            wb = xl.load_workbook(excel_path)
            ws = wb[sheet_name]
            # 表の左上に開催地の追加
            ws['A1'] = venue_name
            ws['A1'].font = Font(bold=True)
            side1 = Side(style='thin', color='000000')
            side2 = Side(style='double', color='000000')
            border1 = Border(top=side1, bottom=side1, left=side1, right=side1)
            border2 = Border(top=side1, bottom=side1, left=side1, right=side2)
            for col in ws.columns:
                max_length = 0
                for i, cell in enumerate(col):
                    max_length = max(max_length, len(str(cell.value)))
                    if cell.coordinate[0] == 'I' or cell.coordinate[0] == 'C': ws[cell.coordinate].border = border2 # 二重線の記入
                    else: ws[cell.coordinate].border = border1 # 線の記入
                    # ランクA及び着順の予想が的中した時、セルをオレンジ色にする
                    if ws[cell.coordinate].value == 'A' or (cell.coordinate[0] == 'J' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)") or (cell.coordinate[0] == 'M' and sanrenpuku_chk[i] == 3) or (cell.coordinate[0] == 'L' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)" and sanrenpuku_chk[i] == 3):
                        ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='ffbf7f')
                    # ランクB及び着順の予想が3着以内及び三連複の3頭中2頭的中した時、セルを水色にする
                    if ws[cell.coordinate].value == 'B' or (cell.coordinate[0] == 'J' and (ws[list(ws.columns)[3][i].coordinate].value[-3:]=="(2)" or ws[list(ws.columns)[3][i].coordinate].value[-3:]=="(3)")) or (cell.coordinate[0] == 'M' and sanrenpuku_chk[i] == 2) or (cell.coordinate[0] == 'L' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)" and sanrenpuku_chk[i] == 2):
                        ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='a8d3ff')
                    # ランクC及び及び三連複の3頭中1頭のみ的中した時、セルを灰色にする
                    if ws[cell.coordinate].value == 'C' or (cell.coordinate[0] == 'M' and sanrenpuku_chk[i] == 1) or (cell.coordinate[0] == 'L' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)" and sanrenpuku_chk[i] == 1):
                        ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='d3d3d3')
                    if cell.coordinate[0] == 'A' or cell.coordinate[1:] == '1':
                        ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='000000')
                        ws[cell.coordinate].font = Font(color="ffffff")
                    # 文字を中心に配置する
                    cell.alignment = Alignment(horizontal = 'center', 
                                        vertical = 'center',
                                        wrap_text = False)
                adjusted_width = max_length * 2.08
                ws.column_dimensions[col[0].column_letter].width = adjusted_width
            for row in ws.rows:
                if 1 < int(row[0].coordinate[1:]) < 14:
                    for cell, score in zip(row[3:9], proba_table.loc[venue_id+str(int(row[0].coordinate[1:])-1).zfill(2)].sort_values('score', ascending = False)["score"].head(6)):
                        if score > 3:
                            ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='ffbf7f')
                        elif score > 2:
                            ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='a8d3ff')
                        elif score > 1.5:
                            ws[cell.coordinate].fill = PatternFill(patternType='solid', fgColor='d3d3d3')
            wb.save(excel_path)
        else:
            print("<"+venue_name+">")
            print(tabulate(predict_df, predict_df.columns, tablefmt="presto", showindex=True))
    # 出力結果が得られた要因
    print(me.feature_importance(X))