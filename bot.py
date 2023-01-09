import pandas as pd
import numpy as np
import requests, json
from web3 import Web3
from modules import postgres as pg

class OneInch():
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
        self.tokens = self.get_tokens()

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
        return r

    def healthcheck(self):
        """
        Calls the healthcheck endpoint
        returns 200 if API is stable
        """
        url = f"{self.base_url}/{self.version}/{self.chain_id}/healthcheck"
        r = self._get(url)
        return r["status"]


    def get_allowance(self, token_name, wallet_address=None, **kwargs):
        """
        Calls the approve/allowance API endpoint. Gets the amount which is approved by the protocol to be spent.
        """
        if wallet_address == None:
            wallet_address = self.from_address
        tokens = self.tokens
        TokenAddress = tokens.loc[token_name, "address"]
        url = f'{self.base_url}/{self.version}/{self.chain_id}/approve/allowance'
        url = url + f'?tokenAddress={TokenAddress}&walletAddress={wallet_address}'
        if kwargs is not None:
            result = self._get(url, params=kwargs)
        else:
            result = self._get(url)
        return result

    def approve_transaction(self, token_name, amount=None):
        """
        Calls the approve/transaction api endpoint is used to allow the spending of tokens.
        """
        tokens = self.tokens
        TokenAddress = tokens.loc[token_name, "address"]
        url = f'{self.base_url}/{self.version}/{self.chain_id}/approve/transaction'
        if amount is None:
            url = url + f"?tokenAddress={TokenAddress}"
        else:
            amount_in_wei = amount * 10 ** tokens.loc[token_name, "decimals"]
            url = url + f"?tokenAddress={TokenAddress}&amount={amount_in_wei}"
        result = self._get(url)
        return result

    def get_swap(self, from_token_name, to_token_name, amount, slippage, decimal=18, **kwargs):
        """
        Calls the swap api endpoint. Allows for the creation of transactions on the 1inch protocol.
        """
        tokens = self.tokens
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


class HelperWeb3():
    def __init__(self, public_key, private_key, rpc_url='http://127.0.0.1:8545'):
        self.public_key = public_key
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.w3 = self.connect()
    
    def __str__(self):
        return self.public_key

    def connect(self):
        if self.rpc_url[0:3] == "wss":
            w3 = Web3(Web3.WebsocketProvider(self.rpc_url)) 
        elif self.rpc_url[0:4] == "http":
            w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        else:
            w3 = Web3(Web3.IPCProvider(self.rpc_url))
        if w3.isConnected():
            print("Connected to the blockchain with RPC:", self.rpc_url)
            return w3
        else:
            print("Connection error please check.")
        
if __name__ == "__main__":
    """
    Addresses:
    - 0x5a4069c86f49d2454cf4ea9cda5d3bcb0f340c4b #an address found on polygon scan allowed to spend matic
    - 0x453699319d2866dc8F969F06A07eE3ee9a92306e #my Metamask test address on polygon
    
    bot = OneInch(from_address="0x453699319d2866dc8F969F06A07eE3ee9a92306e", slippage=5)
    print(bot.healthcheck())
    df = pg.get_postgres(table_name="hist_prices", index_col="index")
    print(bot.get_allowance(token_name="MATIC"))
    """
    helper = HelperWeb3(public_key="0x5a4069c86f49d2454cf4ea9cda5d3bcb0f340c4b", private_key="")
