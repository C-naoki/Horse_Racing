import pandas as pd
from ..functions import update_data
from environment import settings as sets
from tqdm import tqdm


class Jockeys:
    def __init__(self, jockey_results):
        self.jockey_results = jockey_results

    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)

    @staticmethod
    def scrape(jockey_id_list, pre_jockey_results=pd.DataFrame()):
        jockeys_dict = {}
        for jockey_id in tqdm(jockey_id_list):
            if len(pre_jockey_results) and jockey_id in pre_jockey_results.index:
                continue
            page = 1
            with tqdm() as pbar:
                while True:
                    pbar.update(1)
                    url = "https://db.netkeiba.com/?pid=jockey_detail&id="+jockey_id+"&page="+str(page)
                    html = sets.session.get(url)
                    html.encoding = "EUC-JP"
                    try:
                        df = pd.read_html(html.content)[0]
                        if page == 1:
                            jockey_df = df
                        else:
                            jockey_df = pd.concat([df, jockey_df])
                    except Exception:
                        break
                    page += 1
            jockey_df.index = [jockey_id] * len(jockey_df)
            jockeys_dict[jockey_id] = jockey_df
        # pd.DataFrame型にして一つのデータにまとめる
        try:
            jockey_results_df = pd.concat([jockeys_dict[key] for key in jockeys_dict])
        except ValueError:
            return pre_jockey_results
        if len(pre_jockey_results.index):
            return pd.concat([pre_jockey_results, jockey_results_df])
        else:
            return jockey_results_df

    def preprocessing(self):
        df = self.horse_results.copy()
