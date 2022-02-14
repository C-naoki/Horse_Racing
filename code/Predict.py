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

from tabulate import tabulate
from openpyxl.styles import PatternFill
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import Font
from openpyxl.styles.alignment import Alignment
from openpyxl.utils import column_index_from_string

if __name__ == '__main__':
    # race_dataの取得
    r = c.Results(_dat.race_results["overall"])
    # 前処理
    r.preprocessing(obj=objective)
    # 馬の過去成績の追加
    hr = c.HorseResults(_dat.horse_results["overall"])
    r.merge_horse_results(hr)
    # 5世代分の血統データの追加
    # p = c.Peds(_dat.ped_results["overall"])
    # p.encode()
    # r.merge_peds(p.peds_e)
    # カテゴリ変数の処理
    r.process_categorical()

    # 説明変数と目的変数に分割
    X = r.data_c.drop(drop_list+["odds", "rank"], axis=1)
    y = r.data_c['rank']

    # ランキング学習のためのクエリの作成
    query = list()
    for i in X.groupby(level=0):
        query.append(len(i[1]))
    # lightgbmでの学習
    lgb_clf = lgb.LGBMRanker(**params)
    lgb_clf.fit(X.values, y.values, group=query)

    # 出馬表データのスクレイピング
    # 欲しい出馬表のrace_id, 日付を引数とする。
    # "https://db.netkeiba.com/race/" + race_id (データベース)
    # "https://race.netkeiba.com/race/shutuba.html?race_id=" + race_id (出馬表)
    for venue_id in venue_id_list:
        # 出馬表のスクレイピング
        st = c.ShutubaTable.scrape(race_id_list=race_id_list[venue_id][venue_id[4:6]][venue_id[6:8]], date=date, place=venue_id[4:6])
        st.preprocessing()
        st.merge_horse_results(hr)
        # st.merge_peds(p.peds_e)
        st.process_categorical(r.le_horse, r.le_jockey)
        # ModelEvaluator
        me = c.ModelEvaluator(lgb_clf, tables_path, kind=1, obj=objective)
        X_fact = st.data_c.drop(drop_list, axis=1)
        # 各レースの本命馬、対抗馬、単穴馬、連下馬の出力
        pred = me.predict_proba(X_fact, train=False)
        proba_table = st.data_c[['horse_num']].astype('int').copy()
        proba_table['score'] = pred.astype('float64')
        # 払い戻し表のスクレイピング(まだサイトが完成していない場合はexceptに飛ぶ)
        try:
            return_chk = 1
            today_return_tables, arrival_tables_df = c.Return.scrape(race_id_list[venue_id])
            rt = c.Return(today_return_tables)
            tansho_df = rt.tansho.fillna(0)
            fukusho_df = rt.fukusho.fillna(0)
            sanrentan_df = rt.sanrentan.fillna(0)
            sanrenpuku_df = rt.sanrenpuku.fillna(0)
            predict_df = pd.DataFrame(
                                        index = [], 
                                        columns = predict_columns + result_columns
                                    )
            return_df = pd.DataFrame(
                                        index = [], 
                                        columns = return_columns
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
            if race_proba.iat[0, 1] - race_proba.iat[1, 1] >= 1 and race_proba.iat[0, 1] >= 2:
                favorite_rank = "A"
            elif race_proba.iat[0, 1] - race_proba.iat[1, 1] >= 1 or race_proba.iat[0, 1] >= 2:
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
                        real_arrival.append(
                            str(arrival_tables_df.loc[proba[0],:][
                                    arrival_tables_df.loc[proba[0],"馬番"]==race_proba.iat[j, 0]
                                ]["着順"].iat[0])
                            )
                    else:
                        real_arrival.append("-")
                # 単勝オッズを取得
                tansho_odds = tansho_df.loc[proba[0], "return"] / 100
                # 単勝回収率の計算
                if real_arrival[0] == "1": tansho_money = tansho_df.loc[proba[0], "return"]
                else: tansho_money = 0
                # 三連単の結果を取得
                sanrentan_results = str(int(sanrentan_df.loc[proba[0], "win_0"]))+" → "+\
                                    str(int(sanrentan_df.loc[proba[0], "win_1"]))+" → "+\
                                    str(int(sanrentan_df.loc[proba[0], "win_2"]))
                # 三連単のオッズを取得
                sanrentan_odds = sanrentan_df.loc[proba[0], "return"] / 100
                # 三連複のオッズを取得
                sanrenpuku_odds = sanrenpuku_df.loc[proba[0], "return"] / 100
                # 三連複が的中したかどうか記録
                sanrenpuku_results_list = list(map(int, sanrenpuku_df.loc[proba[0], "win_0":"win_2"]))
                sanrenpuku_predict_list = [
                                            race_proba.iat[0, 0],
                                            race_proba.iat[1, 0],
                                            race_proba.iat[2, 0],
                                            race_proba.iat[3, 0],
                                            race_proba.iat[4, 0],
                                            race_proba.iat[5, 0]
                                        ]
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
                predict_df.loc[race_num+"R"] = [
                                                favorite_rank,
                                                triple_rank,
                                                str(race_proba.iat[0, 0])+" ("+real_arrival[0]+")",
                                                str(race_proba.iat[1, 0])+" ("+real_arrival[1]+")",
                                                str(race_proba.iat[2, 0])+" ("+real_arrival[2]+")",
                                                str(race_proba.iat[3, 0])+" ("+real_arrival[3]+")",
                                                str(race_proba.iat[4, 0])+" ("+real_arrival[4]+")",
                                                str(race_proba.iat[5, 0])+" ("+real_arrival[5]+")",
                                                proba[1]['horse_num'][-1],
                                                tansho_odds,
                                                sanrentan_results,
                                                sanrentan_odds,
                                                sanrenpuku_odds,
                                                tansho_money,
                                                sanrentan_money,
                                                sanrenpuku_money
                                                ]
            else:
                # データをdfに追加
                predict_df.loc[race_num+"R"] = [
                                                favorite_rank,
                                                triple_rank,
                                                race_proba.iat[0, 0],
                                                race_proba.iat[1, 0],
                                                race_proba.iat[2, 0],
                                                race_proba.iat[3, 0],
                                                race_proba.iat[4, 0], 
                                                race_proba.iat[5, 0], 
                                                proba[1]['horse_num'][-1]
                                                ]

        if return_chk:
            # 予測及びオッズデータをxlsxファイルに書き込む
            writer = pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace')
            predict_df.to_excel(writer, sheet_name=sheet_name[venue_id])
            writer.save()
            # 追加したデータの修正
            wb = xl.load_workbook(excel_path)
            ws = wb[sheet_name[venue_id]]
            # 表の左上に開催地の追加
            ws['A1'] = venue_name[venue_id]
            ws['A1'].font = Font(bold=True)
            # 通常の線と二重線を用意
            side1 = Side(style='thin', color='000000')
            side2 = Side(style='double', color='000000')
            border1 = Border(top=side1, bottom=side1, left=side1, right=side1)
            border2 = Border(top=side1, bottom=side1, left=side1, right=side2)
            for col in ws.columns:
                for i, cell in enumerate(col):
                    coord = cell.coordinate
                    # 二重線の記入
                    if coord[0] == 'J' or coord[0] == 'C': ws[coord].border = border2
                    # 線の記入
                    else: ws[coord].border = border1
                    # ランクA及び着順の予想が的中した時、セルをオレンジ色にする
                    if (    ws[coord].value == 'A'
                        or (coord[0] == 'K' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)") 
                        or (coord[0] == 'N' and sanrenpuku_chk[i] == 3)
                        or (coord[0] == 'M' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)" and sanrenpuku_chk[i] == 3)):
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='ffbf7f')
                    # ランクB及び着順の予想が3着以内及び三連複の3頭中2頭的中した時、セルを水色にする
                    if (    ws[coord].value == 'B'
                        or (coord[0] == 'K' and (ws[list(ws.columns)[3][i].coordinate].value[-3:]=="(2)"
                        or ws[list(ws.columns)[3][i].coordinate].value[-3:]=="(3)"))
                        or (coord[0] == 'N' and sanrenpuku_chk[i] == 2)
                        or (coord[0] == 'M' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)" and sanrenpuku_chk[i] == 2)):
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='a8d3ff')
                    # ランクC及び及び三連複の3頭中1頭のみ的中した時、セルを灰色にする
                    if (    ws[coord].value == 'C'
                        or (coord[0] == 'N' and sanrenpuku_chk[i] == 1)
                        or (coord[0] == 'M' and ws[list(ws.columns)[3][i].coordinate].value[-3:] =="(1)" and sanrenpuku_chk[i] == 1)):
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='d3d3d3')
                    if coord[0] == 'A' or coord[1:] == '1':
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='000000')
                        ws[coord].font = Font(color="ffffff")
            # 馬のスコアごとにカラーリング
            for row in ws.rows:
                if 1 < int(row[0].coordinate[1:]) < 14:
                    for cell, score in zip(row[3:9], proba_table.loc[venue_id+str(int(row[0].coordinate[1:])-1).zfill(2)].sort_values('score', ascending = False)["score"].head(6)):
                        coord = cell.coordinate
                        if score > 2.4:
                            ws[coord].fill = PatternFill(patternType='solid', fgColor='ffbf7f')
                        elif score > 2:
                            ws[coord].fill = PatternFill(patternType='solid', fgColor='a8d3ff')
                        elif score > 1:
                            ws[coord].fill = PatternFill(patternType='solid', fgColor='d3d3d3')
            wb.save(excel_path)
            wb.close()

            # return_dfの作成
            all_win = np.zeros(4, dtype = int)
            all_sanrenpuku_win = 0
            all_sanrentan_win = 0
            all_tansho_cnt = 0
            all_sanren_cnt = 0
            all_tansho_money = 0
            all_sanrentan_money = 0
            all_sanrenpuku_money = 0
            # 各ランク毎の結果を集計
            for idx in ["A", "B", "C"]:
                tansho_win = np.zeros(4, dtype = int) # 勝ち馬を予測できた数
                tansho_cnt = 0 # ランク毎の馬の数
                tansho_money = 0 # 単勝の回収率
                sanrenpuku_win = 0 # 三連複的中数
                sanren_cnt = 0 # 三連系を購入すると決定した数
                sanrenpuku_money = 0 # 三連複回収金額
                sanrentan_win = 0 # 三連単的中数
                sanrentan_money = 0 # 三連単回収金額
                wb = xl.load_workbook(excel_path)
                ws = wb[sheet_name[venue_id]]
                for i in range(ws.max_row):
                    # True: 本命馬ランクがidxと一致
                    if ws['B{}'.format(i+1)].value == idx:
                        tansho_cnt += 1
                        # True: 単勝予測成功
                        if ws['D{}'.format(i+1)].value[-3:] == "(1)":
                            tansho_win[0] += 1
                            tansho_money += ws['O{}'.format(i+1)].value
                        elif ws['D{}'.format(i+1)].value[-3:] == "(2)":
                            tansho_win[1] += 1
                        elif ws['D{}'.format(i+1)].value[-3:] == "(3)":
                            tansho_win[2] += 1
                        else:
                            tansho_win[3] += 1
                    # True: 三連複ランクがidxと一致
                    if ws['C{}'.format(i+1)].value == idx:
                        sanren_cnt += 1
                        # True: 三連複予測成功
                        if ws['N{}'.format(i+1)].fill == PatternFill(patternType='solid', fgColor='ffbf7f'):
                            sanrenpuku_win += 1
                            sanrenpuku_money += ws['Q{}'.format(i+1)].value
                        # True: 三連単予測成功
                        if ws['M{}'.format(i+1)].fill == PatternFill(patternType='solid', fgColor='ffbf7f'):
                            sanrentan_win += 1
                            sanrentan_money += ws['P{}'.format(i+1)].value
                return_df.loc[idx] = [
                                        str(tansho_win[0])+'-'+str(tansho_win[1])+'-'+str(tansho_win[2])+'-'+str(tansho_win[3]),
                                        str(tansho_win[0])+'/'+str(tansho_cnt),
                                        str(sanrentan_win)+'/'+str(sanren_cnt),
                                        str(sanrenpuku_win)+'/'+str(sanren_cnt),
                                        m.div(tansho_money, 100*tansho_cnt),
                                        m.div(sanrentan_money,2000*sanren_cnt),
                                        m.div(sanrenpuku_money, 2000*sanren_cnt)
                                    ]
                all_win += tansho_win
                all_sanrentan_win += sanrentan_win
                all_sanrenpuku_win += sanrenpuku_win
                all_tansho_cnt += tansho_cnt
                all_sanren_cnt += sanren_cnt
                all_tansho_money += tansho_money
                all_sanrentan_money += sanrentan_money
                all_sanrenpuku_money += sanrenpuku_money
                wb.save(excel_path)
                wb.close()
                
            return_df.loc["全体"] = [
                                        str(all_win[0])+'-'+str(all_win[1])+'-'+str(all_win[2])+'-'+str(all_win[3]),
                                        str(all_win[0])+'/'+str(all_tansho_cnt),
                                        str(all_sanrentan_win)+'/'+str(all_sanren_cnt),
                                        str(sanrenpuku_win)+'/'+str(all_sanren_cnt),
                                        m.div(all_tansho_money, 100*all_tansho_cnt),
                                        m.div(all_sanrentan_money, 2000*all_sanren_cnt),
                                        m.div(all_sanrenpuku_money, 2000*all_sanren_cnt)
                                    ]
            # return_dfをexcelに追記
            wb = xl.load_workbook(excel_path)
            ws = wb[sheet_name[venue_id]]
            writer = pd.ExcelWriter(excel_path, engine='openpyxl')
            writer.book = wb
            writer.sheets = {ws.title: ws for ws in wb.worksheets}
            startrow = writer.sheets[sheet_name[venue_id]].max_row
            return_df.to_excel(writer, sheet_name=sheet_name[venue_id], startrow=startrow+1)
            # excelファイルの装飾
            ws['A15'] = "成績"
            ws['A15'].font = Font(bold=True)
            for col in ws.columns:
                max_length = 0
                for i, cell in enumerate(col):
                    coord = cell.coordinate
                    if coord[1:]!='14' and int(coord[1:])<=19 and int(column_index_from_string(coord[0]))<=8: ws[coord].border = border1
                    max_length = max(max_length, len(str(cell.value)))
                    # 必要箇所にカラーリング
                    if (coord[0] == 'A' and coord[1:] != '14') or coord[1:] == '15' and column_index_from_string(coord[0])<=8:
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='000000')
                        ws[coord].font = Font(color="ffffff")
                    if ws[coord].value == 'A':
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='ffbf7f')
                        ws[coord].font = Font(color="000000")
                    if ws[coord].value == 'B':
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='a8d3ff')
                        ws[coord].font = Font(color="000000")
                    if ws[coord].value == 'C':
                        ws[coord].fill = PatternFill(patternType='solid', fgColor='d3d3d3')
                        ws[coord].font = Font(color="000000")
                    # 文字を中心に配置する
                    cell.alignment = Alignment(horizontal = 'center', 
                                        vertical = 'center',
                                        wrap_text = False)
                    if (coord[0] == 'F' or coord[0] == 'G' or coord[0] == 'H') and 16 <= int(coord[1:]) <= 19:
                        cell.number_format = '0.00%'
                adjusted_width = max_length * 2.08
                ws.column_dimensions[col[0].column_letter].width = adjusted_width
            # ディレクトリを自動作成
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
                os.makedirs(dir_path.replace('pdf', 'png'))
            # xlsxをpdfに変換し、pdfディレクトリに保存する
            m.xlsx2pdf(file_path[venue_id], ws)
            # pdfをpngに変換し、pngディレクトリに保存する
            m.pdf2png(file_path[venue_id])



            writer.save()
            wb.save(excel_path)
            wb.close()
        # (まだレースが開催されていない場合)予想結果の表示
        else:
            print("<"+venue_name[venue_id]+">")
            print(tabulate(predict_df, predict_df.columns, tablefmt="presto", showindex=True))
        
    # 出力結果が得られた要因
    print(me.feature_importance(X))