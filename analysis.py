import postgres as pg
import pandas as pd
import numpy as np


#get the data from postgres
df = pg.get_postgres(table_name="hist_prices")
print(df.head())