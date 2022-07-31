import pandas as pd
from ..functions import update_data
from environment import settings as sets
from tqdm import tqdm


class Trainers:
    def __init__(self):
        pass

    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)

    @staticmethod
    def scrape(trainer_id_list, pre_trainer_results=pd.DataFrame()):
        trainers_dict = {}
        for trainer_id in tqdm(trainer_id_list):
            if len(pre_trainer_results) and trainer_id in pre_trainer_results.index:
                continue
            page = 1
            with tqdm() as pbar:
                while True:
                    pbar.update(1)
                    url = "https://db.netkeiba.com/?pid=trainer_detail&id="+trainer_id+"&page="+str(page)
                    html = sets.session.get(url)
                    html.encoding = "EUC-JP"
                    try:
                        df = pd.read_html(html.content)[0]
                        if page == 1:
                            trainer_df = df
                        else:
                            trainer_df = pd.concat([df, trainer_df])
                    except Exception:
                        break
                    page += 1
                trainer_df.index = [trainer_id] * len(trainer_df)
                trainers_dict[trainer_id] = trainer_df
        # pd.DataFrame型にして一つのデータにまとめる
        try:
            trainer_results_df = pd.concat([trainers_dict[key] for key in trainers_dict])
        except ValueError:
            return pre_trainer_results
        if len(pre_trainer_results.index):
            return pd.concat([pre_trainer_results, trainer_results_df])
        else:
            return trainer_results_df
