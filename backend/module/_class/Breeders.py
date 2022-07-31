import pandas as pd
from ..functions import update_data
from environment import settings as sets
from tqdm import tqdm


class Breeders:
    def __init__(self):
        pass

    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)

    @staticmethod
    def scrape(breeder_id_list, pre_breeder_results=pd.DataFrame()):
        breeders_dict = {}
        for breeder_id in tqdm(breeder_id_list):
            if len(pre_breeder_results) and breeder_id in pre_breeder_results.index:
                continue
            page = 1
            with tqdm() as pbar:
                while True:
                    pbar.update(1)
                    url = "https://db.netkeiba.com/?pid=breeder_detail&id="+breeder_id+"&page="+str(page)
                    html = sets.session.get(url)
                    html.encoding = "EUC-JP"
                    try:
                        df = pd.read_html(html.content)[0]
                        if page == 1:
                            breeder_df = df
                        else:
                            breeder_df = pd.concat([df, breeder_df])
                    except Exception:
                        break
                    page += 1
                breeder_df.index = [breeder_id] * len(breeder_df)
                breeders_dict[breeder_id] = breeder_df
        # pd.DataFrame型にして一つのデータにまとめる
        try:
            breeder_results_df = pd.concat([breeders_dict[key] for key in breeders_dict])
        except ValueError:
            return pre_breeder_results
        if len(pre_breeder_results.index):
            return pd.concat([pre_breeder_results, breeder_results_df])
        else:
            return breeder_results_df
