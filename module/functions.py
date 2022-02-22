import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

import openpyxl as xl
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import column_index_from_string
from openpyxl.styles.borders import Border, Side
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import mm
from reportlab.lib import colors
from pathlib import Path
from pdf2image import convert_from_path

def update_data(old, new):
    """
    Parameters:
    ----------
    old : pandas.DataFrame
        古いデータ
    new : pandas.DataFrame
        新しいデータ
    """

    filtered_old = old[~old.index.isin(new.index)]
    return pd.concat([filtered_old, new])

def split_data(df, test_size=0.3):
    sorted_id_list = df.sort_values("date").index.unique()
    train_id_list = sorted_id_list[: round(len(sorted_id_list) * (1 - test_size))]
    test_id_list = sorted_id_list[round(len(sorted_id_list) * (1 - test_size)) :]
    train = df.loc[train_id_list]
    test = df.loc[test_id_list]
    return train, test

def gain(return_func, X, n_samples=100, t_range=[0.5, 3.5]):
    gain = {}
    for i in tqdm(range(n_samples)):
        #min_thresholdから1まで、n_samples等分して、thresholdをfor分で回す
        threshold = t_range[1] * i / n_samples + t_range[0] * (1-(i/n_samples))
        n_bets, return_rate, n_hits, std = return_func(X, threshold)
        if n_bets > 2:
            gain[threshold] = {'return_rate': return_rate, 
                            'n_hits': n_hits,
                            'std': std,
                            'n_bets': n_bets}
    return pd.DataFrame(gain).T

def plot(df, label=' '):
    #標準偏差で幅をつけて薄くプロット
    plt.fill_between(df.index, y1=df['return_rate']-df['std'],
                y2=df['return_rate']+df['std'],
                alpha=0.3) #alphaで透明度を設定
    #回収率を実線でプロット
    plt.plot(df.index, df['return_rate'], label=label)
    plt.legend() #labelで設定した凡例を表示させる
    plt.grid(True) #グリッドをつける

def xlsx2pdf(pdf_file, ws):
    doc = SimpleDocTemplate( pdf_file, pagesize=(450*mm, 200*mm) )
    pdfmetrics.registerFont(TTFont('meiryo', '/Users/naoki/Downloads/font/meiryo/meiryo.ttc'))
    pdf_data = []
    data = []
    # Tableの作成
    for row in ws.rows:
        row_list = []
        for cell in row:
            if cell.number_format == '0.00%' and cell.value != '-': row_list.append(str(round(cell.value*100, 2))+'%')
            else: row_list.append(cell.value)
        data.append(row_list)
    tt = Table(data)
    tt.setStyle(TableStyle([
                                ('BACKGROUND',(0, 0),(-1, 0),colors.black),
                                ('BACKGROUND',(0, 14),(7, 14),colors.black),
                                ('TEXTCOLOR',(0, 14),(7, 14),colors.white),
                                ('TEXTCOLOR',(0, 0),(-1, 0),colors.white),
                                ('BACKGROUND',(0, 0),(0, 12),colors.black),
                                ('BACKGROUND',(0, 14),(0, -1),colors.black),
                                ('TEXTCOLOR',(0, 0),(0, 14),colors.white),
                                ('TEXTCOLOR',(0, 18),(0, 18),colors.white),
                                ('FONT', (0, 0), (-1, -1), "meiryo", 11),
                                ('GRID', (0, 0), (ws.max_column, ws.max_row), 0.25, colors.black),
                                ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                                ('ALIGN', (0, 0), (-1, -1), "CENTER")
                                ]))
    # 着色
    for row in ws.rows:
        for cell in row:
            cell_idx = (column_index_from_string(cell.coordinate[0])-1, int(cell.coordinate[1:])-1)
            if ws[cell.coordinate].fill == PatternFill(patternType='solid', fgColor='ffbf7f'):
                tt.setStyle(TableStyle([
                                ('BACKGROUND',cell_idx,cell_idx,colors.lightsalmon),
                                ]))
            elif ws[cell.coordinate].fill == PatternFill(patternType='solid', fgColor='a8d3ff'):
                tt.setStyle(TableStyle([
                                ('BACKGROUND',cell_idx,cell_idx,colors.lightblue),
                                ]))
            elif ws[cell.coordinate].fill == PatternFill(patternType='solid', fgColor='d3d3d3'):
                tt.setStyle(TableStyle([
                                ('BACKGROUND',cell_idx,cell_idx,colors.lightgrey),
                                ]))
    pdf_data.append(tt)
    doc.build(pdf_data)

def pdf2png(pdf_path, dpi=200, fmt='png'):
    png_path = pdf_path.replace('pdf', 'png')
    pdf_path = Path(pdf_path)
    png_path = Path(png_path)
    page = convert_from_path(pdf_path, dpi)
    page[0].save(png_path, fmt)

def div(a, b):
    if b == 0:
        return '-'
    else:
        return round(a / b, 4)

def make_total_sheet(total, excel_path, pdf_path):
    wb = xl.load_workbook(excel_path)
    columns=['単勝A', '三連単A', '三連複A', '単勝B', '三連単B', '三連複B', '単勝C', '三連単C', '三連複C', '単勝', '三連単', '三連複']
    df = pd.DataFrame(columns = columns)
    sheetnames = list(wb.sheetnames)
    if total in wb.sheetnames: sheetnames.remove(total)
    for name in sheetnames:
        ws_ = wb[name]
        tansho_rank = {'A': 0, 'B': 0, 'C': 0, '-': 0}
        sanren_rank = {'A': 0, 'B': 0, 'C': 0, '-': 0}  
        for i in range(2, 14):
            tansho_rank[ws.cell(row=i, column=2).value] += 100
            sanren_rank[ws.cell(row=i, column=3).value] += 2000
        s = pd.Series([
            ws_['F16'].value,
            ws_['G16'].value,
            ws_['H16'].value,
            ws_['F17'].value,
            ws_['G17'].value,
            ws_['H17'].value,
            ws_['F18'].value,
            ws_['G18'].value,
            ws_['H18'].value,
            ws_['F19'].value,
            ws_['G19'].value,
            ws_['H19'].value
            ], name=name, index=columns).replace('-', np.nan)
        s = s-1
        s["単勝A"] *= tansho_rank["A"]
        s["単勝B"] *= tansho_rank["B"]
        s["単勝C"] *= tansho_rank["C"]
        s["単勝"] *= (1200-tansho_rank["-"])
        s["三連複A"] *= sanren_rank["A"]
        s["三連複B"] *= sanren_rank["B"]
        s["三連複C"] *= sanren_rank["C"]
        s["三連複"] *= (24000-sanren_rank["-"])
        s["三連単A"] *= sanren_rank["A"]
        s["三連単B"] *= sanren_rank["B"]
        s["三連単C"] *= sanren_rank["C"]
        s["三連単"] *= (24000-sanren_rank["-"])
        df = df.append(s)
    df = df.round(-1)
    total_s = pd.Series(df.sum(), name='合計')
    df = df.append(total_s)
    writer = pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace')
    writer.book = wb
    writer.sheets = {ws_.title: ws_ for ws_ in wb.worksheets}
    df.to_excel(writer, sheet_name=total)
    writer.save()
    # 必要箇所にカラーリング
    ws = wb[total]
    side1 = Side(style='thin', color='000000')
    border1 = Border(top=side1, bottom=side1, left=side1, right=side1)
    for col in ws.columns:
        max_length = 0
        for i, cell in enumerate(col):
            coord = cell.coordinate
            max_length = max(max_length, len(str(cell.value)))
            ws[coord].border = border1
            if coord[0] == 'A' or coord[1:] == '1':
                ws[coord].fill = PatternFill(patternType='solid', fgColor='000000')
                ws[coord].font = Font(color="ffffff")
            try:
                if cell.value > 0:
                    ws[coord].fill = PatternFill(patternType='solid', fgColor='ffbf7f')
                elif cell.value < 0:
                    ws[coord].fill = PatternFill(patternType='solid', fgColor='a8d3ff')
            except:
                continue
    # 月収支シートをファイルの先頭に移動させる
    for ws_ in wb.worksheets:
        i = i+1
        if total in ws_.title:

            #先頭までの移動シート枚数
            Top_Sheet = i - 1
            #シート移動
            wb.move_sheet(ws,offset=-Top_Sheet)
    # xlsxをpdfに変換し、pdfディレクトリに保存する
    xlsx2pdf(pdf_path, ws)
    # pdfをpngに変換し、pngディレクトリに保存する
    pdf2png(pdf_path)
    wb.save(excel_path)
    wb.close()