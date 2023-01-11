import json, os, requests
from dotenv import load_dotenv

#loads env variables 
load_dotenv()
POLYSCAN_API_KEY = os.environ["POLYSCAN_API_KEY"]
POLYGONSCAN_ABI_ENDPOINT = 'https://api.polygonscan.com/api?module=contract&action=getabi'

def get_abi(contract_address, api_key=POLYSCAN_API_KEY):
    # Exports contract ABI in JSON
    url = POLYGONSCAN_ABI_ENDPOINT
    url = url + f'&address={contract_address}&apikey={api_key}'
    r = requests.get(url)
    r = r.json()["result"]
    return r

if __name__ == '__main__':
    print(get_abi("0x0000000000000000000000000000000000001010"))