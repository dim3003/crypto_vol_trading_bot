import math
import postgres as pg
import pandas as pd
pd.set_option('display.max_rows', None)
import numpy as np
import termplotlib as tpl
from scipy import stats
from datetime import datetime, timedelta

NBR_DAYS = 730 #number of days to keep as data
SLIPPAGE_FEE = 0.005 #used the automatic max from 1inch as estimate
LIQUIDITY_FEE = 0.003 #used the medium fee tier of uniswap as estimate
VOL_WINDOW_DAYS = 30 #period for volatility calc 
MONTHLY_SHOW = 0 #set to one to show monthly returns

def total_returns(returns):
    """Gives the total returns with a investment of 1 and the number of periods as a tuple"""
    r = returns + 1
    pnl = r.product()
    return (pnl, len(r))

def returns_detailed(returns, weights, weight):
    """
    Calculates the returns of a dataframe with the liquidity and slippage fees associated 
    Gives as second argument a pd series with number of trades
    """
    #get turnover of portfolio for the day in percentage
    weights_calc = weights+1
    df_turnover = weights_calc.pct_change()
    df_turnover[df_turnover!=0] = weight
    df_turnover.iloc[0,:] = 1/len(df_turnover.columns) #sums up to one for turnover
    #get nbr of trades for gas fees calcs
    df_nbr_trades = df_turnover.copy()
    df_nbr_trades[df_nbr_trades != 0] = 1
    df_nbr_trades = df_nbr_trades.sum(axis=1)
    #multiply it with (SLIPPAGE + LIQUID FEE) 
    df_turnover = df_turnover.sum(axis=1)
    df_fees = df_turnover * (SLIPPAGE_FEE + LIQUIDITY_FEE)
    df_returns_net = returns - df_fees
    return df_returns_net, df_nbr_trades

def monthly_returns(returns):
    #get first date and find first day of next month
    first = returns.index[0]
    if int(first.strftime("%d")) != 1:
        next_month = first.replace(day=27) + timedelta(days=5)
        first = next_month - timedelta(days=(next_month.day-1))
    #get last date and find last day of last month
    last = returns.index[-1]
    last = last - timedelta(days=last.day)
    #filter df
    returns = returns[(returns.index >= first) & (returns.index <= last)]
    #average returns over each month
    df = pd.DataFrame()
    while len(returns) > 0:
        next_month = returns.index[0].replace(day=27) + timedelta(days=5)
        last_day = next_month - timedelta(days=next_month.day)
        monthly_returns = returns[returns.index <= last_day] + 1
        monthly_returns = pd.Series(monthly_returns.product() - 1, index=[last_day.strftime("%y.%m")])
        df = pd.concat([df,monthly_returns])
        returns = returns[returns.index > last_day]
    df.rename(columns={0: "average_returns"}, inplace=True)
    return df

def sharpe(returns):
    """
    Returns the Sharpe ratio of returns given based on the earning rate of the Compound protocol
    """
    return round(((total_returns(returns)[0] - 1) - 0.0154) / returns.std(), 4) #0.0154 value is earnings of Compound on 01.01.23

def beta(returns, bench_returns):
    """
    Returns the beta of returns with the benchmark returns
    """
    df_cov = pd.concat([returns, bench_returns], axis=1).cov()
    return round(df_cov.iloc[0, 1] / df_cov.iloc[0,0],4)

def trackingError(returns, bench_returns):
    """
    returns the tracking error of returns and of a benchmark returns
    """
    return round((returns - bench_returns).std(),4)

def informationRatio(returns, bench_returns):
    """
    Returns the information ratio of returns
    """
    TE = trackingError(returns, bench_returns)
    if TE != 0:
       return round((total_returns(returns)[0] - total_returns(bench_returns)[0]) / trackingError(returns, bench_returns))
    else:
        return 0

def bear_bull_returns(returns):
    """
    Separates returns between bull and bear markets and gives a tuple with first bull market returns and then bear market returns
    Uses this analysis for dates of bull/bear markets https://crypto.com/research/crypto-bear-markets
    """
    #get all relevant bear markets as dateranges
    bear_market_dates = pd.date_range(start="06.26.2019", end="03.12.2020").union(pd.date_range(start="04.14.2021", end="05.17.2021")).union(pd.date_range(start="11.10.2021", end=datetime.today()))
    #create 2 dataframes by filtering out/in these dateranges in index
    bear_market_dates = bear_market_dates[(bear_market_dates >= returns.index[0]) & (bear_market_dates <= returns.index[-1])]
    bear_returns = total_returns(returns.loc[bear_market_dates])[0] - 1
    bull_returns = total_returns(returns.drop(bear_market_dates))[0] - 1
    return (bull_returns, bear_returns)


#get the data from postgres
df = pg.get_postgres(table_name="hist_prices", index_col="index")

#data cleaning
df.fillna(method="ffill", inplace=True) #adds missing days
df = df.iloc[len(df)-NBR_DAYS:] #keeps only cryptos with 2 year of data
df.dropna(axis=1, inplace=True)

#get returns
df_returns = df.pct_change()
df_returns.dropna(how="all", inplace=True)
#change returns outliers to 0
val = df_returns.values
og_shape = val.shape
val = val.ravel()
df_temp = pd.Series(val)
df_temp[(df_temp > 1) | (df_temp < -1)] = 0
df_temp = df_temp.values.reshape(og_shape)
df_returns = pd.DataFrame(df_temp, columns = df_returns.columns, index=df_returns.index)

#df_gas_price
df_gas_price = pd.read_csv("gas_price_gwei.csv") #gas price as csv from https://polygonscan.com/chart/gasprice
df_gas_price.set_index(pd.to_datetime(df_gas_price["Date(UTC)"]), inplace=True)
df_gas_price = df_gas_price.iloc[:, 2].rename("wei")
df_gas_price = pd.merge(df["matic_usd"], df_gas_price, right_index=True, left_index=True, how="left")
df_gas_price["gas_fee_usd"] = df_gas_price.matic_usd * df_gas_price.wei * 10e-18 * 21000 #21000 is basic gas limit cost
df_gas_price = df_gas_price["gas_fee_usd"].dropna()


#get volatility
df_vol = df_returns.rolling(VOL_WINDOW_DAYS).std()
df_vol.dropna(how="all", inplace=True)
df_returns = df_returns[len(df_returns)-len(df_vol):]
df_gas_price = df_gas_price[len(df_gas_price)-len(df_vol):]

#ranks crypto according to vola
df_rank = df_vol.rank(axis=1)

#wrappedBTC as reference
print(50*"=")
df_wBTC = df_returns.loc[:, "wrappedbtc_usd"]
r = total_returns(df_wBTC)
print("WRAPPED BTC RESULTS")
print(50*"-")
print(f"{'NUMBER OF DAYS':<15}{r[1]:>35d}")
print(f"{'NO FEE':<15}{round(r[0] - 1, 4):>35.2%}")
print(f"{'VOLATILITY':<15}{round(df_wBTC.std(),4):>35.2%}")
print(f"{'MAX DD':<15}{df_wBTC.min():>35.2%}")
print(f"{'SHARPE':<15}{sharpe(df_wBTC):>35.4f}")
print(f"{'BETA':<15}{beta(df_wBTC, df_wBTC):>35.4f}")
print(f"{'TRACKING ERROR':<15}{trackingError(df_wBTC, df_wBTC):>35.4f}")
print(f"{'INFO RATIO':<15}{informationRatio(df_wBTC, df_wBTC):>35.4f}")
print(f"{'BULL RETURNS':<15}{bear_bull_returns(df_wBTC)[0]:>35.2%}")
print(f"{'BEAR RETURNS':<15}{bear_bull_returns(df_wBTC)[1]:>35.2%}")
if MONTHLY_SHOW != 0:
    print(50*"-")
    print("MONTHLY RETURNS")
    df_monthly = monthly_returns(df_wBTC)
    fig = tpl.figure()
    fig.barh(round(df_monthly.average_returns+1,4), df_monthly.index, force_ascii=True)
    fig.show()
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
r_net, df_nbr_trades = returns_detailed(df_low_vol_returns, df_low_vol_weights, weight)
r_net_total = total_returns(r_net)
print("LOW VOLATILITY RESULTS")
print(50*"-")
print(f"{'NUMBER OF DAYS':<15}{r[1]:>35d}")
print(f"{'NO FEE':<15}{round(r[0] - 1, 4):>35.2%}")
print(f"{'LIQ+SLIP FEE':<15}{round(r_net_total[0] - 1, 4):>35.2%}")
print(f"{'VOLATILITY':<15}{round(df_low_vol_returns.std(),4):>35.2%}")
print(f"{'MAX DD':<15}{df_low_vol_returns.min():>35.2%}")
print(f"{'SHARPE':<15}{sharpe(df_low_vol_returns):>35.4f}")
print(f"{'BETA':<15}{beta(df_low_vol_returns, df_wBTC):>35.4f}")
print(f"{'TRACKING ERROR':<15}{trackingError(df_low_vol_returns, df_wBTC):>35.4f}")
print(f"{'INFO RATIO':<15}{informationRatio(df_low_vol_returns, df_wBTC):>35.4f}")
print(f"{'BULL RETURNS':<15}{bear_bull_returns(df_low_vol_returns)[0]:>35.2%}")
print(f"{'BEAR RETURNS':<15}{bear_bull_returns(df_low_vol_returns)[1]:>35.2%}")
if MONTHLY_SHOW != 0:
    print(50*"-")
    print("MONTHLY RETURNS")
    df_monthly = monthly_returns(df_low_vol_returns)
    fig = tpl.figure()
    fig.barh(round(df_monthly.average_returns+1,4), df_monthly.index, force_ascii=True)
    fig.show()
    print(50*"-")



#High vola
df_high_vol_weights = df_rank.copy()

df_high_vol_weights[df_high_vol_weights < half_nbr_col] = 0
df_high_vol_weights[df_high_vol_weights != 0] = weight


df_high_vol_returns = df_high_vol_weights * df_returns
df_high_vol_returns = df_high_vol_returns.sum(axis=1)

print(50*"=")
r = total_returns(df_high_vol_returns)
r_net, df_nbr_trades = returns_detailed(df_high_vol_returns, df_high_vol_weights, weight)
r_net_total = total_returns(r_net)
print("HIGH VOLATILITY RESULTS")
print(50*"-")
print(f"{'NUMBER OF DAYS':<15}{r[1]:>35d}")
print(f"{'NO FEE':<15}{round(r[0] - 1, 4):>35.2%}")
print(f"{'LIQ+SLIP FEE':<15}{r_net_total[0]-1:>35.2%}")
print(f"{'VOLATILITY':<15}{round(df_high_vol_returns.std(),4):>35.2%}")
print(f"{'MAX DD':<15}{df_high_vol_returns.min():>35.2%}")
print(f"{'SHARPE':<15}{sharpe(df_high_vol_returns):>35.4f}")
print(f"{'BETA':<15}{beta(df_high_vol_returns, df_wBTC):>35.4f}")
print(f"{'TRACKING ERROR':<15}{trackingError(df_high_vol_returns, df_wBTC):>35.4f}")
print(f"{'INFO RATIO':<15}{informationRatio(df_high_vol_returns, df_wBTC):>35.4f}")
print(f"{'BULL RETURNS':<15}{bear_bull_returns(df_high_vol_returns)[0]:>35.2%}")
print(f"{'BEAR RETURNS':<15}{bear_bull_returns(df_high_vol_returns)[1]:>35.2%}")
if MONTHLY_SHOW != 0:
    print(50*"-")
    print("MONTHLY RETURNS")
    df_monthly = monthly_returns(df_high_vol_returns)
    fig = tpl.figure()
    fig.barh(round(df_monthly.average_returns+1,4), df_monthly.index, force_ascii=True)
    fig.show()
    print(50*"-")
