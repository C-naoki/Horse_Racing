import numpy as np
import pandas as pd
import re
import time
from tqdm import tqdm
from ..functions import update_data
from environment.variables import *

class HorseResults:
    def __init__(self, horse_results):
        self.horse_results = horse_results[['日付', '着順', '賞金', '着差', '通過', '開催', '距離', 'タイム']]
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

        #horse_idをkeyにしてDataFrame型を格納
        horse_results = {}
        for horse_id in tqdm(horse_id_list):
            if len(pre_horse_results) and horse_id in pre_horse_results.index:
                continue
            time.sleep(1)
            try:
                url = 'https://db.netkeiba.com/horse/' + horse_id
                df = pd.read_html(url)[3]
                #受賞歴がある馬の場合、3番目に受賞歴テーブルが来るため、4番目のデータを取得する
                if df.columns[0]=='受賞歴':
                    df = pd.read_html(url)[4]
                df.index = [horse_id] * len(df)
                horse_results[horse_id] = df
            except IndexError:
                continue
            except Exception as e:
                print(e)
                break
            except:
                break

        #pd.DataFrame型にして一つのデータにまとめる        
        horse_results_df = pd.concat([horse_results[key] for key in horse_results])
        if len(pre_horse_results.index):
            return pd.concat([pre_horse_results, horse_results_df])
        else:
            return horse_results_df
    
    def preprocessing(self):
        df = self.horse_results.copy()

        # 着順に数字以外の文字列が含まれているものを取り除く
        df['着順'] = pd.to_numeric(df['着順'], errors='coerce')
        df.dropna(subset=['着順'], inplace=True)
        df['着順'] = df['着順'].astype(int)
        # 日付データ
        df["date"] = pd.to_datetime(df["日付"])
        df.drop(['日付'], axis=1, inplace=True)
        # 賞金のNaNを0で埋める
        df['賞金'].fillna(0, inplace=True)
        # 1着の着差を0にする
        df['着差'] = df['着差'].map(lambda x: 0 if x<0 else x)
        # タイムデータをfloat型に変換
        df['タイム'].fillna(0, inplace=True)
        df['time'] = df['タイム'].map(lambda x: int(str(x)[0])*60 + int(str(x)[2:4]) + int(str(x)[5])/10 if x!=0 else 0)
        
        #レース展開データ
        #n=1: 最初のコーナー位置, n=4: 最終コーナー位置
        def corner(x, n):
            if type(x) != str:
                return x
            elif n==4:
                return int(re.findall(r'\d+', x)[-1])
            elif n==1:
                return int(re.findall(r'\d+', x)[0])
        # first_corner: 1コーナー(約1/5)通過時の着順
        # final_corner: 4コーナー(約4/5)通過時の着順
        df['first_corner'] = df['通過'].map(lambda x: corner(x, 1))
        df['final_corner'] = df['通過'].map(lambda x: corner(x, 4))
        
        df['final_to_rank'] = df['final_corner'] - df['着順']
        df['first_to_rank'] = df['first_corner'] - df['着順']
        df['first_to_final'] = df['first_corner'] - df['final_corner']
        
        #開催場所
        df['開催'] = df['開催'].str.extract(r'(\D+)')[0].map(place_dict).fillna('11')
        #race_type
        df['race_type'] = df['距離'].str.extract(r'(\D+)')[0].map(race_type_dict)
        #距離は10の位を切り捨てる
        df['course_len'] = df['距離'].str.extract(r'(\d+)').astype(int) // 100
        df.drop(['距離'], axis=1, inplace=True)
        #インデックス名を与える
        df.index.name = 'horse_id'
        self.horse_results = df
        # ex. ) "course_len"(kind_listの要素)毎の"着順"(target_listの要素)
        # 過去の平均値を出したいデータ
        self.target_list = ['着順', '賞金', '着差', 'first_corner', 'final_corner', 'first_to_rank', 'first_to_final','final_to_rank', 'time']
        # 種類に分割したいデータ
        self.kind_list = ['course_len', 'race_type', '開催']
    
    #n_samplesレース分馬ごとに平均する
    def average(self, horse_id_list, date, n_samples='all'):
        target_df = self.horse_results.query('index in @horse_id_list')
        
        #過去何走分取り出すか指定
        if n_samples == 'all':
            filtered_df = target_df[target_df['date'] < date]
        elif n_samples > 0:
            filtered_df = target_df[target_df['date'] < date].sort_values('date', ascending=False).groupby(level=0).head(n_samples)
        else:
            raise Exception('n_samples must be >0')
        
	#集計して辞書型に入れる
        self.average_dict = {}
        self.average_dict['non_category'] = filtered_df.groupby(level=0)[self.target_list].mean().add_suffix('_{}R'.format(n_samples))
        for column in self.kind_list:
            self.average_dict[column] = filtered_df.groupby(['horse_id', column])[self.target_list].mean().add_suffix('_{}_{}R'.format(column, n_samples))
	
        #6/6追加: 馬の出走間隔追加のために、全レースの日付を変数latestに格納
        if n_samples == 5:
            self.latest = filtered_df.groupby('horse_id')['date'].max().rename('latest')
    
    def merge(self, results, date, n_samples='all'):
        df = results[results['date']==date]
        horse_id_list = df['horse_id']
        self.average(horse_id_list, date, n_samples)
        merged_df = df.merge(self.average_dict['non_category'], left_on='horse_id', right_index=True, how='left')
        for column in self.kind_list:
            merged_df = merged_df.merge(self.average_dict[column], 
                                        left_on=['horse_id', column],
                                        right_index=True, how='left')
	
        #6/6追加：馬の出走間隔追加のために、全レースの日付を変数latestに格納
        if n_samples == 5:
            merged_df = merged_df.merge(self.latest, left_on='horse_id', right_index=True, how='left')
        return merged_df
    
    def merge_all(self, results, n_samples='all'):
        date_list = results['date'].unique()
        merged_df = pd.concat([self.merge(results, date, n_samples) for date in tqdm(date_list)])
        return merged_df
