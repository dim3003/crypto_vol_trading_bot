import math
import postgres as pg
import pandas as pd
import numpy as np

def total_returns(returns):
    """Gives the total returns with a investment of 1 and the number of periods as a tuple"""
    r = returns + 1
    pnl = r.product()
    return (pnl, len(r))

def monthly_returns(returns):
    pass

def volatility(returns):
    pass

def maxDD(returns):
    pass

def sharpe(returns, bench_returns):
    pass

def excReturns(returns, bench_returns):
    pass

def beta(returns, bench_returns):
    pass

def trackingError(returns, bench_returns):
    pass

def informationRatio(returns, bench_returns):
    pass

def HHI(returns):
    pass


#get the data from postgres
df = pg.get_postgres(table_name="hist_prices", index_col="index")

#data cleaning
df.fillna(method="ffill", inplace=True) #adds missing days
df = df.iloc[len(df)-730:] #keeps only cryptos with 2 year of data
df.dropna(axis=1, inplace=True)

#get returns
df_returns = df.pct_change()
df_returns.dropna(how="all", inplace=True)

#get volatility
df_vol = df_returns.rolling(30).std()
df_vol.dropna(how="all", inplace=True)

#ranks crypto according to vola
df_rank = df_vol.rank(axis=1)

#wrappedBTC as reference
print(50*"=")
df_wBTC = df_returns.loc[:, "wrappedbtc_usd"]
r = total_returns(df_wBTC)
print("Wrapped BTC results")
print("It averaged", round(r[0]*100 - 100, 2), "% out of", r[1], "days.")
print(50*"-")


#low vola
nbr_col = len(df_returns.columns)
w = round(1 / (math.floor(nbr_col / 2)), 6)
