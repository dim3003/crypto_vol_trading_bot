import pandas as pd
import numpy as np
import requests, json
from web3 import Web3
from modules import postgres as pg

class Bot():
    base_url = 'https://api.1inch.exchange'

    chains = {
        "ethereum": '1',
        "binance": '56',
        "polygon": "137",
        "optimism": "10",
        "arbitrum": "42161",
        "gnosis": "100",
        "avalanche": "43114",
        "fantom": "250"
    }

    def __init__(self, from_address=None, chain='polygon', version='v5.0'):
        self.from_address = from_address
        self.chain_id = self.chains[chain]
        self.version = version

    @staticmethod
    def _get(url, params=None, headers=None):
        """ Implements a get request """
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.ConnectionError as e:
            print("ConnectionError when doing a GET request from {}".format(url))
            payload = None
        except requests.exceptions.HTTPError:
            print("HTTPError {}".format(url))
            payload = None
        return payload

    def get_tokens(self):
        """
        Calls the token API endpoint
        """
        url = f'{self.base_url}/{self.version}/{self.chain_id}/tokens'
        result = self._get(url)
        if not result.__contains__('tokens'):
            return result
        r = result["tokens"]
        self.tokens = pd.DataFrame([r.name, r.address, r.decimals], columns=["name", "address", "decimals"], index=r.index)
        print(self.tokens)
        df_names.loc[df_names.symbol == "MATIC", "address"] = "0x0000000000000000000000000000000000001010"
        #create dataframe with address, name, decimals
        return self.tokens

    def healthcheck(self):
        """
        Calls the healthcheck endpoint
        returns 200 if API is stable
        """
        url = f"{self.base_url}/{self.version}/{self.chain_id}/healthcheck"
        r = self._get(url)
        return r["status"]

    def get_swap(self, from_token_name, to_token_name, amount, slippage, decimal=18):
        """
        Calls the swap api endpoint. Allows for the creation of transactions on the 1inch protocol.
        """
        url = f'{self.base_url}/{self.version}/{self.chain_id}/swap'
        url = url + f'?fromTokenAddress={fromTokenAddress}&toTokenAddress={toTokenAddress}&amount={amount_in_wei}'
        url = url + f'&fromAddress={send_address}&slippage={slippage}'
        if kwargs is not None:
            result = self._get(url, params=kwargs)
        else:
            result = self._get(url)
        return result


if __name__ == "__main__":
    bot = Bot()
    print(bot.healthcheck())
    bot.get_tokens()
    #df = pg.get_postgres(table_name="hist_prices", index_col="index")