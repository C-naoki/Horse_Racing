import os
# ログインに必要な情報を環境変数から取り出す
USER = os.environ['private_gmail']
PASS = os.environ['netkeiba_pass']

# スクレイピングする年の設定
scrape_year='2022'

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
    'lambda_l1': 2.0374919161324458e-05,
    'lambda_l2': 5.198946634943905,
    'num_leaves': 16,
    'feature_fraction': 0.716,
    'bagging_fraction': 1.0,
    'bagging_freq': 0,
    'min_child_samples': 20
    }

# race_id_listの要素からしたR情報を削除したもの
venue_id_list = ["2022070102", '2022060102']
# レース日
date = '2022/01/08'
# 日付の分割
year = date[0:4]
month = date[5:7]
if month[0] == '0': month = month[1]
day = date[8:10]
if day[0] == '0': day = day[1]

# xlsxファイルを保存したいpath
excel_path = '/Users/naoki/git/Horse-Racing/results/'+year+'/xlsx/'+month+'月.xlsx'
# return_tablesのpath
tables_path = ['../_dat/train_data/overall/return_tables.pickle']

# dfのcolumns
predict_columns = ["本命馬ランク", "レースランク", "本命馬◎", "対抗馬○", "単穴馬▲", "連下馬1△", "連下馬2△", "連下馬3△", "頭数"]
result_columns = ["単勝オッズ", "三連単結果", "三連単オッズ", "三連複オッズ", "単勝回収金額", "三連単回収金額", "三連複回収金額"]
return_columns = ["着順", "単勝的中率", "複勝的中率(◎)", "三連単的中率", "三連複的中率", "単勝回収率", "三連単回収率", "三連複回収率"]
fukusho_columns = ["本命馬◎", "対抗馬○", "単穴馬▲", "ワイド"]
total_columns = ['単勝A', '複勝A', '三連単A', '三連複A', '単勝B', '複勝B', '三連単B', '三連複B', '単勝C', '複勝C', '三連単C', '三連複C', '単勝ABC', '複勝ABC', '三連単ABC', '三連複ABC', '単勝', '三連単', '三連複']

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