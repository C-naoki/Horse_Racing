#開催場所をidに変換するための辞書型
place_dict = {
    '札幌':'01',  '函館':'02',  '福島':'03',  '新潟':'04',  '東京':'05', 
    '中山':'06',  '中京':'07',  '京都':'08',  '阪神':'09',  '小倉':'10'
}
#レースタイプをレース結果データと整合させるための辞書型
race_type_dict = {
    '芝': '芝', 'ダ': 'ダート', '障': '障害'
}

# race_id_list
venue_id_list = ["2022060106", "2022070106", "2022100102"]
# レース日
date = '2022/01/16'
# 日付の分割
year = date[0:4]
month = date[5:7]
if month[0] == '0': month = month[1]
day = date[8:10]
if day[0] == '0': day = day[1]
# venue_id_listからrace_id_listを作成
race_id_list = {}
venue_name = {}
sheet_name = {}
pdf_path = {}
for venue_id in venue_id_list:
    race_id_list[venue_id] = [venue_id + str(i).zfill(2) for i in range(1, 13)]
    # 開催地名と記入するシート名
    venue_name[venue_id] = [k for k, v in place_dict.items() if v == race_id_list[venue_id][0][4:6]][0]
    sheet_name[venue_id] = day+"日"+venue_name[venue_id]
    # pdfファイルを保存したいpath
    pdf_path[venue_id] = '../results/'+year+'/pdf/'+month+'月/'+sheet_name[venue_id]+'.pdf'

# xlsxファイルを保存したいpath
excel_path = '../results/'+year+'/xlsx/'+month+'月.xlsx'
# return_tablesのpath
tables_path = ['../_dat/train_data/overall/return_tables.pickle']

# predict_dfのcolumns
predict_columns = ["本命馬ランク", "三連複ランク", "本命馬◎", "対抗馬○", "単穴馬▲", "連下馬1△", "連下馬2△", "連下馬3△"]
result_columns = ["単勝オッズ", "三連単結果", "三連単オッズ", "三連複オッズ", "単勝回収金額", "三連単回収金額", "三連複回収金額"]