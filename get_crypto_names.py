import requests, json
import pandas as pd
import os
import postgres as pg

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

if __name__ == "__main__":
    print("Getting tokens...")
    df = get_tokens_1inch()
    print("Saving to postgres...")
    pg.send_to_postgres(df)
    print("SAVED")