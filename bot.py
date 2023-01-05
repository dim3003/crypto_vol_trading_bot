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
        r = pd.DataFrame(r).T.loc[:, ["name", "address", "decimals"]]
        r.name = r.name + "_USD" # TO BE REMOVED
        r.set_index(r["name"], inplace=True)
        r.drop("name", axis=1, inplace=True)
        self.tokens = r
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
        tokens = self.get_tokens()
        print(tokens)

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
    df = pg.get_postgres(table_name="hist_prices", index_col="index")
    bot.get_swap(from_token_name=df.columns[4], to_token_name=df.columns[12], amount=1, slippage=0.05)