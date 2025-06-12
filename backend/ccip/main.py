from flask import Flask, request, jsonify
from web3 import Web3
from eth_account import Account
from ccip_terminal.ccip import (send_ccip_transfer, get_account_info, get_ccip_fee_estimate, 
                                get_gas_limit_estimate, check_ccip_message_status)
from ccip_terminal.metadata import GAS_LIMITS_BY_CHAIN
from ccip_terminal.utils import get_dynamic_gas_fees, estimate_dynamic_gas
from ccip_terminal.network import network_func
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PRIVATE_KEYS = os.getenv("PRIVATE_KEYS", "").split(",")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

abi_path = "../abi/erc20.json"
def load_abi():
    with open(abi_path, 'r') as file:
        return file.read()
    
scheduler = BackgroundScheduler()

def shutdown_scheduler(exception=None):
    if scheduler.running:
        scheduler.shutdown()

def create_app():
    app = Flask(__name__)

    @app.route('/balances', methods=['GET'])
    def get_balances():
        w3 = network_func("ethereum")
        fees = get_dynamic_gas_fees(w3) 
        max_fee_per_gas = fees["max_fee_per_gas"]
        gas_limit_est = estimate_dynamic_gas("ethereum")
        estimate = ((gas_limit_est * max_fee_per_gas) / 1e18) * 1.25
        print(f"Gas limit estimate: {gas_limit_est}, Max fee per gas: {max_fee_per_gas}, Estimate: {estimate}")
        account_info = get_account_info(min_gas_threshold=estimate)
        return jsonify(account_info)

    @app.route('/manage_liquidity', methods=['POST'])
    def manage_liquidity():
        print("pass")

    @app.route('/transfer', methods=['POST'])
    def transfer():
        data = request.get_json()
        to = data.get('to', ACCOUNT_ADDRESS)
        dest = data.get('dest')
        amount = data.get('amount')

        if not any([to, dest, amount]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if not isinstance(amount, (int, float)):
            return jsonify({"error": "Amount must be a number"}), 400
        
        if not to.startswith("0x"):
            return jsonify({"error": "Invalid 'to' address format"}), 400
        
        if dest not in GAS_LIMITS_BY_CHAIN.keys():
            return jsonify({"error": "Invalid destination chain"}), 400
        
        try:
        
            receipt, links, success, message_id = send_ccip_transfer(
                to_address=to,
                dest_chain=dest,
                amount=amount,
            )

            return jsonify({
                "receipt": receipt,
                "links": links,
                "success": success,
                "message_id": message_id
            }), 200
        except Exception as e:
            print(f"Error during transfer: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/check_status', methods=['POST'])
    def check_status():
        data = request.get_json()
        message_id = data.get('message_id')
        dest = data.get('dest')

        if not dest or dest not in GAS_LIMITS_BY_CHAIN.keys():
            return jsonify({"error": "Invalid or missing 'dest' chain"}), 400

        if not message_id:
            return jsonify({"error": "Missing 'message_id'"}), 400
        
        try:
            status = check_ccip_message_status(message_id, dest)
            return jsonify(status), 200
        except Exception as e:
            print(f"Error checking status: {e}")
            return jsonify({"error": str(e)}), 500
        
    return app

if __name__ == "__main__":
    app = create_app()
    print("Starting Flask app...")
    scheduler.start()
    app.run(debug=True, use_reloader=True, port=5089)