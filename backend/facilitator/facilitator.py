from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from python_viem import get_chain_by_id
from web3 import Web3
import base64
from ccip_terminal.network import network_func
import os
import time
import json
from dataclasses import asdict
from eth_account import Account
from httpayer.x402_exact import (
    verify_exact,
    settle_exact,
    PaymentRequirements,
)
load_dotenv()

PRIVATE_KEYS = os.getenv("PRIVATE_KEYS", "")
PRIVATE_KEY = PRIVATE_KEYS.split(",")[1] if PRIVATE_KEYS else None

if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEYS environment variable must be set with at least one key.")

w3 = network_func('avalanche')
CHAIN_NAME = 'avalanche-fuji'
wallet  = Account.from_key(PRIVATE_KEY) if PRIVATE_KEY else None

# ───────────────────────── helpers ───────────────────────────
def _req_obj(j: dict) -> PaymentRequirements:
    """Convert incoming JSON -> dataclass (minimal fields)."""
    pr = j["paymentRequirements"]
    return PaymentRequirements(
        scheme              = pr["scheme"],
        network             = pr["network"],
        maxAmountRequired   = int(pr["maxAmountRequired"]),
        resource            = pr["resource"],
        payTo               = pr["payTo"],
        asset               = Web3.to_checksum_address(pr["asset"]),
        maxTimeoutSeconds   = pr.get("maxTimeoutSeconds", 60),
        extra               = pr["extra"],
    )

def _encode_header(settle_resp: dict) -> str:
    """exact-same Base64 (URL-safe, no padding) as JS SDK does."""
    raw = json.dumps(settle_resp, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

# ───────────────────────── Flask app ─────────────────────────
app = Flask(__name__)

@app.route("/facilitator/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "chainId": w3.eth.chain_id})

@app.route("/facilitator/supported", methods=["GET"])
def supported():
    return jsonify({
        "kinds": [{"scheme": "exact", "networkId": CHAIN_NAME}]
    })

@app.route("/facilitator/verify", methods=["POST"])
def verify():
    body = request.get_json(force=True)
    payload = body["paymentPayload"]["payload"]
    req     = _req_obj(body)

    result = verify_exact(w3, payload, req)
    return jsonify(asdict(result))

@app.route("/facilitator/settle", methods=["POST"])
def settle():
    body = request.get_json(force=True)
    payload = body["paymentPayload"]["payload"]
    req     = _req_obj(body)

    if wallet is None:
        payer = payload["authorization"]["from"]
        return jsonify({"success": False,
                        "errorReason": "no_signer_configured",
                        "transaction": "",
                        "network": req.network,
                        "payer": payer}), 200

    result = settle_exact(w3, wallet, payload, req)
    if result.success:
        # build header exactly like JS helper does
        header = _encode_header({
            "success":    True,
            "transaction": result.transaction,
            "network":     result.network,
            "payer":       result.payer,
            "ts":          int(time.time())
        })
        return jsonify({"header": header})

    # failure
    return jsonify(asdict(result))

if __name__ == "__main__":
    port = int(os.getenv("FACILITATOR_PORT", 5074))
    print(f"Facilitator live on {port}  (chainId {w3.eth.chain_id})")
    app.run(host="0.0.0.0", port=port)
