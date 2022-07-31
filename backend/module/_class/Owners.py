import pandas as pd
from ..functions import update_data
from environment import settings as sets
from tqdm import tqdm


class Owners:
    def __init__(self):
        pass

    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)

    @staticmethod
    def scrape(owner_id_list, pre_owner_results=pd.DataFrame()):
        owners_dict = {}
        for owner_id in tqdm(owner_id_list):
            if len(pre_owner_results) and owner_id in pre_owner_results.index:
                continue
            page = 1
            with tqdm() as pbar:
                while True:
                    pbar.update(1)
                    url = "https://db.netkeiba.com/?pid=owner_detail&id="+owner_id+"&page="+str(page)
                    html = sets.session.get(url)
                    html.encoding = "EUC-JP"
                    try:
                        df = pd.read_html(html.content)[0]
                        if page == 1:
                            owner_df = df
                        else:
                            owner_df = pd.concat([df, owner_df])
                    except Exception:
                        break
                    page += 1
                owner_df.index = [owner_id] * len(owner_df)
                owners_dict[owner_id] = owner_df
        # pd.DataFrame型にして一つのデータにまとめる
        try:
            owner_results_df = pd.concat([owners_dict[key] for key in owners_dict])
        except ValueError:
            return pre_owner_results
        if len(pre_owner_results.index):
            return pd.concat([pre_owner_results, owner_results_df])
        else:
            return owner_results_df
