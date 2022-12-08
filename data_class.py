

# Crypto price data fetcher class
#--------------------------------
class PriceCrypto:
    def __init__(self):
        """
        Datetime should be YYYY-MM-DD
        methods:
        """
        pass
    def __str__(self):
        print("START TIME:  " + "UNDEFINED")

    def getDf(crypto, start, end):
        try:
            df = san.get(
                f"ohlcv/{crypto}",
                from_date=start,
                to_date=end,
                interval="1d"
            )
            return df
        except Exception as e:
            print(e)