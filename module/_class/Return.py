import sys
sys.path.append('.../')

import pandas as pd
import time
from ..functions import update_data
from tqdm import tqdm
from urllib.request import urlopen
from environment.variables import place_dict

class Return:
    def __init__(self, return_tables):
        self.return_tables = return_tables
    
    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)
    
    @staticmethod
    def scrape(race_id_dict, pre_return_tables=pd.DataFrame()):
        return_tables = {}
        arrival_tables = {}
        for place, race_id_place in race_id_dict.items():
            for kai, race_id_kai in race_id_place.items():
                indexerror_chk = -1
                pbar = tqdm(total=len(race_id_kai))
                for race_id in race_id_kai:
                    pbar.update(1)
                    pbar.set_description("scrape  return table in {} {}回".format([k for k, v in place_dict.items() if v == str(place).zfill(2)][0], kai))
                    if len(pre_return_tables) and race_id in set(pre_return_tables.index):
                        continue
                    try:
                        time.sleep(1)
                        url = "https://db.netkeiba.com/race/" + race_id
                        #普通にスクレイピングすると複勝やワイドなどが区切られないで繋がってしまう。
                        #そのため、改行コードを文字列brに変換して後でsplitする
                        f = urlopen(url)
                        html = f.read()
                        html = html.replace(b'<br />', b'br')
                        dfs1 = pd.read_html(html, match='単勝')[1]
                        dfs2 = pd.read_html(html, match='三連複')[0]
                        arrival_df = pd.read_html(html, match='単勝')[0].iloc[:,[0,2]]
                        # dfsの1番目に単勝〜馬連、2番目にワイド〜三連単がある
                        df = pd.concat([dfs1, dfs2])
                        df.index = [race_id] * len(df)
                        return_tables[race_id] = df
                        # 馬番と着順の関係表
                        arrival_df.index = [race_id] * len(arrival_df)
                        arrival_df.columns = ["着順", "馬番"]
                        arrival_tables[race_id] = arrival_df
                    except IndexError:
                        indexerror_chk = 1
                        break
                    except Exception as e:
                        if str(e)[-3:-1]=="単勝": indexerror_chk = 1
                        else: indexerror_chk = 0
                        break
                    except:
                        indexerror_chk = 0
                        break
                if indexerror_chk == 1:
                    pbar.close()
                    print("{}回{}日のレースはまだ開催されていません。\n".format(str(race_id)[6:8], str(race_id)[8:10]))
                    continue
                elif indexerror_chk == 0:
                    break
                elif indexerror_chk == -1:
                    pbar.close()
                    print("対象のレースを全て取得し終わりました。\n")

        #pd.DataFrame型にして一つのデータにまとめる
        try:
            return_tables_df = pd.concat([return_tables[key] for key in return_tables])
            arrival_tables_df = pd.concat([arrival_tables[key] for key in arrival_tables])
        except ValueError:
            return pre_return_tables, pd.DataFrame()
        if len(pre_return_tables.index):
            return pd.concat([pre_return_tables, return_tables_df]), arrival_tables_df
        else:
            return return_tables_df, arrival_tables_df

    @property
    def fukusho(self):
        fukusho = self.return_tables[self.return_tables[0]=='複勝'][[1,2]]
        wins = fukusho[1].str.split('br', expand=True)[[0,1,2]]
        
        wins.columns = ['win_0', 'win_1', 'win_2']
        returns = fukusho[2].str.split('br', expand=True)[[0,1,2]]
        returns.columns = ['return_0', 'return_1', 'return_2']
        
        df = pd.concat([wins, returns], axis=1)
        for column in df.columns:
            df[column] = df[column].str.replace(',', '')
        return df.fillna(0).astype(int)
    
    @property
    def tansho(self):
        tansho = self.return_tables[self.return_tables[0]=='単勝'][[1,2]]
        tansho.columns = ['win', 'return']
        
        for column in tansho.columns:
            tansho[column] = pd.to_numeric(tansho[column], errors='coerce')
            
        return tansho
    
    @property
    def umaren(self):
        umaren = self.return_tables[self.return_tables[0]=='馬連'][[1,2]]
        wins = umaren[1].str.split('-', expand=True)[[0,1]].add_prefix('win_')
        return_ = umaren[2].rename('return')  
        df = pd.concat([wins, return_], axis=1)        
        return df.apply(lambda x: pd.to_numeric(x, errors='coerce'))
    
    @property
    def umatan(self):
        umatan = self.return_tables[self.return_tables[0]=='馬単'][[1,2]]
        wins = umatan[1].str.split('→', expand=True)[[0,1]].add_prefix('win_')
        return_ = umatan[2].rename('return')  
        df = pd.concat([wins, return_], axis=1)        
        return df.apply(lambda x: pd.to_numeric(x, errors='coerce'))
    
    @property
    def wide(self):
        wide = self.return_tables[self.return_tables[0]=='ワイド'][[1,2]]
        wins = wide[1].str.split('br', expand=True)[[0,1,2]]
        wins = wins.stack().str.split('-', expand=True).add_prefix('win_')
        return_ = wide[2].str.split('br', expand=True)[[0,1,2]]
        return_ = return_.stack().rename('return')
        df = pd.concat([wins, return_], axis=1)
        return df.apply(lambda x: pd.to_numeric(x.str.replace(',',''), errors='coerce'))
    
    @property
    def sanrentan(self):
        rentan = self.return_tables[self.return_tables[0]=='三連単'][[1,2]]
        wins = rentan[1].str.split('→', expand=True)[[0,1,2]].add_prefix('win_')
        return_ = rentan[2].rename('return')
        df = pd.concat([wins, return_], axis=1) 
        return df.apply(lambda x: pd.to_numeric(x, errors='coerce'))
    
    @property
    def sanrenpuku(self):
        renpuku = self.return_tables[self.return_tables[0]=='三連複'][[1,2]]
        wins = renpuku[1].str.split('-', expand=True)[[0,1,2]].add_prefix('win_')
        return_ = renpuku[2].rename('return')
        df = pd.concat([wins, return_], axis=1)
        return df.apply(lambda x: pd.to_numeric(x, errors='coerce'))
