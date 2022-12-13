import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

#loads env variables 
load_dotenv() 

# establish connections
conn_string = f"postgresql://{os.environ['POSTGRES_USERNAME']}:{os.environ['POSTGRES_PASSWORD']}:@localhost:5432/bot_vol"
conn = create_engine(conn_string).connect()

def send_to_postgres(df, conn=conn):
  """
  Sends the dataframe to the cryptos_1inch table in postgres
  """
  df.to_sql('cryptos_1inch', conn, if_exists= 'replace', index=False)

def get_postgres(conn=conn):
  """
  gets the data from cryptos_1inch table in postgres
  """
  return pd.read_sql('cryptos_1inch', conn)