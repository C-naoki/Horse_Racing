import pandas as pd
import numpy as np


class DataProcessor:
    """
    Attributes:
    ----------
    data : pd.DataFrame
        rawデータ
    data_p : pd.DataFrame
        preprocessing後のデータ
    data_h : pd.DataFrame
        merge_horse_results後のデータ
    data_pe : pd.DataFrame
        merge_peds後のデータ
    data_c : pd.DataFrame
        process_categorical後のデータ
    no_peds: Numpy.array
        merge_pedsを実行した時に、血統データが存在しなかった馬のhorse_id一覧
    """

    def __init__(self):
        self.data = pd.DataFrame()
        self.data_p = pd.DataFrame()
        self.data_h = pd.DataFrame()
        self.data_pe = pd.DataFrame()
        self.data_c = pd.DataFrame()

    # 全てのn_samplesごとにhorse_dataを追加する関数
    def merge_horse_results(self, hr, n_samples_list1=[5, 9, 'all'], n_samples_list2=[1, 2, 3, 4, 5], past=True, avg=True):
        """
        馬の過去成績データから、
        n_samples_listで指定されたレース分の着順と賞金の平均を追加してdata_hに返す
        Parameters:
        ----------
        hr : HorseResults
            馬の過去成績データ
        n_samples_list : list, default [5, 9, 'all']
            過去何レース分追加するか
        """

        self.data_h = self.data_p.copy()
        temp_df = hr.horse_results[['breeder_id', 'birthday', 'owner_id', 'trainer_id']]
        temp_df = temp_df[~temp_df.duplicated()]
        self.data_h = self.data_h.merge(temp_df, left_on='horse_id', right_index=True, how='left')
        if past:
            for i, n_samples in enumerate(n_samples_list2):
                self.data_h = hr.merge_past_all(self.data_h, n_samples=n_samples, isZero=i)
        if avg:
            for n_samples in n_samples_list1:
                self.data_h = hr.merge_average_all(self.data_h, n_samples=n_samples)

        # 6/6追加： 馬の出走間隔追加
        self.data_h['interval'] = (self.data_h['date'] - self.data_h['latest']).dt.days
        self.data_h['diff_weight_carry'] = self.data_h['weight_carry']
        self.data_h.drop(['venue', 'latest'], axis=1, inplace=True)

    def merge_peds(self, peds):
        """
        5世代分血統データを追加してdata_peに返す
        Parameters:
        ----------
        peds : Peds.peds_e
            Pedsクラスで加工された血統データ。
        """

        self.data_pe = self.data_h.merge(peds, left_on='horse_id', right_index=True, how='left')
        self.no_peds = self.data_pe[self.data_pe['peds_0'].isnull()]['horse_id'].unique()
        if len(self.no_peds) > 0:
            print('scrape peds at horse_id_list "no_peds"')

    def process_categorical(self, le_horse, le_jockey, n_samples_list1=[5, 9, 'all'], n_samples_list2=[1, 2, 3, 4, 5]):
        """
        カテゴリ変数を処理してdata_cに返す
        Parameters:
        ----------
        le_horse : sklearn.preprocessing.LabelEncoder
            horse_idを0始まりの整数に変換するLabelEncoderオブジェクト。
        le_jockey : sklearn.preprocessing.LabelEncoder
            jockey_idを0始まりの整数に変換するLabelEncoderオブジェクト。
        results_m : Results.data_pe
            ダミー変数化のとき、ResultsクラスとShutubaTableクラスで列を合わせるためのもの
        """

        if len(self.data_pe) == 0:
            df = self.data_h.copy()
        else:
            df = self.data_pe.copy()

        # ラベルエンコーディング。horse_id, jockey_idを0始まりの整数に変換
        mask_horse = df['horse_id'].isin(le_horse.classes_)
        new_horse_id = df['horse_id'].mask(mask_horse).dropna().unique()
        le_horse.classes_ = np.concatenate([le_horse.classes_, new_horse_id])
        df['horse_id'] = le_horse.transform(df['horse_id'])
        mask_jockey = df['jockey_id'].isin(le_jockey.classes_)
        new_jockey_id = df['jockey_id'].mask(mask_jockey).dropna().unique()
        le_jockey.classes_ = np.concatenate([le_jockey.classes_, new_jockey_id])
        df['jockey_id'] = le_jockey.transform(df['jockey_id'])

        # horse_id, jockey_idをpandasのcategory型に変換
        df['horse_id'] = df['horse_id'].astype('category')
        df['jockey_id'] = df['jockey_id'].astype('category')

        # そのほかのカテゴリ変数をpandasのcategory型に変換してからダミー変数化
        # 列を一定にするため
        weathers = ["曇", "晴", "雨", "小雨", "小雪", "雪"]
        race_types = ["芝", "ダート"]
        ground_states = ["良", "稍重", "重", "不良"]
        sexes = ['牡', '牝', 'セ']
        turns = ['右', '左', '直線']
        classes = ["新馬", "未勝利", "１勝クラス", "２勝クラス", "３勝クラス", "オープン"]
        df['weather'] = pd.Categorical(df['weather'], weathers)
        df['race_type'] = pd.Categorical(df['race_type'], race_types)
        df['ground_state'] = pd.Categorical(df['ground_state'], ground_states)
        df['sex'] = pd.Categorical(df['sex'], sexes)
        df['turn'] = pd.Categorical(df['turn'], turns)
        df['class'] = pd.Categorical(df['class'], classes)
        col_name_list = list()
        for past, past_list in {'remark': ['0', '出遅れ', '出脚鈍い', '躓く', '好発']}.items():
            for i in n_samples_list2:
                col_name = 'p_'+past+'_'+str(i)+'R'
                col_name_list.append(col_name)
                df[col_name].fillna(0, inplace=True)
                unique_data = past_list
                df[col_name] = pd.Categorical(df[col_name], unique_data)
        df = pd.get_dummies(df, columns=['weather', 'race_type', 'ground_state', 'sex', 'turn', 'class']+col_name_list, drop_first=True)

        self.data_c = df
