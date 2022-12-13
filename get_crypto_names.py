import requests, json
import pandas as pd
import os
import san
import postgres as pg

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

def get_tokens_san():
  """
  gets slug and address info on santiment tokens
  """
  san_projects = san.graphql.execute_gql("""{
    allProjects {
      slug
      name
      ticker
      infrastructure
      mainContractAddress
    }
  }""")

  df = pd.DataFrame(san_projects["allProjects"])
  return df

df_json = pg.get_postgres()
print(df_json.head(1))
df_san = get_tokens_san()
print(df_san.head(1))

df = df_json.merge(df_san, how="left", left_on="address", right_on="mainContractAddress", suffixes=('_json', '_san'))
#print(df)


