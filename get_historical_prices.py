import pandas as pd
import numpy as np
import postgres as pg
from datetime import date, datetime
from pycoingecko import CoinGeckoAPI

pd.set_option('display.max_rows', 100)

CHAIN =  "Polygon POS"

#set up coingecko API
cg = CoinGeckoAPI()


#check asset slug for chainId
assets_cg = cg.get_asset_platforms() 
df_assets = pd.DataFrame(assets_cg)
chain_id = df_assets[df_assets["name"] == CHAIN].chain_identifier.iloc[0]
cg_chain_id = df_assets[df_assets.chain_identifier == chain_id].id.values[0]

#get the data
df_names = pg.get_postgres()
df_names["missingInCoingecko"] = False
cg_coins = cg.get_coins_list(include_platform=True)
platforms = [item["platforms"] for item in cg_coins]
df_platforms = pd.DataFrame(platforms)
df_coins = pd.DataFrame(cg_coins)
df_coins.drop("platforms", axis=1, inplace=True)
df_coins = pd.concat([df_coins, df_platforms], axis=1)
df_coins = df_coins.loc[:, ["id", "polygon-pos"]]

#add the coingecko id to the df_names df
df_names = df_names.merge(df_coins, left_on="address", right_on="polygon-pos")

def clean_df(df):
    """ removes na rows and lowercases/removes empty columns name """
    df.index = pd.to_datetime(df.index, unit='ms')
    df = df.dropna(how="all")
    df.columns = df.columns.str.replace(' ', '')
    df.columns = df.columns.str.lower()
    return df

def get_prices(df_names=df_names, cg_chain_id=cg_chain_id, cg=cg):
    """ Gets all of the historical data from coingecko from a json of cryptocurrency on 1inch"""

    #create df with index starting in 2012 as ts for market cap and price
    df_price = pd.DataFrame(index=pd.date_range(start='1/1/2012', end=date.today()))
    df_price.index = df_price.index.values.astype(np.int64) // 10 ** 6
    df_mcap = df_price.copy()
    
    for i in range(len(df_names)):
        print(50*"-")
        print(df_names.name[i], "coingecko data extraction", i, "/", len(df_names))
        try:
            r = cg.get_coin_market_chart_by_id(df_names.id[i], "USD", 5000, interval = "daily")
        except:
            print(df_names.name[i], "is missing updating the crypto list...")
            df_names.missingInCoingecko = True
            print("Added to missing elements.")
            continue

        df_temp_price = pd.DataFrame(r["prices"])
        df_temp_price.set_index(0, inplace=True)
        df_temp_price.rename(columns={1: f"{df_names.name[i]}_USD"}, inplace=True)
        df_price = df_price.merge(df_temp_price, how="left", left_index=True, right_index=True)

        df_temp_mcap = pd.DataFrame(r["market_caps"])
        df_temp_mcap.set_index(0, inplace=True)
        df_temp_mcap.rename(columns={1: f"{df_names.name[i]}_USD"}, inplace=True)
        df_price = df_price.merge(df_temp_price, how="left", left_index=True, right_index=True)
        
    print(40*"-")
    return (df_price, df_mcap)




    
if __name__ == "__main__":
    df_price, df_mcap = get_prices(df_names)
    df_price = clean_df(df_price)
    df_mcap = clean_df(df_mcap)
    pg.send_to_postgres(df_price, table_name="hist_prices", index=True)
    pg.send_to_postgres(df_mcap, table_name="hist_mcap", index=True)
    pg.send_to_postgres(df_names)
