import pandas as pd
import numpy as np
import requests, json, os, time
from modules import postgres as pg
from modules import fetch_abi
from datetime import date, datetime
from pycoingecko import CoinGeckoAPI
pd.set_option('display.max_rows', 100)

GET_NAMES = 1 #set this to 1 if you want to refetch the cryptos names available from 1inch api
GET_PRICES = 1 #set this to 1 if you want to fetch price data on coingecko
GET_ABI = 1 #set this to 1 if you want to fetch ABI data for 1inch coins contracts
CHAIN = "Polygon POS"

#set up coingecko API
cg = CoinGeckoAPI()

#check asset slug for chainId
assets_cg = cg.get_asset_platforms() 
df_assets = pd.DataFrame(assets_cg)
chain_id = df_assets[df_assets["name"] == CHAIN].chain_identifier.iloc[0]
cg_chain_id = df_assets[df_assets.chain_identifier == chain_id].id.values[0]

#get the data
df_names = pg.get_postgres()

#manually adding addresses from coingecko
df_names.loc[df_names.symbol == "MATIC", "address"] = "0x0000000000000000000000000000000000001010"
df_names.loc[df_names.symbol == "deUSDC", "address"] = "0xda43bfd7ecc6835aa6f1761ced30b986a574c0d2"
df_names.loc[df_names.symbol == "NFTY", "address"] = "0xcc081220542a60a8ea7963c4f53d522b503272c1"

df_names["missingInCoingecko"] = False
cg_coins = cg.get_coins_list(include_platform=True)
platforms = [item["platforms"] for item in cg_coins]
df_platforms = pd.DataFrame(platforms)
df_coins = pd.DataFrame(cg_coins)
df_coins.drop("platforms", axis=1, inplace=True)
df_coins = pd.concat([df_coins, df_platforms], axis=1)
df_coins = df_coins.loc[:, ["id", "polygon-pos"]]


#add the coingecko id to the df_names df
df_names = df_names.merge(df_coins, how="left", left_on="address", right_on="polygon-pos")
#print(df_names[df_names.id.isnull()]) #used to look which ones are not on coingecko :/

def get_tokens_1inch(save=0):
    """
    Gets cryptocurrencies available on 1inch from tokenlist.org
    """
    r = requests.get("https://api.1inch.io/v5.0/137/tokens")
    r = r.json()
    token_data = r['tokens']
    df = pd.DataFrame(token_data)
    df = df.T
    if save == 1:
        df.to_pickle("token_1inch.pkl")
    #some data cleaning...
    df = df.convert_dtypes()
    df.dropna(how="all", inplace=True)
    return df

def get_abis(token_names, contract_addresses):
    if len(token_names) != len(contract_addresses):
        print("Token names and contract addresses arrays are not of the same length please verify.")
        return 0
    for i, name in enumerate(token_names):
       pass 

def clean_df(df):
    """ removes na rows and changes index to datetime """
    df.index = pd.to_datetime(df.index, unit='ms')
    df = df.dropna(how="all")
    return df

def get_prices(df_names=df_names, cg_chain_id=cg_chain_id, cg=cg):
    """ Gets all of the historical data from coingecko from a json of cryptocurrency on 1inch"""

    #create df with index starting in 2012 as ts for market cap and price
    df_price = pd.DataFrame(index=pd.date_range(start='1/1/2012', end=date.today()))
    df_price.index = df_price.index.values.astype(np.int64) // 10 ** 6
    df_mcap = df_price.copy()
    for i in range(len(df_names)):
        print(50*"-")
        print(df_names.name[i], "coingecko data extraction", i+1, "/", len(df_names))
        try:
            r = cg.get_coin_market_chart_by_id(df_names.id[i], "USD", 5000, interval = "daily")
        except:
            print(df_names.name[i], "is missing updating the crypto list...")
            df_names.missingInCoingecko = True
            print("Added to missing elements.")
            continue

        df_temp_price = pd.DataFrame(r["prices"])
        df_temp_price.set_index(0, inplace=True)
        df_temp_price.rename(columns={1: f"{df_names.name[i]}"}, inplace=True)
        df_price = df_price.merge(df_temp_price, how="left", left_index=True, right_index=True)

        df_temp_mcap = pd.DataFrame(r["market_caps"])
        df_temp_mcap.set_index(0, inplace=True)
        df_temp_mcap.rename(columns={1: f"{df_names.name[i]}"}, inplace=True)
        df_mcap = df_mcap.merge(df_temp_mcap, how="left", left_index=True, right_index=True)
        
    print(40*"-")
    return (df_price, df_mcap)


if __name__ == "__main__":
    if GET_ABI == 1:
        print("Getting the ABIs...")
        get_abis(df_names.name, df_names.address)
    if GET_NAMES == 1:
        print("Getting tokens names from 1inch api...")
        df = get_tokens_1inch()
        print("Saving to postgres...")
        pg.send_to_postgres(df)
    if GET_PRICES == 1:
        print("Getting prices and market capitalizations from Coingecko...")
        df_price, df_mcap = get_prices(df_names)
        print("Clean the dataframes...")
        df_price = clean_df(df_price)
        df_mcap = clean_df(df_mcap)
        print("Sending to postgres...")
        pg.send_to_postgres(df_price, table_name="hist_prices", index=True)
        pg.send_to_postgres(df_mcap, table_name="hist_mcap", index=True)
    print("DONE")
