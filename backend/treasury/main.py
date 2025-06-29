from flask import Flask, request, jsonify, render_template
from web3 import Web3
from eth_account import Account
from chartengineer import ChartMaker  # May need to comment out due to kaleido dependency issues
from plotly.utils import PlotlyJSONEncoder
from ccip_terminal.ccip import (send_ccip_transfer, get_account_info, get_ccip_fee_estimate, 
                                get_gas_limit_estimate, check_ccip_message_status)
from ccip_terminal.metadata import GAS_LIMITS_BY_CHAIN, USDC_MAP
from ccip_terminal.utils import get_dynamic_gas_fees, estimate_dynamic_gas
from ccip_terminal.network import network_func
from ccip_terminal.core import track_ccip_messages
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from threading import Lock
import math
import numpy as np
import json
import os
import asyncio
from dotenv import load_dotenv
import datetime as dt
import pandas as pd
from pathlib import Path
from diskcache import Cache
from typing import Dict, Tuple
from threading import Thread

from httpayer_core.treasury.burn_rate import (
    fetch_authorized_burns,
    rolling_burn,
    current_usdc_balance,
    runway_metrics
)

from httpayer_core.treasury.liquidity import rebalance_once

# Load environment variables
load_dotenv()
# PRIVATE_KEYS = os.getenv("PRIVATE_KEYS", "").split(",")[0] # ccip-terminal handles this for us in backend
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

cache = Cache('cache_dir')
LOG_PATH = Path("rebalance_log.csv")

abi_path = "../abi/erc20.json"
def load_abi():
    with open(abi_path, 'r') as file:
        return file.read()
    
scheduler = BackgroundScheduler()
job_lock = Lock()

global ccip_messages

ccip_messages = []

def run_in_thread(fn, *args, **kw):
    """Fire-and-forget helper (daemon=True)."""
    t = Thread(target=fn, args=args, kwargs=kw, daemon=True)
    t.start()
    return t

def safe_runway(r: Dict[str, float]) -> Dict[str, float]:
    """
    Convert JS-breaking Infinity / -Infinity to float('inf') / float('-inf').
    """
    safe = {}
    for k, v in r.items():
        if v in (float("inf"), float("-inf")) or (isinstance(v, str) and v.lower() == "inf"):
            safe[k] = float("inf")
        else:
            safe[k] = v
    return safe

def shutdown_scheduler(exception=None):
    if scheduler.running:
        scheduler.shutdown()

def clean_for_json(obj):
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(i) for i in obj]
    return obj

def compute_burn_rate_for_chains(chains: list[str], window_days=7) -> dict:
    results = {}
    PRIVATE_KEYS = os.getenv("PRIVATE_KEYS", "").split(",")

    for chain in chains:
        if chain not in GAS_LIMITS_BY_CHAIN:
            raise ValueError(f"Unsupported chain '{chain}'")

        for i, pk in enumerate(PRIVATE_KEYS):
            if not pk.strip():
                continue
            try:
                acct = Account.from_key(pk)
                account_address = acct.address
            except Exception as e:
                print(f"Invalid private key at index {i}: {e}")
                continue

            df_tx = fetch_authorized_burns(account_address, chain)
            # print(f'df_tx: {df_tx.head()}')
            cache.set(f"transactions_{chain}_{account_address}", df_tx)
            avg_7d, daily = rolling_burn(df_tx, window_days=window_days)

            w3 = network_func(chain)
            bal = current_usdc_balance(w3, USDC_MAP[chain], account_address)
            run = safe_runway(runway_metrics(bal, avg_7d))

            if chain not in results:
                results[chain] = {}

            results[chain][account_address] = {
                "average_burn_rate": str(avg_7d),
                "balance": str(bal),
                "runway": run,
                "daily_series": daily.to_dict("records"),
                "timestamp": dt.datetime.utcnow().isoformat()
            }

    rows = []
    for chain, chain_data in results.items():
        for address, metrics in chain_data.items():
            rows.append({
                "chain": chain,
                "address": address,
                "balance": float(metrics["balance"]),
                "runway": metrics["runway"],
                "avg_burn": float(metrics["average_burn_rate"]),
            })

    df_balances = pd.DataFrame(rows)
    total_balance = df_balances["balance"].sum()

    results["total_balance"] = total_balance
    results["balances"] = df_balances.to_dict("records")

    results_cleaned = clean_for_json(results)

    return results_cleaned

def create_app():
    app = Flask(__name__)

    def run_manage_liquidity():
        with app.app_context():
            if job_lock.locked():
                print("[Info] Previous liquidity job still running. Skipping this cycle.")
                return

            with job_lock:
                print("[Info] Running scheduled liquidity management job.")
                manage_liquidity()

    def scheduled_burn_rate_job():
        try:
            results = compute_burn_rate_for_chains(["base", "avalanche"])
            cache.set("data", results)
            print(f"[Info] Burn rate metrics cached at {dt.datetime.utcnow().isoformat()}")
        except Exception as exc:
            print(f"[ERROR] Scheduled burn rate job failed: {exc}")

    scheduler.add_job(
        run_manage_liquidity, 
        'interval', 
        minutes=2, 
        id='liquidity_management', 
        replace_existing=True
    )

    scheduler.add_job(
        scheduled_burn_rate_job,
        'interval',
        minutes=2,  # Every hour at :00
        id='hourly_burn_rate',
        replace_existing=True
    )

    @app.route('/treasury')
    def index():
        return render_template('index.html')
    
    @app.route('/treasury/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200
    
    @app.route('/treasury/cached-data', methods=['GET'])
    def get_cached_data():
        data = cache.get('data')
        ccip_messages = cache.get('ccip_messages', [])
        # print(f"Retrieved cached data: {data}")
        # print(f"CCIP messages: {ccip_messages}")
        return jsonify({'data':data,'messages':ccip_messages}), 200
    
    @app.route('/treasury/charts', methods=['GET'])
    def visualizations():

        data = cache.get('data', None)
        balances  = data.get('balances', None)
        # print(f"Balances: {balances}")

        balances_df = pd.DataFrame(balances)
        # print(f"Balances DataFrame:\n{balances_df}")

        cm1 = ChartMaker()
        cm1.build(
            df=balances_df,
            groupby_col='chain',
            num_col='balance',
            title='Chain Balances',
            chart_type='pie',
            options = {
                'margin':dict(t=100),'annotations':True,
                'tickprefix':{'y1':'$'},'hole_size':0.5,
                'line_width':0,
                'texttemplate':'%{label}<br>%{percent}',
                'show_legend':False,'legend_placement':{'x':1.1,'y':1},
                'textinfo':'percent+label'
            }
        )
        cm1.add_title()
        
        graph_json_1 = json.dumps(cm1.return_fig(), cls=PlotlyJSONEncoder)

        return jsonify({
            'graph_1': graph_json_1
        }), 200

    @app.route('/treasury/balances', methods=['GET'])
    def get_balances():
        w3 = network_func("ethereum")
        fees = get_dynamic_gas_fees(w3) 
        max_fee_per_gas = fees["max_fee_per_gas"]
        gas_limit_est = estimate_dynamic_gas("ethereum")
        estimate = ((gas_limit_est * max_fee_per_gas) / 1e18) * 1.25
        print(f"Gas limit estimate: {gas_limit_est}, Max fee per gas: {max_fee_per_gas}, Estimate: {estimate}")
        account_info = get_account_info(min_gas_threshold=estimate)
        return jsonify(account_info)
    
    @app.route('/treasury/gas_estimate', methods=['POST'])
    def gas_estimate():
        data = request.get_json()
        dest_chain = data.get('dest_chain')
        amount = data.get('amount')

        if not dest_chain or dest_chain not in GAS_LIMITS_BY_CHAIN.keys():
            return jsonify({"error": "Invalid or missing 'dest_chain'"}), 400
        
        if not isinstance(amount, (int, float)):
            return jsonify({"error": "Amount must be a number"}), 400
        
        try:
            gas_limit = get_gas_limit_estimate(dest_chain, amount)
            fee_estimate = get_ccip_fee_estimate(dest_chain, amount)
            return jsonify({
                "gas_limit": gas_limit,
                "fee_estimate": fee_estimate
            }), 200
        except Exception as e:
            print(f"Error during gas estimate: {e}")
            return jsonify({"error": str(e)}), 500
        
    @app.route("/treasury/burn_rate", methods=["POST"])
    def burn_rate():
        req = request.get_json() or {}
        chains = req.get("chains") or [req.get("chain", "base")]
        if isinstance(chains, str):
            chains = [c.strip() for c in chains.split(",")]

        try:
            results = compute_burn_rate_for_chains(chains, window_days=int(req.get("window_days", 7)))
            cache.set("burn_rate_bundle", results, expire=3600)
            return jsonify(results), 200
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route('/treasury/manage_liquidity', methods=['POST'])
    def manage_liquidity():

        try:
            messages, rebalance_summary = rebalance_once()
        except Exception as e:
            print(f"Error during liquidity management: {e}")
            return jsonify({"error": str(e)}), 500
        
        # Capture log entry
        timestamp = dt.datetime.utcnow().isoformat()
        
        # Flatten each action into its own row
        actions  = rebalance_summary.get("actions", [])
        skipped  = rebalance_summary.get("skipped", [])
        run_note = rebalance_summary.get("message")   # may be None

        # 1)  CSV timeseries log  ───────────────────────────────────────────
        rows = []

        for r in actions:
            rows.append({
                "timestamp"   : timestamp,
                "from"        : r["from"],
                "to"          : r["to"],
                "amount_usdc" : r["amount_usdc"],
                "success"     : r["success"],
                "message_id"  : r.get("message_id"),
                "tx_hash"     : r.get("tx_hash"),
                "status"      : "action",
            })

            ccip_url = r.get("ccip_url")
            if ccip_url:
                ccip_messages.append(ccip_url)
                cache.set("ccip_messages", ccip_messages)

        for s in skipped:
            rows.append({
                "timestamp"   : timestamp,
                "from"        : None,
                "to"          : s["chain"],
                "amount_usdc" : None,
                "success"     : False,
                "message_id"  : None,
                "tx_hash"     : None,
                "status"      : f"skipped: {s['reason']}",
            })

        # If there really was nothing to do, still write a row for posterity
        if not rows:
            rows.append({
                "timestamp"   : timestamp,
                "from"        : None,
                "to"          : None,
                "amount_usdc" : None,
                "success"     : None,
                "message_id"  : None,
                "tx_hash"     : None,
                "status"      : run_note or "no-op",
            })

        df = pd.DataFrame(rows)
        if LOG_PATH.exists():
            df.to_csv(LOG_PATH, mode="a", index=False, header=False)
        else:
            df.to_csv(LOG_PATH, index=False)

        # 2)  Console output  ───────────────────────────────────────────────
        if actions:
            for r in actions:
                print(f"{r['from']} ➜  {r['to']} | {r['amount_usdc']} USDC | success={r['success']}")
        else:
            print(run_note or "No rebalance actions this run.")

        for s in skipped:
            print(f"Skipped: {s['chain']} | Reason: {s['reason']}")

        # Message tracking
        if messages:
            run_in_thread(
                track_ccip_messages,
                messages,
                wait_for_status=True,
                poll_interval=60,
                max_retries=10,
            )

        return jsonify({"ok": True, "note": run_note}), 200
    
    @app.route('/treasury/transfer', methods=['POST'])
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
    
    @app.route('/treasury/check_status', methods=['POST'])
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
        
    run_manage_liquidity()
    scheduled_burn_rate_job()
        
    return app

if __name__ == "__main__":
    PORT = int(os.getenv('TREASURY_PORT', 5089))
    print(f"Starting Flask app on port {PORT}...")
    app = create_app()

    scheduler.start()

    for job in scheduler.get_jobs():
        print(f"[Info] Next run for {job.id} at {job.next_run_time}")

    app.run(port=PORT, host="0.0.0.0")