import pandas as pd
import numpy as np
import postgres as pg
from datetime import date, datetime
from pycoingecko import CoinGeckoAPI

#set up coingecko API
cg = CoinGeckoAPI()

#check asset slug for chainId 1 
assets_cg = cg.get_asset_platforms() 
df_assets = pd.DataFrame(assets_cg)
cg_chain_id = df_assets[df_assets.chain_identifier == 1].id.values[0]


#get the data
df_names = pg.get_postgres()

def get_prices(df_names=df_names, cg_chain_id=cg_chain_id, cg=cg):
    """ Gets all of the historical price data from coingecko from a json of cryptocurrency on 1inch"""

    #create a df with index starting in 2012 as ts
    df = pd.DataFrame(index=pd.date_range(start='1/1/2012', end=date.today()))
    df.index = df.index.values.astype(np.int64) // 10 ** 6
    
    
    for i in range(len(df_names)):
        print(50*"=")
        print(df_names.name[i], "coingecko data extraction", i, "/", len(df_names))
        try:
            r = cg.get_coin_market_chart_from_contract_address_by_id(cg_chain_id, df_names.address[i], "USD", 5000)["prices"]
        except:
            #add a row with the missing value name
        df_temp = pd.DataFrame(r)
        df_temp.set_index(0, inplace=True)
        df_temp.rename(columns={1: f"{df_names.name[i]}_USD"}, inplace=True)
        df = df.merge(df_temp, how="left", left_index=True, right_index=True)
    
    df.index = pd.to_datetime(df.index, unit='ms')
    print(40*"-")
    return df
    
if __name__ == "__main__":
    df = get_prices(df_names)
    df = df.dropna(how="all")
    df.columns = df.columns.str.replace(' ', '')
    df.columns = df.columns.str.lower()
    pg.send_to_postgres(df, table_name="hist_prices", index=True)