import numpy as np
import pandas as pd
import re
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm
from ..functions import update_data
from environment.variables import *

class HorseResults:
    def __init__(self, horse_results):
        self.horse_results = horse_results[['日付', '着順', '通過', '開催', '距離', '上り', 'R', 'ﾀｲﾑ指数', '馬場指数', '備考', 'breeder_id', 'birthday', 'owner_id', 'trainer_id']]
        self.preprocessing()
    
    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)
    
    @staticmethod
    def scrape(horse_id_list, pre_horse_results=pd.DataFrame()):
        """
        馬の過去成績データをスクレイピングする関数
        Parameters:
        ----------
        horse_id_list : list
            馬IDのリスト
        Returns:
        ----------
        horse_results_df : pandas.DataFrame
            全馬の過去成績データをまとめてDataFrame型にしたもの
        """

        # horse_idをkeyにしてDataFrame型を格納
        horse_results = {}
        # プレミアムアカウントのデータを利用するためnetkeibaにログイン
        url_login = "https://regist.netkeiba.com/account/?pid=login&action=auth"
        payload = {
            'login_id': USER,
            'pswd': PASS
        }
        session = requests.Session()
        session.post(url_login, data=payload)
        for horse_id in tqdm(horse_id_list):
            if len(pre_horse_results) and horse_id in pre_horse_results.index:
                continue
            try:
                time.sleep(1)
                url = 'https://db.netkeiba.com/horse/' + horse_id
                html = session.get(url)
                html.encoding = "EUC-JP"
                df = pd.read_html(html.content)[3]
                #受賞歴がある馬の場合、3番目に受賞歴テーブルが来るため、4番目のデータを取得する
                if df.columns[0]=='受賞歴':
                    df = pd.read_html(url)[4]
                soup = BeautifulSoup(html.content, "html.parser")
                info_list = soup.find_all('table')[1].find_all('td')
                for info in info_list:
                    text = info.text
                    if re.sub('[年月日]', '', text).isdigit():
                        df['birthday'] = [int(datetime.strptime(text, "%Y年%m月%d日").strftime('%Y%m%d'))] * len(df)
                    try:
                        if "/trainer/" in info.find('a').get('href'):
                            df['trainer_id'] = [re.sub('trainer|/', '', info.find('a').get('href'))] * len(df)
                        if "/owner/" in info.find('a').get('href'):
                            df['owner_id'] = [re.sub('owner|/', '', info.find('a').get('href'))] * len(df)
                        if "/breeder/" in info.find('a').get('href'):
                            df['breeder_id'] = [re.sub('breeder|/', '', info.find('a').get('href'))] * len(df)
                    except:
                        continue
                df.index = [horse_id] * len(df)
                horse_results[horse_id] = df
            except IndexError:
                continue
            except Exception as e:
                print(e)
                break
            except:
                break
        # pd.DataFrame型にして一つのデータにまとめる
        try:       
            horse_results_df = pd.concat([horse_results[key] for key in horse_results])
        except ValueError:
            return pre_horse_results
        if len(pre_horse_results.index):
            return pd.concat([pre_horse_results, horse_results_df])
        else:
            return horse_results_df
    
    def preprocessing(self):
        df = self.horse_results.copy()

        # 着順に数字以外の文字列が含まれているものを取り除く
        df['着順'] = pd.to_numeric(df['着順'], errors='coerce')
        df.dropna(subset=['着順'], inplace=True)
        df['order'] = df['着順'].astype(int)
        # 日付データ
        df["date"] = pd.to_datetime(df["日付"])
        # 上り3F
        df['last3F'] = df['上り'].fillna(0).map(lambda x: int(str(x)[0:2]) + int(str(x)[3])/10 if x!=0 else 0)
        # レース情報がないデータはほとんどの情報が欠落しているため削除する。
        df = df[np.isnan(df['R'])==False]
        df['rece_num'] = df['R'].fillna(0).astype(int)
        df['time_idx'] = df['馬場指数'].replace('**', 0).fillna(0).astype(float)
        df['ground_state_idx'] = df['馬場指数'].replace('**', 0).fillna(0).astype(float)
        df['birthday'] = df['birthday'].astype(int)
        
        #レース展開データ
        #n=1: 最初のコーナー位置, n=4: 最終コーナー位置
        def corner(x, n):
            if type(x) != str:
                return x
            elif n==4:
                return int(re.findall(r'\d+', x)[-1])
            elif n==1:
                return int(re.findall(r'\d+', x)[0])
        def remarks(x):
            if x == '出遅れ':
                return 1
            elif x == '出脚鈍い':
                return 2
            elif x == '躓く':
                return 3
            elif x == '好発':
                return 4
            else:
                return 0
        # first_corner: 1コーナー(約1/5)通過時の着順
        # final_corner: 4コーナー(約4/5)通過時の着順
        df['first_corner'] = df['通過'].map(lambda x: corner(x, 1))
        df['final_corner'] = df['通過'].map(lambda x: corner(x, 4))
        
        df['final_to_rank'] = df['final_corner'] - df['order']
        df['first_to_rank'] = df['first_corner'] - df['order']
        df['first_to_final'] = df['first_corner'] - df['final_corner']
        df['remark'] = df['備考'].map(lambda x: remarks(x))
        
        #開催場所
        df['venue'] = df['開催'].str.extract(r'(\D+)')[0].map(place_dict).fillna('11')
        #race_type
        df['race_type'] = df['距離'].str.extract(r'(\D+)')[0].map(race_type_dict)
        #距離は10の位を切り捨てる
        df['course_len'] = df['距離'].str.extract(r'(\d+)').astype(int) // 100
        df.drop(['距離', '日付', '着順', '開催', 'R', 'ﾀｲﾑ指数', '馬場指数', '備考'], axis=1, inplace=True)
        #インデックス名を与える
        df.index.name = 'horse_id'
        self.horse_results = df
        # str型のデータをラベルエンコーディングする
        self.encode()
        # ex. ) "course_len"(kind_listの要素)毎の"着順"(avg_target_listの要素)
        # 過去の平均値を出したいデータ
        self.avg_target_list = ['order', 'first_corner', 'final_corner', 'first_to_rank', 'first_to_final','final_to_rank', 'last3F', 'time_idx', 'ground_state_idx']
        self.past_target_list = ['rece_num', 'remark'] + self.avg_target_list
        # 種類に分割したいデータ
        self.kind_list = ['course_len', 'race_type', 'venue']

    def encode(self):
        df = self.horse_results.copy()
        for column in ["owner_id", "trainer_id", "breeder_id"]:
            df[column] = LabelEncoder().fit_transform(df[column].fillna('Na'))
            df[column] = df[column].astype('category')
        self.horse_results = df

    #n_samplesレース分馬ごとに平均する
    def average(self, horse_id_list, date, n_samples='all'):
        # horse_id_listに含まれたindexに絞る
        target_df = self.horse_results.query('index in @horse_id_list')
        
        # 過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df['date'] < date]
        elif n_samples > 0:
            filtered_df = target_df[target_df['date'] < date].sort_values('date', ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')
        
        # 集計して辞書型に入れる
        self.average_dict = {}
        # filtered_dfをhorse_id毎に分割し、平均値を出す。そして、その平均値の名前を元の名前に_{}Rをつけた名前とする。
        # ex.) filterd_dfでorder(self.avg_target_listの要素の一つ)を上からn_samples(=5)個ずつ取得する。その平均値に対して、名前をorder_5Rと再決定する。
        self.average_dict['non_category'] = filtered_df.groupby(level=0)[self.avg_target_list].mean().add_suffix('_{}R'.format(n_samples))
        for column in self.kind_list:
            self.average_dict[column] = filtered_df.groupby(['horse_id', column])[self.avg_target_list].mean().add_suffix('_{}_{}R'.format(column, n_samples))
    
    def merge_average(self, results, date, n_samples='all'):
        # ある日付に関する情報のみに絞る
        df = results[results['date']==date]
        # horse_id_listを取得する
        horse_id_list = df['horse_id']
        self.average(horse_id_list, date, n_samples)
        merged_df = df.merge(self.average_dict['non_category'], left_on='horse_id', right_index=True, how='left')
        for column in self.kind_list:
            merged_df = merged_df.merge(self.average_dict[column], left_on=['horse_id', column], right_index=True, how='left')
        return merged_df

    def merge_average_all(self, results, n_samples='all'):
        # 日付の情報を取得する
        date_list = results['date'].unique()
        temp_list = list()
        pbar = tqdm(total=len(date_list))
        for date in date_list:
            pbar.update(1)
            pbar.set_description("merge {} data".format(str(n_samples)+(" "*(3-len(str(n_samples))))))
            temp_list.append(self.merge_average(results, date, n_samples))
        merged_df = pd.concat(temp_list)
        return merged_df

    def past(self, horse_id_list, date, n_samples, chk):
        target_df = self.horse_results.query('index in @horse_id_list')
        filtered_df = target_df[target_df['date'] < date].sort_values('date', ascending=False).groupby(level=0).head(n_samples)
        self.past_dict = {}
        self.past_dict['non_category'] = filtered_df.groupby(level=0)[self.past_target_list].tail(1).add_suffix('_{}R'.format(n_samples)).add_prefix('p_')
        if chk == 0:
            self.latest = filtered_df.groupby('horse_id')['date'].max().rename('latest')

    def merge_past(self, results, date, n_samples, chk):
        # ある日付に関する情報のみに絞る
        df = results[results['date']==date]
        # horse_id_listを取得する
        horse_id_list = df['horse_id']
        self.past(horse_id_list, date, n_samples, chk)
        merged_df = df.merge(self.past_dict['non_category'], left_on='horse_id', right_index=True, how='left')
        if chk == 0:
            merged_df = merged_df.merge(self.latest, left_on='horse_id', right_index=True, how='left')
        return merged_df

    def merge_past_all(self, results, n_samples, chk):
        # 日付の情報を取得する
        date_list = results['date'].unique()
        temp_list = list()
        pbar = tqdm(total=len(date_list))
        for date in date_list:
            pbar.update(1)
            pbar.set_description("merge p{} data".format(str(n_samples)+(" "*(2-len(str(n_samples))))))
            temp_list.append(self.merge_past(results, date, n_samples, chk))
        merged_df = pd.concat(temp_list)
        return merged_df
