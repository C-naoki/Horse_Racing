import os
USER = os.environ['private_gmail']
PASS = os.environ['netkeiba_pass']

# 開催場所をidに変換するための辞書型
place_dict = {
    '札幌':'01',  '函館':'02',  '福島':'03',  '新潟':'04',  '東京':'05', 
    '中山':'06',  '中京':'07',  '京都':'08',  '阪神':'09',  '小倉':'10'
}
# レースタイプをレース結果データと整合させるための辞書型
race_type_dict = {
    '芝': '芝', 'ダ': 'ダート', '障': '障害'
}
# どのobjectiveを用いるか
objective = "lambdarank"

# 利用しない特徴量の選択(rankは正解データ)
drop_list = ['date', 'jockey_id', 'trainer_id', 'owner_id']

# 単勝予測のparams
params={
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [100],
    'feature_pre_filter': False,
    'lambda_l1': 9.18791635108344e-05,
    'lambda_l2': 4.130283126875665e-05,
    'num_leaves': 224,
    'feature_fraction': 0.58,
    'bagging_fraction': 1.0,
    'bagging_freq': 0,
    'min_child_samples': 20}

# race_id_listの要素からしたR情報を削除したもの
venue_id_list = ["2022050105", "2022090101", "2022100201"]
# レース日
date = '2022/02/12'
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
file_path = {}
dir_path = '../results/'+year+'/pdf/'+month+'月/'
for venue_id in venue_id_list:
    race_id_list[venue_id] = {venue_id[4:6]: {venue_id[6:8]: [venue_id + str(i).zfill(2) for i in range(1, 13)]}}
    # 開催地名と記入するシート名
    venue_name[venue_id] = [k for k, v in place_dict.items() if v == venue_id[4:6]][0]
    sheet_name[venue_id] = day+"日"+venue_name[venue_id]
    # pdfファイルを保存したいpath
    file_path[venue_id] = '../results/'+year+'/pdf/'+month+'月/'+sheet_name[venue_id]+'.pdf'

# xlsxファイルを保存したいpath
excel_path = '/Users/naoki/git/Horse-Racing/results/'+year+'/xlsx/'+month+'月.xlsx'
# excel_path = '../results/'+year+'/xlsx/'+month+'月.xlsx'
# return_tablesのpath
tables_path = ['../_dat/train_data/overall/return_tables.pickle']

# dfのcolumns
predict_columns = ["本命馬ランク", "三連複ランク", "本命馬◎", "対抗馬○", "単穴馬▲", "連下馬1△", "連下馬2△", "連下馬3△", "頭数"]
result_columns = ["単勝オッズ", "三連単結果", "三連単オッズ", "三連複オッズ", "単勝回収金額", "三連単回収金額", "三連複回収金額"]
return_columns = ["着順", "単勝的中率", "三連単的中率", "三連複的中率", "単勝回収率", "三連単回収率", "三連複回収率"]