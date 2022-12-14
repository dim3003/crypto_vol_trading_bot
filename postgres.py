import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

#loads env variables 
load_dotenv() 

# establish connections
conn_string = f"postgresql://{os.environ['POSTGRES_USERNAME']}:{os.environ['POSTGRES_PASSWORD']}:@localhost:5432/bot_vol"
conn = create_engine(conn_string).connect()

def send_to_postgres(df, conn=conn, table_name='cryptos_1inch'):
  """
  Sends the dataframe to the cryptos_1inch table in postgres
  """
  df.to_sql(table_name, conn, if_exists= 'replace', index=False)

def get_postgres(conn=conn, table_name='cryptos_1inch'):
  """
  gets the data from cryptos_1inch table in postgres
  """
  return pd.read_sql(table_name, conn)