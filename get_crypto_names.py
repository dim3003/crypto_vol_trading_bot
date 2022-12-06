import requests, json
import pandas as pd



def get_tokens_1inch(save=0):
    """
    Gets cryptocurrencies available on 1inch from tokenlist.org
    """
    r = requests.get("https://wispy-bird-88a7.uniswap.workers.dev/?url=http://tokens.1inch.eth.link")
    r = r.json()
    token_data = r['tokens']
    df = pd.DataFrame(token_data)
    if save == 1:
        df.to_pickle("token_1inch.pkl")
    #some data cleaning...
    df = df.convert_dtypes()
    df.dropna(inplace=True)
    return df


df = get_tokens_1inch()

