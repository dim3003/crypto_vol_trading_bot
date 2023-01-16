import json, os, requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

#loads env variables 
load_dotenv()
POLYSCAN_API_KEY = os.environ["POLYSCAN_API_KEY"]
POLYGONSCAN_ABI_ENDPOINT = 'https://api.polygonscan.com/api?module=contract&action=getabi'
POLYGONSCAN_TOKEN = 'https://polygonscan.com/token/'

def get_abi(contract_address, api_key=POLYSCAN_API_KEY):
    """
    Calls Polygonscan contract abi endpoint with given contract address and api_key
    Checks if there is a proxy implementation first
    """
    #check with bs4 if there is an abi implementation as the contract can be a proxy
    url_token = POLYGONSCAN_TOKEN + contract_address + "#readProxyContract"
    r = requests.get(url_token)
    soup = BeautifulSoup(r.content, 'html5lib')
    proxy_span = soup.find(id='ContentPlaceHolder1_readProxyMessage')
    if proxy_span.find("a"):
        contract_address = proxy_span.find("a").text
    #get the abi 
    url = POLYGONSCAN_ABI_ENDPOINT
    url = url + f'&address={contract_address}&apikey={api_key}'
    r = requests.get(url)
    r = r.json()["result"]
    return r

if __name__ == '__main__':
    get_abi("0x0000000000000000000000000000000000001010")
    get_abi("0xd6df932a45c0f255f85145f286ea0b292b21c90b")