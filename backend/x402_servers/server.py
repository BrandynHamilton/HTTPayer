import os
import json
import logging
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
import requests
from eth_account import Account
from x402.clients.requests import x402_requests
import base64
import time
# ---------------------------------------------------------------------------
# env + bootstrap
# ---------------------------------------------------------------------------

load_dotenv()
PORT = int(os.getenv("MAIN_PORT", 3003))

raw_keys = os.getenv("PRIVATE_KEYS")
if not raw_keys:
    raise ValueError("Missing PRIVATE_KEYS in .env")
pk = raw_keys.split(",")[0].strip()
if not pk.startswith("0x"):
    pk = "0x" + pk
PRIVATE_KEY = pk

api_key = os.getenv("HTTPAYER_API_KEY")
if not api_key:
    raise ValueError("Missing HTTPAYER_API_KEY in .env")

account = Account.from_key(PRIVATE_KEY)
session = x402_requests(account)

print(f'account: {account.address}')

# ---------------------------------------------------------------------------
# flask app setup
# ---------------------------------------------------------------------------

def decode_x_payment(header: str) -> dict:
    """
    Decode a base64-encoded X-PAYMENT header back into its structured JSON form.

    :param header: Base64-encoded X-PAYMENT string
    :return: Parsed Python dictionary of the payment payload
    """
    try:
        decoded_bytes = base64.b64decode(header)
        decoded_json = json.loads(decoded_bytes)
        if not isinstance(decoded_json, dict):
            raise ValueError("Decoded X-PAYMENT is not a JSON object")
        return decoded_json
    except (ValueError, json.JSONDecodeError, base64.binascii.Error) as e:
        raise ValueError(f"Invalid X-PAYMENT header: {e}")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "server running"}), 200

@app.route("/httpayer", methods=["POST"])
def httpayer_proxy():
    if request.headers.get("x-api-key") != api_key:
        return jsonify({"error": "Unauthorized: invalid API key"}), 401

    try:
        data = request.get_json(force=True)
        api_url = data.get("api_url")
        method = data.get("method", "GET").upper()
        payload = data.get("payload")

        logging.info(f"[httpayer] → {method} {api_url}")

        # First request (to trigger 402)
        if method == "GET":
            initial_resp = requests.get(api_url)
        else:
            initial_resp = requests.request(method, api_url, json=payload)

        logging.info(f"[httpayer] first status {initial_resp.status_code}")

        if initial_resp.status_code != 402:
            return Response(initial_resp.content, status=initial_resp.status_code)

        resp_json = initial_resp.json()
        accepts = resp_json.get("accepts", [])
        exact = next((x for x in accepts if x.get("scheme") == "exact"), None)

        if not exact or "network" not in exact:
            return jsonify({"error": "Missing exact scheme or network"}), 400

        logging.info(f"[httpayer] paying… {{chain: {exact['network']}  to: {exact['payTo']}  amount: {exact['maxAmountRequired']}}}")

        # Send paid request
        headers = {"Connection": "close"}
        if method != "GET":
            headers["Content-Type"] = "application/json"

        paid_resp = session.request(method, api_url, json=payload if method != "GET" else None, headers=headers)

        if paid_resp.status_code == 402:
            logging.warning("[httpayer] first retry failed with 402, retrying once after delay")
            time.sleep(2)
            paid_resp = session.request(method, api_url, json=payload if method != "GET" else None, headers=headers)

        text = paid_resp.text

        logging.info(f"[httpayer] paid response: {text}")

        status = paid_resp.status_code

        logging.info(f"[httpayer] paid status {status}")

        # Optional callback
        pay_hdr = paid_resp.headers.get("X-PAYMENT-RESPONSE")
        if pay_hdr:
            decoded = decode_x_payment(pay_hdr)
            logging.info(f"[httpayer] decoded payment response: {json.dumps(decoded, indent=2)}")
            callback_url = decoded.get("callbackUrl") 
            tx_hash = decoded.get("transaction")

            if callback_url:
                try:
                    requests.post(
                        callback_url,
                        headers={"Content-Type": "application/json"},
                        json={"tx_hash": tx_hash}
                    )
                except Exception as e:
                    logging.warning(f"callback failed: {e}")

        return Response(text, status=status)

    except Exception as e:
        logging.error(f"[httpayer] error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# serve
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
    logging.info(f"Server running on port {PORT}")