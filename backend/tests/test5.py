import requests
from flask import Flask, request, jsonify, make_response
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

if network == 'avalanche':
    network_id = 'avalanche-fuji'
    if FACILITATOR_URL == "https://x402.org":
        raise ValueError("FACILITATOR_URL must be set to a valid URL for Avalanche Fuji testnet.")

w3 = network_func(network)

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
        return "<h1>Avalanche Weather Server</h1><p>Welcome to the Avalanche Weather Server!</p>"

    @app.route("/weather", methods=["POST"])
    @gate.gate
    def weather():
        data = request.json
        location = data.get("location", "default_location")
        print(f"Received weather request for location: {location}")
        # Simulate a weather response
        # In a real application, you would fetch actual weather data here
        # For demonstration, we return a static response
        response = make_response(jsonify({"weather": "sunny", "temp": 75, "location": location}))
        return response

    return app

if __name__ == "__main__":
    port = int(50351)
    print(f'Starting test4 on {port}...')
    app = create_app()
    app.run(host="0.0.0.0",port=port)