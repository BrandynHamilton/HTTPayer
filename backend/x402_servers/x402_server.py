import requests
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from httpayer import X402Gate
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

USDC_MAP = {
    "avalanche-fuji": "0x5425890298aed601595a70ab815c96711a31bc65",
    "base-sepolia": "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    # Add more networks as desired
}

current_dir = os.path.dirname(os.path.abspath(__file__))

ERC20_ABI_PATH = os.path.join(current_dir, "../abi/erc20.json")
print(f'ERC20_ABI_PATH: {ERC20_ABI_PATH}')

with open(ERC20_ABI_PATH, 'r') as f:
    ERC20_ABI = f.read()

load_dotenv()

BASE_SEPOLIA_GATEWAY = os.getenv("BASE_SEPOLIA_GATEWAY")
AVALANCHE_FUJI_GATEWAY = os.getenv("AVALANCHE_FUJI_GATEWAY")

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org")
PAY_TO_ADDRESS = os.getenv("PAY_TO_ADDRESS", "0x58a4Cae5e8dDA3a5614972F34951e482a29ef0f0")

print(f'FACILITATOR_URL: {FACILITATOR_URL}')

def get_network_details(network):

    if network == 'avalanche-fuji':
        RPC_GATEWAY = AVALANCHE_FUJI_GATEWAY
    elif network == 'base-sepolia':
        RPC_GATEWAY = BASE_SEPOLIA_GATEWAY

    w3 = Web3(Web3.HTTPProvider(RPC_GATEWAY))

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

avalanche_details = get_network_details('avalanche-fuji')
base_details = get_network_details('base-sepolia')

avalanche_gate = X402Gate(
    pay_to=PAY_TO_ADDRESS,
    network='avalanche-fuji',
    asset_address=USDC_MAP.get('avalanche-fuji'),
    max_amount=1000,
    asset_name=avalanche_details["name"],
    asset_version=avalanche_details["version"],
    facilitator_url=FACILITATOR_URL
)

base_gate = X402Gate(
    pay_to=PAY_TO_ADDRESS,
    network='base-sepolia',
    asset_address=USDC_MAP.get('base-sepolia'),
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

    @app.route("/base-weather", methods=['GET'])
    @base_gate.gate
    def base_weather():
        response = make_response(jsonify({"weather": "sunny", "temp": 75}))
        return response

    @app.route("/avalanche-weather", methods=['GET'])
    @avalanche_gate.gate
    def avalanche_weather():
        response = make_response(jsonify({"weather": "sunny", "temp": 75}))
        return response

    return app

if __name__ == "__main__":
    port = int(os.getenv("X402_SERVER_PORT", 5036))
    print(f'Starting test4 on {port}...')
    app = create_app()
    app.run(host="0.0.0.0",port=port)