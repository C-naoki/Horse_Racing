import sys
sys.path.extend(['../'])

import os
import requests
from module import make_venue_id_list

# ログインに必要な情報を環境変数から取り出す
USER = os.environ['private_gmail']
PASS = os.environ['netkeiba_pass']

url_login = "https://regist.netkeiba.com/account/?pid=login&action=auth"
payload = {
    'login_id': USER,
    'pswd': PASS
}
# プレミアムアカウントのデータを利用するためnetkeibaにログイン
session = requests.Session()
session.post(url_login, data=payload)

# スクレイピングする年の設定
scrape_year='2022'

# レース日
date = '2022/03/26'
# 日付の分割
year = date[0:4]
month = date[5:7]
day = date[8:10]
if month[0] == '0': month = month[1]
if day[0] == '0': day = day[1]

# race_id_listの要素からR情報を削除したもの
venue_id_list = make_venue_id_list(date.replace('/', ''))

# xlsxファイルを保存したいpath
excel_path = '/Users/naoki/git/Horse-Racing/results/'+year+'/xlsx/'+month+'月.xlsx'
# return_tablesのpath
tables_path = ['../_dat/train_data/overall/return_tables.pickle']

# dfのcolumns
predict_columns = ["本命馬ランク", "レースクラス", "1着予想◎", "2着予想○", "3着予想▲", "4着予想△", "5着予想☆", "6着予想×", "結果"]
result_columns = ["頭数", "単勝オッズ", "三連単オッズ", "三連複オッズ", "単勝回収金額", "三連単流し回収金額", "三連複流し回収金額"]
return_columns = ["着順", "単勝的中率", "複勝的中率(◎)", "三連単流し的中率", "三連複流し的中率", "単勝回収率", "三連単流し回収率", "三連複流し回収率"]
fukusho_columns = ["1着予想◎", "2着予想○", "3着予想▲", "ワイド", "三連複", "三連単"]
total_columns = ['単勝A', '複勝A', '三連単流しA', '三連複流しA', '単勝B', '複勝B', '三連単流しB', '三連複流しB', '単勝C', '複勝C', '三連単流しC', '三連複流しC', '単勝ABC', '複勝ABC', '三連単流しABC', '三連複流しABC', '単勝', '三連単流し', '三連複流し']

# 開催場所をidに変換するための辞書
place_dict = {
    '札幌':'01',  '函館':'02',  '福島':'03',  '新潟':'04',  '東京':'05', 
    '中山':'06',  '中京':'07',  '京都':'08',  '阪神':'09',  '小倉':'10'
}
# レースタイプをレース結果データと整合させるための辞書
race_type_dict = {
    '芝': '芝', 'ダ': 'ダート', '障': '障害'
}
# idからレースクラスに変換するための辞書
class_dict = {
    0: '新馬', 1: '未勝利', 2: '1勝クラス', 3: '2勝クラス', 4: '3勝クラス', 5: 'オープン'
}

# venue_id_listからrace_id_listを作成
race_id_dict = {}
venue_name = {}
sheet_name = {}
file_path = {}
dir_path = '../results/'+year+'/pdf/'+month+'月/'
for venue_id in venue_id_list:
    race_id_dict[venue_id] = {venue_id[4:6]: {venue_id[6:8]: [venue_id + str(i).zfill(2) for i in range(1, 13)]}}
    # 開催地名と記入するシート名
    venue_name[venue_id] = [k for k, v in place_dict.items() if v == venue_id[4:6]][0]
    sheet_name[venue_id] = day+"日"+venue_name[venue_id]
    # pdfファイルを保存したいpath
    file_path[venue_id] = '../results/'+year+'/pdf/'+month+'月/'+sheet_name[venue_id]+'.pdf'
file_path[month+'月収支'] = '../results/'+year+'/pdf/'+month+'月/'+month+'月収支.pdf'
file_path[month+'月的中率'] = '../results/'+year+'/pdf/'+month+'月/'+month+'月的中率.pdf'

# どのobjectiveを用いるか
objective_type = "lambdarank"
metric = "ndcg"

# 利用しない特徴量の選択
drop_list = ['date', 'jockey_id', 'breeder_id', 'owner_id', 'trainer_id', 'birthday', 'horse_id']

# 単勝予測のparams
params={
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'task': 'train',
    'feature_pre_filter': False,
    'boosting_type': 'gbdt',
    'eval_at': [1000],
    'lambda_l1': 1.3020837198994648e-07,
    'lambda_l2': 1.0558073318473672e-07,
    'num_leaves': 31,
    'feature_fraction': 0.6479999999999999,
    'bagging_fraction': 1.0,
    'bagging_freq': 0,
    'min_child_samples': 20
    }