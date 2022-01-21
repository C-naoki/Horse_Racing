import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string
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
            row_list.append(cell.value)
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
    if b == 0 or a == 0:
        return 0
    else:
        return a / b