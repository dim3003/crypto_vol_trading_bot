import pandas as pd
import numpy as np
import requests, json
from web3 import Web3
from modules import postgres as pg

"""
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
print(w3.isConnected())
print(w3.eth.get_block('latest'))
"""


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
    
    def healthcheck(self):
        """
        Calls the healthcheck endpoint
        returns 200 if API is stable
        """
        url = f"{self.base_url}/{self.version}/{self.chain_id}/healthcheck"
        r = self._get(url)
        return r["status"]

    def swap(self):
        pass


if __name__ == "__main__":
    bot = Bot()
    print(bot.healthcheck())