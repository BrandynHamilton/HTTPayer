import requests
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from httpayer import X402Gate
import os
from dotenv import load_dotenv

from ccip_terminal.metadata import USDC_MAP
from ccip_terminal.network import network_func
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))

ERC20_ABI_PATH = os.path.join(current_dir, "../abi/erc20.json")
print(f'ERC20_ABI_PATH: {ERC20_ABI_PATH}')

with open(ERC20_ABI_PATH, 'r') as f:
    ERC20_ABI = f.read()

load_dotenv()

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org")
PAY_TO_ADDRESS = os.getenv("PAY_TO_ADDRESS", "0x58a4Cae5e8dDA3a5614972F34951e482a29ef0f0")

print(f'FACILITATOR_URL: {FACILITATOR_URL}')

network = 'avalanche'

# if network == 'avalanche':
#     network_id = 'avalanche-fuji'
#     if FACILITATOR_URL == "https://x402.org":
#         raise ValueError("FACILITATOR_URL must be set to a valid URL for Avalanche Fuji testnet.")

def get_network_details(network):

    w3 = network_func(network)

    token_address = USDC_MAP.get(network)
    if not token_address:
        raise ValueError(f"No USDC address found for network: {network}")
    token_contract = w3.to_checksum_address(token_address)
    token = w3.eth.contract(address=token_contract, abi=ERC20_ABI)
    name_onchain    = token.functions.name().call()
    version_onchain = token.functions.version().call() 

    extra = {"name": name_onchain, "version": version_onchain}

    print(f'Network: {network}, extra: {extra}')

    return extra

avalanche_details = get_network_details('avalanche')
base_details = get_network_details('base')

avalanche_gate = X402Gate(
    pay_to=PAY_TO_ADDRESS,
    network='avalanche-fuji',
    asset_address=USDC_MAP.get('avalanche'),
    max_amount=1000,
    asset_name=avalanche_details["name"],
    asset_version=avalanche_details["version"],
    facilitator_url=FACILITATOR_URL
)

base_gate = X402Gate(
    pay_to=PAY_TO_ADDRESS,
    network='base-sepolia',
    asset_address=USDC_MAP.get('base'),
    max_amount=1000,
    asset_name=base_details["name"],
    asset_version=base_details["version"],
    facilitator_url="https://x402.org"
)

def create_app():
    app = Flask(__name__)

    CORS(app)

    @app.route("/health")
    def health():
        return "OK", 200

    @app.route("/")
    def index():
        return "<h1>x402 Demo Server</h1><p>Welcome to the x402 Demo Server!</p>"

    @app.route("/avalanche-weather")
    def avalanche_weather():
        request_data = {
            "headers": dict(request.headers),
            "url": request.base_url
        }

        def handler(_request_data):
            return {
                "status": 200,
                "headers": {},
                "body": {
                    "data": {
                        "body": {
                            "weather": "sunny",
                            "temp": 75
                        }
                    },
                    "error": False
                }
            }

        result = avalanche_gate.gate(handler)(request_data)
        return make_response(jsonify(result["body"]), result["status"], result.get("headers", {}))

    @app.route("/base-weather")
    def base_weather():
        request_data = {
            "headers": dict(request.headers),
            "url": request.base_url
        }

        def handler(_request_data):
            return {
                "status": 200,
                "headers": {},
                "body": {
                    "body": {
                        "weather": "sunny",
                        "temp": 75
                    },
                    "error": False
                }
            }

        result = base_gate.gate(handler)(request_data)
        return make_response(jsonify(result["body"]), result["status"], result.get("headers", {}))

    return app

if __name__ == "__main__":
    port = int(os.getenv("X402_SERVER_PORT", 5036))
    print(f'Starting test4 on {port}...')
    app = create_app()
    app.run(host="0.0.0.0",port=port)