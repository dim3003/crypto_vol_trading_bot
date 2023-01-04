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

class Analyzer():
    def __init__(self, df_price, bench_returns=0, strategy="BTC", nbr_days=NBR_DAYS, slippage_fee=SLIPPAGE_FEE, liquidity_fee=LIQUIDITY_FEE, vol_window_days=VOL_WINDOW_DAYS):
        self.df_price = df_price
        self.strategy = strategy
        self.nbr_days = nbr_days - vol_window_days
        self.slippage_fee = slippage_fee
        self.liquidity_fee = liquidity_fee
        self.vol_window_days = vol_window_days
        self.returns = self.get_strat_returns()
        self.nbr_trades, self.returns_net = self.returns_detailed()
        self.monthly_returns = self.monthly_returns()
        if strategy != "BTC":
            self.bench_returns = bench_returns
        else:   
            self.bench_returns = self.returns
    
    def __str__(self, monthly_show=0):
        print(50*"=")
        print(f"{self.strategy} RESULTS")
        print(50*"-")
        print(f"{'NUMBER OF DAYS':<15}{self.nbr_days:>35d}")
        print(f"{'NO FEE':<15}{self.total_returns():>35.2%}")
        print(f"{'VOLATILITY':<15}{self.returns.std():>35.2%}")
        print(f"{'MAX DD':<15}{self.returns.min():>35.2%}")
        print(f"{'SHARPE':<15}{self.sharpe():>35.4f}")
        print(f"{'BETA':<15}{self.beta():>35.4f}")
        print(f"{'TRACKING ERROR':<15}{self.trackingError():>35.4f}")
        print(f"{'INFO RATIO':<15}{self.informationRatio():>35.4f}")
        print(f"{'BULL RETURNS':<15}{self.bear_bull_returns()[0]:>35.2%}")
        print(f"{'BEAR RETURNS':<15}{self.bear_bull_returns()[1]:>35.2%}")
        print(f"{'TOTAL GAS FEES USD':<20}{self.gas_fee():>30.4f}")
        if monthly_show != 0:
            print(50*"-")
            print("MONTHLY RETURNS")
            df_monthly = self.monthly_returns()
            fig = tpl.figure()
            fig.barh(round(df_monthly.average_returns+1,4), df_monthly.index, force_ascii=True)
            fig.show()
        print(50*"-")
        return ""

    def clean_returns(self):
        """ Gives back the cleaned returns with the df price given """
        df = self.df_price.copy()
        #data cleaning
        df.fillna(method="ffill", inplace=True) #adds missing days
        df = df.iloc[len(df)-self.nbr_days:] #keeps only cryptos with 2 year of data
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
        #remove returns used for calculating the volatility
        df_returns = df_returns[self.vol_window_days - 1:]
        return df_returns
    
    def get_strat_returns(self):
        df_returns = self.clean_returns()
        #BTC only
        if self.strategy == "BTC":
            self.weight = 1
            df_temp = df_returns.copy()
            for col in df_returns.columns:
                df_temp[col] = 0
            df_temp["wrappedbtc_usd"] = 1
            self.weights = df_temp
        #calculate returns
        returns = df_returns * self.weights
        return returns.sum(axis=1)

    def total_returns(self, returns=[]):
        """Gives the total returns and the number of periods as a tuple"""
        if len(returns) == 0:
            r = self.returns + 1
            pnl = r.product() - 1
        else:
            r = returns + 1
            pnl = r.product() - 1 
        return pnl

    def returns_detailed(self):
        """
        Calculates the returns of a dataframe with the liquidity and slippage fees associated 
        Gives as second argument a pd series with number of trades
        """
        #get turnover of portfolio for the day in percentage
        weights_calc = self.weights+1
        df_turnover = weights_calc.pct_change()
        df_turnover[df_turnover!=0] = self.weight
        if self.strategy == "BTC":
            df_turnover.iloc[0,:] = 0
            df_turnover.iloc[0,0] = 1
        else:
            pass #FIRST ROW TURNOVER TO BE DONE FOR OTHER STRATEGIES 
        #get nbr of trades for gas fees calcs
        df_nbr_trades = df_turnover.copy()
        df_nbr_trades[df_nbr_trades != 0] = 1
        df_nbr_trades = df_nbr_trades.sum(axis=1)
        #multiply it with (SLIPPAGE + LIQUID FEE) 
        df_turnover = df_turnover.sum(axis=1)
        df_fees = df_turnover * (self.slippage_fee + self.liquidity_fee)
        df_returns_net = self.returns - df_fees
        return (df_nbr_trades, df_returns_net)

    def monthly_returns(self):
        #get first date and find first day of next month
        returns = self.returns
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

    def sharpe(self):
        """
        Returns the Sharpe ratio of returns given based on the earning rate of the Compound protocol
        """
        return round(((self.total_returns() - 1) - 0.0154) / self.returns.std(), 4) #0.0154 value is earnings of Compound on 01.01.23

    def beta(self):
        """
        Returns the beta of returns with the benchmark returns
        """
        df_cov = pd.concat([self.returns, self.bench_returns], axis=1).cov()
        return round(df_cov.iloc[0, 1] / df_cov.iloc[0,0],4)

    def trackingError(self):
        """
        returns the tracking error of returns and of a benchmark returns
        """
        return round((self.returns - self.bench_returns).std(),4)

    def informationRatio(self):
        """
        Returns the information ratio of returns
        """
        TE = self.trackingError()
        if TE != 0:
            return round((total_returns(self.returns) - total_returns(self.bench_returns)) / TE)
        else:
            return 0

    def bear_bull_returns(self):
        """
        Separates returns between bull and bear markets and gives a tuple with first bull market returns and then bear market returns
        Uses this analysis for dates of bull/bear markets https://crypto.com/research/crypto-bear-markets
        """
        #get all relevant bear markets as dateranges
        bear_market_dates = pd.date_range(start="06.26.2019", end="03.12.2020").union(pd.date_range(start="04.14.2021", end="05.17.2021")).union(pd.date_range(start="11.10.2021", end=datetime.today()))
        #create 2 dataframes by filtering out/in these dateranges in index
        returns = self.returns
        bear_market_dates = bear_market_dates[(bear_market_dates >= returns.index[0]) & (bear_market_dates <= returns.index[-1])]
        bear_returns = self.total_returns(returns=returns.loc[bear_market_dates]) - 1
        bull_returns = self.total_returns(returns=returns.drop(bear_market_dates)) - 1
        return (bull_returns, bear_returns)

    def gas_fee(self):
        """
        Determines the gas price which will be needed for all of the transactions
        Defaults to the Polygon network IF USED FOR OTHERN CHAINS IT SHOULD BE REWORKED
        """
        #df_gas_price cleaning
        df_gas_price = pd.read_csv("gas_price_gwei.csv") #gas price as csv from https://polygonscan.com/chart/gasprice TO BE UPDATED BY USING SELENIUM
        df_gas_price.set_index(pd.to_datetime(df_gas_price["Date(UTC)"]), inplace=True)
        df_gas_price = df_gas_price.iloc[:, 2].rename("wei")
        df_gas_price = pd.merge(self.df_price["matic_usd"], df_gas_price, right_index=True, left_index=True, how="left")
        df_gas_price["gas_fee_usd"] = df_gas_price.matic_usd * df_gas_price.wei * 10e-18 * 21000 #21000 is basic gas limit cost
        df_gas_price = df_gas_price["gas_fee_usd"].dropna()
        #combine with the number of trades
        df_nbr_trades = pd.DataFrame(self.nbr_trades, index=self.nbr_trades.index, columns=["nbr_trades"])
        df_gas_price = df_nbr_trades.merge(df_gas_price, how="left", left_index=True, right_index=True)
        df_gas_price.fillna(method="ffill", inplace=True)
        df_gas_price["total_usd"] = df_gas_price["nbr_trades"] * df_gas_price["gas_fee_usd"]
        return df_gas_price.total_usd.sum()


#get the data from postgres
df = pg.get_postgres(table_name="hist_prices", index_col="index")

#BTC only analysis
btc = Analyzer(df)
print(btc.returns)
print(btc)
exit()



#get volatility
df_vol = df_returns.rolling(VOL_WINDOW_DAYS).std()
df_vol.dropna(how="all", inplace=True)
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
