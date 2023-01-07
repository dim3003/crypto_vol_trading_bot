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
        "fantom": "250",
    }

    def __init__(self, from_address=None, chain='polygon', version='v5.0', slippage=5):
        self.from_address = from_address
        self.chain_id = self.chains[chain]
        self.version = version
        self.slippage = slippage

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


    #THOSE FUNCTIONS ARE TO BE DONE
    def get_allowance(self, token_name, wallet_address=None, **kwargs):
        """
        Calls the approve/allowance API endpoint. Gets the amount which is approved by the protocol to be spent.
        """
        if wallet_address == None:
            wallet_address = self.from_address
        
        tokens = self.get_tokens()
        TokenAddress = tokens.loc[token_name, "address"]
        url = f'{self.base_url}/{self.version}/{self.chain_id}/approve/allowance'
        url = url + f'?tokenAddress={TokenAddress}&walletAddress={wallet_address}'
        if kwargs is not None:
            result = self._get(url, params=kwargs)
        else:
            result = self._get(url)
        return result

    def approve_transaction(self, token_name):
        pass

    def get_swap(self, from_token_name, to_token_name, amount, slippage, decimal=18, **kwargs):
        """
        Calls the swap api endpoint. Allows for the creation of transactions on the 1inch protocol.
        """
        tokens = self.get_tokens()
        fromTokenAddress = tokens.loc[from_token_name, "address"]
        toTokenAddress = tokens.loc[to_token_name, "address"]
        decimals = tokens.loc[from_token_name, "decimals"]
        amount_in_wei = amount * 10 ** decimals
        
        url = f'{self.base_url}/{self.version}/{self.chain_id}/swap'
        url = url + f'?fromTokenAddress={fromTokenAddress}&toTokenAddress={toTokenAddress}&amount={amount_in_wei}'
        url = url + f'&fromAddress={self.from_address}&slippage={self.slippage}'
        if kwargs is not None:
            result = self._get(url, params=kwargs)
        else:
            result = self._get(url)
        return result


if __name__ == "__main__":
    bot = Bot(from_address="0x0f0c716b007c289c0011e470cc7f14de4fe9fc80", slippage=5)
    print(bot.healthcheck())
    df = pg.get_postgres(table_name="hist_prices", index_col="index")
    #Use an address that has got a lot of the tokens to be swapped to create the transaction and then create the same address on ganache to actually broadcast it on local network 
    print(bot.get_allowance(token_name="Ether"))
    bot.get_swap(from_token_name="Ether", to_token_name=df.columns[12], amount=1, slippage=0.05)
