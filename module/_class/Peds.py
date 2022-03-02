import pandas as pd
import numpy as np
import time
import requests
import re
from ..functions import update_data
from tqdm import tqdm
from sklearn.preprocessing import LabelEncoder
from bs4 import BeautifulSoup


class Peds:
    def __init__(self, peds):
        self.peds = peds
        self.peds_e = pd.DataFrame() # after label encoding and transforming into category
        self.encode()
    
    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)
    
    @staticmethod
    def scrape(horse_id_list, pre_ped_results=pd.DataFrame()):
        """
        血統データをスクレイピングする関数
        Parameters:
        ----------
        horse_id_list : list
            馬IDのリスト
        Returns:
        ----------
        peds_df : pandas.DataFrame
            全血統データをまとめてDataFrame型にしたもの
        """

        peds_dict = {}
        for horse_id in tqdm(horse_id_list):
            if len(pre_ped_results) and horse_id in pre_ped_results.index:
                continue
            try:
                time.sleep(1)
                transrate_num = [0, 2, 6, 14, 30, 31, 15, 32, 33, 7, 16, 34, 35, 17, 36, 37, 3, 8, 18, 38, 39, 19, 40, 41, 9, 20, 42, 43, 21, 44, 45, 1, 4, 10, 22, 46, 47, 23, 48, 49, 11, 24, 50, 51, 25, 52, 53, 5, 12, 26, 54, 55, 27, 56, 57, 13, 28, 58, 59, 29, 60, 61]
                ped = pd.Series([0] * len(transrate_num)).rename(horse_id)
                url = "https://db.netkeiba.com/horse/ped/" + horse_id
                # 自作
                html = requests.get(url)
                soup = BeautifulSoup(html.content, "html.parser")
                texts = soup.find("table").find_all("td")
                for idx, t in enumerate(texts):
                    try:
                        if len(t.find("a").get('href')[7:-1]) != 0: ped[transrate_num[idx]] = t.find("a").get('href')[7:-1]
                        else: ped[transrate_num[idx]] = np.nan
                    except:
                        ped[transrate_num[idx]] = np.nan
                ped = ped.rename(horse_id)
                peds_dict[horse_id] = ped.reset_index(drop=True)
            except IndexError:
                continue
            except Exception as e:
                print(e)
                break
            except:
                break
        #列名をpeds_0, ..., peds_61にする
        try:
            peds_df = pd.concat([peds_dict[key] for key in peds_dict], axis=1).T.add_prefix('peds_')
        except ValueError:
            return pre_ped_results
        if len(pre_ped_results.index):
            return pd.concat([pre_ped_results, peds_df])
        else:
            return peds_df
    
    def encode(self):
        df = self.peds.copy()
        for column in df.columns:
            df = df.astype('str')
            df[column] = LabelEncoder().fit_transform(df[column].fillna('Na'))
        self.peds_e = df.astype('category')
