from modules import postgres as pg
from modules.analyzer import Analyzer

#get the data from postgres
df = pg.get_postgres(table_name="hist_prices", index_col="index")
#BTC only analysis
btc = Analyzer(df)
print(btc)

#low volatility
for i in range(10,60,10):
    low_vol = Analyzer(df, bench_returns=btc.returns, strategy="LOW_VOLATILITY", cryptos_taken_percentage=i)
    print(low_vol)

#high volatility
for i in range(1,11,1):
    high_vol = Analyzer(df, bench_returns=btc.returns, strategy="HIGH_VOLATILITY", cryptos_taken_percentage=i)
    print(high_vol)