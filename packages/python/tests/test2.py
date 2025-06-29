import requests
from flask import Flask, request, jsonify, make_response
from web3 import Web3
from httpayer import X402Gate
import os
from dotenv import load_dotenv

from ccip_terminal.metadata import USDC_MAP
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))

ERC20_ABI_PATH = os.path.join(current_dir, "abi/erc20.json")
print(f'ERC20_ABI_PATH: {ERC20_ABI_PATH}')

with open(ERC20_ABI_PATH, 'r') as f:
    ERC20_ABI = f.read()

load_dotenv()

network = os.getenv("NETWORK", "base").lower()

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org")
PAY_TO_ADDRESS = os.getenv("PAY_TO_ADDRESS", None)
RPC_GATEWAY = os.getenv("RPC_GATEWAY", None)

if not PAY_TO_ADDRESS:
    raise ValueError("PAY_TO_ADDRESS must be set in the environment variables.")

if not RPC_GATEWAY:
    raise ValueError("RPC_GATEWAY must be set in the environment variables.")

print(f'FACILITATOR_URL: {FACILITATOR_URL}')
print(f'PAY_TO_ADDRESS: {PAY_TO_ADDRESS}')
print(f'RPC_GATEWAY: {RPC_GATEWAY}')

if network == 'avalanche':
    network_id = 'avalanche-fuji'
    if FACILITATOR_URL == "https://x402.org":
        raise ValueError("FACILITATOR_URL must be set to a valid URL for Avalanche Fuji testnet.")
elif network == 'base':
    network_id = 'base-sepolia'
    if FACILITATOR_URL != "https://x402.org":
        raise ValueError("FACILITATOR_URL must be set to a valid URL for Base Sepolia testnet.")

w3 = Web3(Web3.HTTPProvider(RPC_GATEWAY))

token_address = USDC_MAP.get(network)

token_contract = w3.to_checksum_address(token_address)
token = w3.eth.contract(address=token_contract, abi=ERC20_ABI)
name_onchain    = token.functions.name().call()
version_onchain = token.functions.version().call() 

extra = {"name": name_onchain, "version": version_onchain}

print(f'Network: {network}, Network ID: {network_id}, extra: {extra}')

gate = X402Gate(
    pay_to=PAY_TO_ADDRESS,
    network=network_id,
    asset_address=token_address,
    max_amount=1000,
    asset_name=extra["name"],
    asset_version=extra["version"],
    facilitator_url=FACILITATOR_URL
)

def create_app():
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return "OK", 200

    @app.route('/')
    def index():
        return "<h1>Demo Weather Server</h1><p>Welcome to the Demo Weather Server!</p>"

    @app.route("/weather")
    def weather():
        request_data = {
            "headers": dict(request.headers),
            "url": request.base_url
        }

        @gate.gate
        def protected(_request_data):
            return {
                "status": 200,
                "headers": {},
                "body": {
                    "weather": "sunny",
                    "temp": 75
                }
            }

        result = protected(request_data)

        return make_response(jsonify(result["body"]), result["status"], result.get("headers", {}))

    return app

if __name__ == "__main__":
    port = int(os.getenv("TEST_SERVER_PORT", 50358))
    print(f'Starting demo on {port}...')
    app = create_app()
    app.run(host="0.0.0.0",port=port)