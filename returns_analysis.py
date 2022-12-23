import math
import postgres as pg
import pandas as pd
import numpy as np
from scipy import stats

NBR_DAYS = 730 #number of days to keep as data
SLIPPAGE_FEE = 0.005 #used the automatic max from 1inch as estimate
LIQUIDITY_FEE = 0.003 #used the medium fee tier of uniswap as estimate
VOL_WINDOW_DAYS = 30 #period for volatility calc 



def total_returns(returns):
    """Gives the total returns with a investment of 1 and the number of periods as a tuple"""
    r = returns + 1
    pnl = r.product()
    return (pnl, len(r))

def returns_with_fees(returns, weights):
    """Calculates the returns of a dataframe with the fees associated """
    #add the gas fees to the weights dataframe
    weights = weights.merge(df_gas_price, how="left", left_index=True, right_index=True)
    

    pass

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
df = df.iloc[len(df)-NBR_DAYS:] #keeps only cryptos with 2 year of data
df.dropna(axis=1, inplace=True)

#get returns
df_returns = df.pct_change()
df_returns.dropna(how="all", inplace=True)

#df_gas_price
df_gas_price = pd.read_csv("gas_price_gwei.csv") #gas price as csv from https://polygonscan.com/chart/gasprice
df_gas_price.set_index(pd.to_datetime(df_gas_price["Date(UTC)"]), inplace=True)
df_gas_price = df_gas_price.iloc[:, 2].rename("wei")
filter_cols = [col for col in df if col.startswith('') ]
print(filter_cols)
df_gas_price = pd.merge(df["ether_usd"], df_gas_price, right_index=True, left_index=True, how="left")
df_gas_price["gas_fee_usd"] = df_gas_price.ether_usd * df_gas_price.wei * 10e-18 * 21000 #21000 is basic gas limit cost
print(df_gas_price)
exit()

#get volatility
df_vol = df_returns.rolling(VOL_WINDOW_DAYS).std()
df_vol.dropna(how="all", inplace=True)
df_returns = df_returns[len(df_returns)-len(df_vol):]
df_gas_price = df_gas_price[len(df_gas_price)-len(df_vol)]

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
half_nbr_col = (math.floor(nbr_col / 2))
weight = round(1 / half_nbr_col, 6)
df_low_vol_weights = df_rank.copy()

df_low_vol_weights[df_low_vol_weights > half_nbr_col] = 0
df_low_vol_weights[df_low_vol_weights != 0] = weight

df_low_vol_returns = df_low_vol_weights * df_returns
df_low_vol_returns = df_low_vol_returns.sum(axis=1)

print(50*"=")
r = total_returns(df_low_vol_returns)
r_net = returns_with_fees(df_low_vol_returns, df_low_vol_weights)
exit()
print("Low vol results")
print("It averaged", round(r[0]*100 - 100, 2), "% out of", r[1], "days.")
print(50*"-")


#High vola
df_high_vol_weights = df_rank.copy()

df_high_vol_weights[df_high_vol_weights < half_nbr_col] = 0
df_high_vol_weights[df_high_vol_weights != 0] = weight


df_high_vol_returns = df_high_vol_weights * df_returns
df_high_vol_returns = df_high_vol_returns.sum(axis=1)

df_high_vol_returns.drop(df_high_vol_returns[df_high_vol_returns > 0.27].index, inplace=True)


print(50*"=")
r = total_returns(df_high_vol_returns)
print("High vol results")
print("It averaged", round(r[0]*100 - 100, 2), "% out of", r[1], "days.")
print(50*"-")