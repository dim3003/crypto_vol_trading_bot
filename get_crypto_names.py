import requests, json
import pandas as pd
import os
import san
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv() #loads env variables 

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

#df = get_tokens_1inch()


#finds all crypto names
san_projects = san.graphql.execute_gql("""{
  allProjects {
    slug
    name
    ticker
    infrastructure
    mainContractAddress
  }
}""")
print(san_projects)

"""
# establish connections
conn_string = f"postgresql://{os.environ['POSTGRES_USERNAME']}:{os.environ['POSTGRES_PASSWORD']}:@localhost:5432/bot_vol"
conn = create_engine(conn_string).connect()

# converting df to sql
df.to_sql('cryptos_1inch', conn, if_exists= 'replace', index=False)
"""