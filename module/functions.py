import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

def update_data(old, new):
    """
    Parameters:
    ----------
    old : pandas.DataFrame
        古いデータ
    new : pandas.DataFrame
        新しいデータ
    """

    filtered_old = old[~old.index.isin(new.index)]
    return pd.concat([filtered_old, new])

def split_data(df, test_size=0.3):
    sorted_id_list = df.sort_values("date").index.unique()
    train_id_list = sorted_id_list[: round(len(sorted_id_list) * (1 - test_size))]
    test_id_list = sorted_id_list[round(len(sorted_id_list) * (1 - test_size)) :]
    train = df.loc[train_id_list]
    test = df.loc[test_id_list]
    return train, test

def gain(return_func, X, n_samples=100, t_range=[0.5, 3.5]):
    gain = {}
    for i in tqdm(range(n_samples)):
        #min_thresholdから1まで、n_samples等分して、thresholdをfor分で回す
        threshold = t_range[1] * i / n_samples + t_range[0] * (1-(i/n_samples))
        n_bets, return_rate, n_hits, std = return_func(X, threshold)
        if n_bets > 2:
            gain[threshold] = {'return_rate': return_rate, 
                            'n_hits': n_hits,
                            'std': std,
                            'n_bets': n_bets}
    return pd.DataFrame(gain).T

def plot(df, label=' '):
    #標準偏差で幅をつけて薄くプロット
    plt.fill_between(df.index, y1=df['return_rate']-df['std'],
                y2=df['return_rate']+df['std'],
                alpha=0.3) #alphaで透明度を設定
    #回収率を実線でプロット
    plt.plot(df.index, df['return_rate'], label=label)
    plt.legend() #labelで設定した凡例を表示させる
    plt.grid(True) #グリッドをつける

def hello():
    print("hello")