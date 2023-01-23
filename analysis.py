from modules import postgres as pg
from operator import itemgetter
from modules.analyzer import Analyzer

#get the data from postgres
df = pg.get_postgres(table_name="hist_prices", index_col="index")
#BTC only analysis
btc = Analyzer(df)
print(btc)

#low volatility
returns_with_fees = []
for i in range(1,101,1):
    low_vol = Analyzer(df, bench_returns=btc.returns, strategy="LOW_VOLATILITY", cryptos_taken_percentage=i)
    returns_with_fees.append((low_vol.returns_with_fees, i))
#print the one with the highest returns with no fee
print(Analyzer(df, bench_returns=btc.returns, strategy="LOW_VOLATILITY", cryptos_taken_percentage=max(returns_with_fees, key=itemgetter(0))[1]))

#high volatility
returns_with_fees = []
for i in range(1,101,1):
    high_vol = Analyzer(df, bench_returns=btc.returns, strategy="HIGH_VOLATILITY", cryptos_taken_percentage=i)
    returns_with_fees.append((high_vol.returns_with_fees, i))
#print the one with the highest returns with no fee
print(Analyzer(df, bench_returns=btc.returns, strategy="HIGH_VOLATILITY", cryptos_taken_percentage=max(returns_with_fees, key=itemgetter(0))[1]))