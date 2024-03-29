import pandas as pd
import numpy as np
import requests, json, os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from modules import postgres as pg
from dotenv import load_dotenv

#loads env variables 
load_dotenv() 
private_key = os.environ['PRIVATE_KEY']

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
        Slippage is in percentage so minimum 0 and max 50
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

    gas_oracle = "https://gas-price-api.1inch.io/v1.3/"

    def __init__(self, public_key, private_key=private_key, rpc_url='http://127.0.0.1:8545', chain_name='polygon'):
        self.rpc_url = rpc_url
        self.w3 = self.connect()
        if chain_name == 'polygon' or chain == 'avalanche':
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        else:
            pass
        self.public_key = public_key
        self.private_key = private_key
        self.chain = chain_name
        self.chain_id = self.chains[chain_name]
    
    def __str__(self):
        return self.public_key
    
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

    
    def get_balances(self, addresses, names, address=None, verbose=1):
        """
        Returns a pandas dataframe of balance of the account by giving a list of contracts and names.
        Works for the contracts tradable of 1inch
        """
        if address == None:
            address = self.public_key
        if len(addresses) != len(names):
            print("Length of contracts is not the same as length of names variable.")
            return 0
        balances = pd.Series(dtype=float)
        missing_decimals = 0
        missing_balanceOf = 0
        for i, address in enumerate(addresses):
            if verbose:
                print((i+1), "out of", len(addresses), names[i], address, "balance extraction", )
            with open(f"abi/{names[i]}.json") as f:
                abi = f.read()
                abi = json.loads(abi)
            address = self.w3.toChecksumAddress(address)
            contract = self.w3.eth.contract(address, abi=abi)
            try:
                decimals_raw = contract.functions.decimals().call()
            except Exception as err:
                print(err)
                print("Missing decimals function for", names[i], address)
                decimals_raw = 18
                missing_decimals += 1
            decimals = 10 ** decimals_raw
            try:
                value = contract.functions.balanceOf(self.public_key).call() // decimals
            except Exception as err:
                print(err)
                print("Missing balanceOf function for", names[i], address)
                decimals_raw = 18
                missing_balanceOf += 1
            balances = pd.concat([balances, pd.Series(value, index=[names[i]])])
        
        balances.sort_values(inplace=False)
        if verbose:
            print("Tokens missing balanceOf function", missing_balanceOf)
            print("Tokens missing decimals function", missing_decimals)
        self.balances = balances
        return balances

    def build_tx(self, raw_tx, speed='high'):
        """
        Cleans transaction parameters and sets the gas limit/price with the help of the inch oracle
        """
        nonce = self.w3.eth.getTransactionCount(self.public_key)
        if 'tx' in raw_tx:
            tx = raw_tx['tx']
        else:
            tx = raw_tx
        if 'from' not in tx:
            tx['from'] = self.w3.toChecksumAddress(self.public_key)
        tx['to'] = self.w3.toChecksumAddress(tx['to'])
        if 'gas' not in tx:
            tx['gas'] = self.w3.eth.estimate_gas(tx)
        tx['nonce'] = nonce
        tx['chainId'] = int(self.chain_id)
        tx['value'] = int(tx['value'])
        tx['gas'] = int(tx['gas'] * 1.25)
        if self.chain == 'ethereum' or self.chain == 'polygon' or self.chain == 'avalanche' or self.chain == 'gnosis':
            gas = self._get(self.gas_oracle+self.chain_id)
            # print(gas)
            # gas = requests.get(self.gas_oracle, params=self.chain_id)
            tx['maxPriorityFeePerGas'] = int(gas[speed]['maxPriorityFeePerGas'])
            tx['maxFeePerGas'] = int(gas[speed]['maxFeePerGas'])
            tx.pop('gasPrice')
        else:
            tx['gasPrice'] = int(tx['gasPrice'])
        return tx
    
    def sign_transaction(self, raw_tx):
        signed_tx = self.w3.eth.account.sign_message(raw_tx, private_key=self.private_key)
        return signed_tx

    def broadcast_tx(self, signed_tx, timeout=360):
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(tx_hash.hex())
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        return receipt, tx_hash.hex()

if __name__ == "__main__":
    """
    Addresses:
    - 0xA97578DD7ad20Ba12D42cB4100616f7d3797a72F #an address found on polygon scan allowed to spend matic
    - 0x453699319d2866dc8F969F06A07eE3ee9a92306e #my Metamask test address on polygon
    - 0xF9e5ca0FA7F2b8A07d2aC4Acb40F60cbBb7A6037 #ganache random address
    """
    #test transaction on 1inch.py through API
    from_address = "0xA97578DD7ad20Ba12D42cB4100616f7d3797a72F"
    df_names = pg.get_postgres()
    df_names.loc[df_names.symbol == "MATIC", "address"] = "0x0000000000000000000000000000000000001010"
    df_names.loc[df_names.symbol == "deUSDC", "address"] = "0xda43bfd7ecc6835aa6f1761ced30b986a574c0d2"
    df_names.loc[df_names.symbol == "NFTY", "address"] = "0xcc081220542a60a8ea7963c4f53d522b503272c1"
    # print(df_names.name)

    one_inch = OneInch(from_address=from_address)
    helper = HelperWeb3(public_key=from_address)
    
    print(helper.get_balances(verbose=0, addresses=[df_names.loc[df_names.name == "MATIC", "address"].iloc[0], df_names.loc[df_names.name == "Tether USD", "address"].iloc[0]], names=["MATIC", "Tether USD"]))
    result = one_inch.get_swap(from_token_name="MATIC", to_token_name="Tether USD", amount=1, slippage=2) #can only create swaps with api so impossible to do this step through ganache
    result = helper.build_tx(result)
    result = helper.sign_transaction(result)
    result = helper.send_raw_transaction(result)
    print(helper.get_balances(addresses=[df_names.loc[df_names.name == "MATIC", "address"].iloc[0], df_names.loc[df_names.name == "Tether USD", "address"].iloc[0]], names=["MATIC", "Tether USD"]))

    # print(helper.get_balances(addresses=df_names.address, names=df_names.name))


