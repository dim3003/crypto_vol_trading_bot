import postgres as pg
import pandas as pd
import numpy as np


#get the data from postgres
df = pg.get_postgres(table_name="hist_prices")#, index_col="index_label"

df_returns = df.pct_change()
df_returns.dropna(how="all", inplace=True)

df_vol = df_returns.rolling(30).std()
df_vol.dropna(how="all", inplace=True)

df_rank = df_vol.rank(axis=1)
