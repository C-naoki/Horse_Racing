import sys
sys.path.extend(['.../', './'])

import time
import datetime
import requests
import re
import numpy as np
import pandas as pd
from . import DataProcessor
from tqdm import tqdm
from bs4 import BeautifulSoup
from environment.variables import place_dict

class ShutubaTable(DataProcessor):
    def __init__(self, shutuba_tables):
        super(ShutubaTable, self).__init__()
        self.data = shutuba_tables
    
    @classmethod
    def scrape(cls, race_id_list, date, place):
        pbar = tqdm(total=len(race_id_list))
        data = pd.DataFrame()
        for race_id in race_id_list:
            pbar.update(1)
            pbar.set_description("scrape shutuba table in {}".format([k for k, v in place_dict.items() if v == place][0]))
            time.sleep(1)
            url = 'https://race.netkeiba.com/race/shutuba.html?race_id=' + race_id
            df = pd.read_html(url)[0]
            df = df.T.reset_index(level=0, drop=True).T
            html = requests.get(url)
            html.encoding = "EUC-JP"
            soup = BeautifulSoup(html.text, "html.parser")
            texts = soup.find('div', attrs={'class': 'RaceData01'}).text
            texts = re.findall(r'\w+', texts)
            for text in texts:
                if 'm' in text:
                    df['course_len'] = [int(re.findall(r"(\d+)m", text)[0])] * len(df)
                if text in ["曇", "晴", "雨", "小雨", "小雪", "雪"]:
                    df["weather"] = [text] * len(df)
                if text in ["良", "稍重", "重"]:
                    df["ground_state"] = [text] * len(df)
                if '不' in text:
                    df["ground_state"] = ['不良'] * len(df)
                # 2020/12/13追加
                if '稍' in text:
                    df["ground_state"] = ['稍重'] * len(df)
                if '芝' in text:
                    df['race_type'] = ['芝'] * len(df)
                if '障' in text:
                    df['race_type'] = ['障害'] * len(df)
                if 'ダ' in text:
                    df['race_type'] = ['ダート'] * len(df)
            df['date'] = [date] * len(df)
            # horse_id
            horse_id_list = []
            horse_td_list = soup.find_all("td", attrs={'class': 'HorseInfo'})
            for td in horse_td_list:
                horse_id = re.findall(r'\d+', td.find('a')['href'])[0]
                horse_id_list.append(horse_id)
            # jockey_id
            jockey_id_list = []
            jockey_td_list = soup.find_all("td", attrs={'class': 'Jockey'})
            for td in jockey_td_list:
                jockey_id = re.findall(r'\d+', td.find('a')['href'])[0]
                jockey_id_list.append(jockey_id)
            df['horse_id'] = horse_id_list
            df['jockey_id'] = jockey_id_list
            df.index = [race_id] * len(df)
            data = data.append(df)
        return cls(data)

    #前処理
    def preprocessing(self):
        df = self.data.copy()
        
        df["性"] = df["性齢"].map(lambda x: str(x)[0])
        df["年齢"] = df["性齢"].map(lambda x: str(x)[1:]).astype(int)
        
        df["date"] = pd.to_datetime(df["date"])
        df["month_sin"] = df["date"].map(lambda x: np.sin(2*np.pi*(datetime.date(x.year, x.month, x.day)-datetime.date(x.year, 1, 1)).days/366))
        df["month_cos"] = df["date"].map(lambda x: np.cos(2*np.pi*(datetime.date(x.year, x.month, x.day)-datetime.date(x.year, 1, 1)).days/366))
        
        df['枠'] = df['枠'].astype(int)
        df['馬番'] = df['馬番'].astype(int)
        df['斤量'] = df['斤量'].astype(int)

        df['開催'] = df.index.map(lambda x:str(x)[4:6])

        #6/6出走数追加
        df['n_horses'] = df.index.map(df.index.value_counts())
        df["course_len"] = df["course_len"].astype(float) // 100

        # 使用する列を選択
        df = df[['枠', '馬番', '斤量', 'course_len', 'weather','race_type', 'ground_state', 'date', 'horse_id', 'jockey_id', '性', '年齢','開催', 'n_horses', 'month_cos', 'month_sin']]
        
        self.data_p = df.rename(columns={'枠': '枠番'})
