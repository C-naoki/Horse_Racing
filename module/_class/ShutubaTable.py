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
from environment.settings import place_dict

class ShutubaTable(DataProcessor):
    def __init__(self, shutuba_tables, r, hr, p, n_samples, past, avg, ped):
        super(ShutubaTable, self).__init__()
        self.data = shutuba_tables
        self.make_data(r, hr, p, n_samples, past, avg, ped)
    
    def make_data(self, r, hr, p, n_samples, past, avg, ped):
        self.preprocessing()
        self.merge_horse_results(hr, n_samples[0], n_samples[1], past, avg)
        if ped:
            self.merge_peds(p.peds_e)
        self.process_categorical(r.le_horse, r.le_jockey)

    @classmethod
    def scrape(cls, race_id_dict, date, venue_id, r, hr, p, n_samples=[[5, 9, 'all'], [1, 2, 3]], past=True, avg=False, ped=False):
        race_id_list = race_id_dict[venue_id][venue_id[4:6]][venue_id[6:8]]
        place = venue_id[4:6]
        pbar = tqdm(total=len(race_id_list))
        data = pd.DataFrame()
        for race_id in race_id_list:
            pbar.update(1)
            pbar.set_description("scrape shutuba table in {} {}回".format([k for k, v in place_dict.items() if v == place][0], venue_id[6:8]))
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
                if "右" in text:
                    df["turn"] = [1] * len(df)
                elif "左" in text:
                    df["turn"] = [2] * len(df)
            texts = soup.find('div', attrs={'class': 'RaceData02'}).text
            texts = re.findall(r'\w+', texts)
            for text in texts:
                if '賞金' in text:
                    df["prize"] = [float(texts[texts.index(text)+1])] * len(df)
                if text in ["新馬", "未勝利", "１勝クラス", "２勝クラス", "３勝クラス", "オープン"]:
                    df['class'] = [["新馬", "未勝利", "１勝クラス", "２勝クラス", "３勝クラス", "オープン"].index(text)] * len(df)
            df["race_num"] = [int(race_id[-2:])] * len(df)
            df["day"] = [int(race_id[8:10])] * len(df)
            df["kai"] = [int(race_id[6:8])] * len(df)
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
        return cls(data, r, hr, p, n_samples, past, avg, ped)

    #前処理
    def preprocessing(self):
        df = self.data.copy()
        
        df["sex"] = df["性齢"].map(lambda x: str(x)[0])
        df["age"] = df["性齢"].map(lambda x: str(x)[1:]).astype(int)
        
        df["date"] = pd.to_datetime(df["date"])
        df["month_sin"] = df["date"].map(lambda x: np.sin(2*np.pi*(datetime.date(x.year, x.month, x.day)-datetime.date(x.year, 1, 1)).days/366))
        df["month_cos"] = df["date"].map(lambda x: np.cos(2*np.pi*(datetime.date(x.year, x.month, x.day)-datetime.date(x.year, 1, 1)).days/366))
        
        df['bracket_num'] = df['枠'].astype(int)
        df['horse_num'] = df['馬番'].astype(int)
        df['weight_carry'] = df['斤量'].astype(int)

        df['venue'] = df.index.map(lambda x:str(x)[4:6])

        #6/6出走数追加
        df['n_horses'] = df.index.map(df.index.value_counts())
        df["course_len"] = df["course_len"].astype(float) // 100

        # 使用する列を選択
        df = df[['bracket_num', 'horse_num', 'weight_carry', 'course_len', 'weather','race_type', 'ground_state', 'date', 'horse_id', 'jockey_id', 'sex', 'age', 'venue', 'n_horses', 'month_cos', 'month_sin', 'turn', 'race_num', 'day', 'kai', 'prize', 'class']]
        
        self.data_p = df.rename(columns={'枠': '枠番'})
