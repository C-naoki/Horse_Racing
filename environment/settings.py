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
scrape_year = '2022'
# レース日
date = '2022/05/21'
# 対象の月に実施された全てのレース対して予想を行うかどうか
all_date = 0
# 日付の分割
year = date[0:4]
month = date[5:7]
day = date[8:10]
if month[0] == '0':
    month = month[1]
if day[0] == '0':
    day = day[1]
n_samples = [[5, 9, 'all'], [1, 2, 3, 4, 5]]

# race_id_listの要素からR情報を削除したもの
venue_id_list = make_venue_id_list(date.replace('/', ''))

# xlsxファイルを保存したいpath
excel_path = '/Users/naoki/git/Horse-Racing/results/'+year+'/xlsx/'+month+'月.xlsx'
# return_tablesのpath
tables_path = ['../_dat/train_data/overall/return_tables.pickle']

# dfのcolumns
predict_columns = ["本命馬ランク", "レースクラス", "1着予想◎", "2着予想○", "3着予想▲", "4着予想△", "5着予想☆", "6着予想×", "結果"]
result_columns = ["頭数", "単勝オッズ", "1着複勝オッズ", "2着複勝オッズ", "3着複勝オッズ", "三連単オッズ", "三連複オッズ", "単勝回収金額", "複勝回収金額", "三連単流し回収金額", "三連複流し回収金額"]
return1_columns = ["着順", "単勝的中率", "複勝的中率", "三連単流し的中率", "三連複流し的中率", "単勝回収率", "複勝回収率", "三連単流し回収率", "三連複流し回収率"]
return2_columns = ["ワイド", "三連複", "三連単"]
total_columns = [
    '単勝A', '複勝A', '三連単流しA', '三連複流しA',
    '単勝B', '複勝B', '三連単流しB', '三連複流しB',
    '単勝C', '複勝C', '三連単流しC', '三連複流しC',
    '単勝ABC', '複勝ABC', '三連単流しABC', '三連複流しABC',
    '単勝', '複勝', '三連単流し', '三連複流し'
]

# 開催場所をidに変換するための辞書
place_dict = {
    '札幌': '01', '函館': '02', '福島': '03', '新潟': '04', '東京': '05',
    '中山': '06', '中京': '07', '京都': '08', '阪神': '09', '小倉': '10'
}
# レースタイプをレース結果データと整合させるための辞書
race_type_dict = {
    '芝': '芝', 'ダ': 'ダート', '障': '障害'
}
# idからレースクラスに変換するための辞書
class_dict = {
    0: '新馬', 1: '未勝利', 2: '1勝クラス', 3: '2勝クラス', 4: '3勝クラス', 5: 'オープン'
}

# どのobjectiveを用いるか
objective_type = "regression"
metric = "rmse"

# 利用しない特徴量の選択
drop_list = ['jockey_id', 'breeder_id', 'owner_id', 'trainer_id', 'birthday', 'horse_id']

params = {
    'objective': 'regression',
    'metric': 'rmse',
    'feature_pre_filter': False,
    'boosting_type': 'gbdt',
    'lambda_l1': 6.6377046563499,
    'lambda_l2': 0.009493220785902975,
    'num_leaves': 31,
    'feature_fraction': 0.748,
    'bagging_fraction': 1.0,
    'bagging_freq': 0,
    'min_child_samples': 20}
