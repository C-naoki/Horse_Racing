import pandas as pd
import numpy as np
import re
import time
import datetime
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm
from bs4 import BeautifulSoup
from .DataProcessor import DataProcessor
from ..functions import update_data
from environment import settings as sets


class Results(DataProcessor):
    def __init__(self, results, hr, p, obj="lambdarank", n_samples=[[5, 9, 'all'], [1, 2, 3, 4, 5]], past=True, avg=False, ped=False):
        super(Results, self).__init__()
        self.data = results
        self.make_data(hr, p, obj, n_samples, past, avg, ped)

    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)

    def make_data(self, hr, p, obj, n_samples, past, avg, ped):
        self.preprocessing()
        df = self.data_p.reset_index()
        df = df.rename(columns={'index': 'race_id'})
        # 各horse_idに対して、dateが最大値のデータを示すindexを取得(.idxmax())
        data_p_idx_max = df[['horse_id', 'date']].groupby('horse_id').idxmax()
        data_p_idx_max.columns = ['max_idx']
        # new_data_p = pd.merge(df, data_p_idx_max, left_index=True, right_on='max_idx')
        # self.data_p['weight_carry'] -= new_data_p['weight_carry']
        self.merge_horse_results(hr, n_samples[0], n_samples[1], past, avg)
        if ped:
            self.merge_peds(p.peds_e)
        self.process_categorical(n_samples)

    @staticmethod
    def scrape(race_id_dict, pre_race_results=pd.DataFrame()):
        """
        レース結果データをスクレイピングする関数
        Parameters:
        ----------
        race_id_dict : dict
            レースIDを開催地毎に分類して格納したもの
        Returns:
        ----------
        race_results_df : pandas.DataFrame
            全レース結果データをまとめてDataFrame型にしたもの
        """

        # race_idをkeyにしてDataFrame型を格納
        race_results = {}
        for place, race_id_place in race_id_dict.items():
            pre_kai = 0
            for kai, race_id_kai in race_id_place.items():
                if pre_kai:
                    continue
                indexerror_chk = -1
                pbar = tqdm(total=len(race_id_kai))
                for race_id in race_id_kai:
                    pbar.update(1)
                    pbar.set_description('Scrape Race data in "{} {}回"'.format(
                        [k for k, v in sets.place_dict.items() if v == str(place).zfill(2)][0],
                        kai
                    ))
                    if len(pre_race_results) and race_id in set(pre_race_results.index):
                        continue
                    try:
                        time.sleep(1)
                        url = "https://db.netkeiba.com/race/" + race_id
                        # メインとなるテーブルデータを取得
                        df = pd.read_html(url)[0]
                        html = sets.session.get(url)
                        html.encoding = "EUC-JP"
                        soup = BeautifulSoup(html.text, "html.parser")
                        # 天候、レースの種類、コースの長さ、馬場の状態、日付をスクレイピング
                        texts = (
                            soup.find("div", attrs={"class": "data_intro"}).find_all("p")[0].text
                            + soup.find("div", attrs={"class": "data_intro"}).find_all("p")[1].text
                        )
                        info = re.findall(r'\w+', texts)
                        for text in info:
                            if text in ["芝", "ダート"]:
                                df["race_type"] = [text] * len(df)
                            if "障" in text:
                                df["race_type"] = ["障害"] * len(df)
                                df["turn"] = ["障害"] * len(df)
                            if "m" in text:
                                df["course_len"] = [int(re.findall(r"(\d+)m", text)[0])] * len(df)
                            if text in ["良", "稍重", "重", "不良"]:
                                df["ground_state"] = [text] * len(df)
                            if text in ["曇", "晴", "雨", "小雨", "小雪", "雪"]:
                                df["weather"] = [text] * len(df)
                            if "年" in text:
                                df["date"] = [text] * len(df)
                            if "右" in text:
                                df["turn"] = ["右"] * len(df)
                            elif "左" in text:
                                df["turn"] = ["左"] * len(df)
                            elif "直線" in text:
                                df["turn"] = ["直線"] * len(df)
                            if "新馬" in text:
                                df["class"] = ["新馬"] * len(df)
                            elif "未勝利" in text:
                                df["class"] = ["未勝利"] * len(df)
                            elif "1勝クラス" in text or "500万下" in text:
                                df["class"] = ["1勝クラス"] * len(df)
                            elif "2勝クラス" in text or "1000万下" in text:
                                df["class"] = ["2勝クラス"] * len(df)
                            elif "3勝クラス" in text or "1600万下" in text:
                                df["class"] = ["3勝クラス"] * len(df)
                            elif "オープン" in text:
                                df["class"] = ["オープン"] * len(df)
                        df["race_num"] = [int(race_id[-2:])] * len(df)
                        df["day"] = [int(race_id[8:10])] * len(df)
                        df["kai"] = [int(race_id[6:8])] * len(df)
                        df["prize"] = [float(soup.find("table", attrs={"summary": "レース結果"}).find_all(
                            "td",
                            attrs={"class": re.compile("txt_r")}
                        )[4].text.replace(',', ''))] * len(df)
                        # 馬ID、騎手IDをスクレイピング
                        horse_id_list = []
                        horse_a_list = soup.find("table", attrs={"summary": "レース結果"}).find_all(
                            "a", attrs={"href": re.compile("^/horse")}
                        )
                        for a in horse_a_list:
                            horse_id = re.findall(r"\d+", a["href"])
                            horse_id_list.append(horse_id[0])
                        jockey_id_list = []
                        jockey_a_list = soup.find("table", attrs={"summary": "レース結果"}).find_all(
                            "a", attrs={"href": re.compile("^/jockey")}
                        )
                        for a in jockey_a_list:
                            jockey_id = re.findall(r"\d+", a["href"])
                            jockey_id_list.append(jockey_id[0])
                        df["horse_id"] = horse_id_list
                        df["jockey_id"] = jockey_id_list
                        # インデックスをrace_idにする
                        df.index = [race_id] * len(df)
                        df.sort_values('馬番', inplace=True)
                        race_results[race_id] = df
                    # 存在しないrace_idを飛ばし次のスクレイピングに移す
                    except IndexError:
                        if race_id[8:10] == '01':
                            pre_kai = 1
                        indexerror_chk = 1
                        break
                    # wifiの接続が切れた時などでも途中までのデータを返せるようにする
                    except Exception:
                        indexerror_chk = 0
                        break
                pbar.close()
                if indexerror_chk == 1:
                    print("{}回{}日のレースはまだ開催されていません。\n".format(str(race_id)[6:8], str(race_id)[8:10]))
                    if pre_kai:
                        print("別開催地のスクレイピングに移ります。\n")
                elif indexerror_chk == 0:
                    break
                elif indexerror_chk == -1 and not pre_kai:
                    print("対象のレースを全て取得し終わりました。\n")
            else:
                continue
            break
        # pd.DataFrame型にして一つのデータにまとめる
        try:
            race_results_df = pd.concat([race_results[key] for key in race_results])
        except ValueError:
            return pre_race_results
        if len(pre_race_results.index):
            return pd.concat([pre_race_results, race_results_df])
        else:
            return race_results_df

    # 前処理
    def preprocessing(self):
        df = self.data.copy()

        # 着順に数字以外の文字列が含まれているものを取り除く
        df['着順'] = pd.to_numeric(df['着順'], errors='coerce')
        df.dropna(subset=['着順'], inplace=True)
        df['着順'] = df['着順'].astype(int)
        df['bracket_num'] = df['枠番']
        df['horse_num'] = df['馬番']
        df['weight_carry'] = df['斤量']

        # 性齢を性と年齢に分ける
        df["sex"] = df["性齢"].map(lambda x: str(x)[0])
        df["age"] = df["性齢"].map(lambda x: str(x)[1:]).astype(int)

        # 単勝をfloatに変換
        df["odds"] = df["単勝"].astype(float)
        df['rank_binary'] = df['着順'].map(lambda x: 1 if x < 4 else 0)
        df['rank_regression'] = df['着順'].map(lambda x: 4-x if x < 4 else 0) * (df["odds"])**0.5
        df['rank_lambdarank'] = df['着順'].map(lambda x: int(10/x) if x < 4 else 0)
        # 距離は10の位を切り捨てる
        df["course_len"] = df["course_len"].astype(float) // 100
        # 障害レースの削除
        df = df[df['race_type'] != '障害']

        # 不要な列を削除
        df.drop(["タイム", "着差", "調教師", "性齢", "馬体重", '馬名', '騎手', '人気', '着順', '枠番', '馬番', '斤量', '単勝'], axis=1, inplace=True)
        df["date"] = pd.to_datetime(df["date"], format="%Y年%m月%d日")
        df["month_sin"] = df["date"].map(lambda x: np.sin(2*np.pi*(datetime.date(x.year, x.month, x.day)-datetime.date(x.year, 1, 1)).days/366))
        df["month_cos"] = df["date"].map(lambda x: np.cos(2*np.pi*(datetime.date(x.year, x.month, x.day)-datetime.date(x.year, 1, 1)).days/366))
        # 開催場所
        df['venue'] = df.index.map(lambda x: str(x)[4:6])

        # 6/6出走数追加
        df['n_horses'] = df.index.map(df.index.value_counts())

        self.data_p = df

    # カテゴリ変数の処理
    def process_categorical(self, n_samples):
        self.le_horse = LabelEncoder().fit(self.data_h['horse_id'])
        self.le_jockey = LabelEncoder().fit(self.data_h['jockey_id'])
        super().process_categorical(self.le_horse, self.le_jockey, n_samples_list1=n_samples[0], n_samples_list2=n_samples[1])
