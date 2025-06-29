from functools import wraps
import requests
from typing import Callable, Dict, Any
from web3 import Web3
import base64, json

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

def _encode_settle_header(settle_json: dict) -> str:
    compact = json.dumps(settle_json, separators=(",", ":"))
    return base64.b64encode(compact.encode()).decode()

class X402Gate:
    def __init__(self, *, pay_to, network, asset_address,
                 max_amount, asset_name, asset_version,
                 facilitator_url):
        self.pay_to          = Web3.to_checksum_address(pay_to)
        self.network         = network
        self.asset_address   = Web3.to_checksum_address(asset_address)
        self.max_amount      = int(max_amount)
        base                 = facilitator_url.rstrip('/')
        self.verify_url      = f"{base}/facilitator/verify"
        self.settle_url      = f"{base}/facilitator/settle"
        self.asset_name      = asset_name
        self.asset_version   = asset_version

    def _verify(self, hdr: str, reqs: dict):
        payload = decode_x_payment(hdr)
        r = requests.post(
            self.verify_url,
            json={
                "x402Version": 1,
                "paymentPayload": payload,
                "paymentRequirements": reqs,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    def _settle(self, hdr: str, reqs: dict):
        payload = decode_x_payment(hdr)
        r = requests.post(
            self.settle_url,
            json={
                "x402Version": 1,
                "paymentPayload": payload,
                "paymentRequirements": reqs,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    def gate(self, view_fn: Callable[[Dict[str, Any]], Any]) -> Callable:
        @wraps(view_fn)
        def wrapper(request_data: Dict[str, Any], *args, **kwargs):
            """
            request_data: a dict-like object with:
              - 'headers': dict
              - 'url': full resource URL
            """

            req_json = {
                "scheme": "exact",
                "network": self.network,
                "maxAmountRequired": str(self.max_amount),
                "resource": request_data.get("url"),
                "description": "",
                "mimeType": "",
                "payTo": self.pay_to,
                "maxTimeoutSeconds": 60,
                "asset": self.asset_address,
                "extra": {
                    "name": self.asset_name,
                    "version": self.asset_version
                }
            }

            pay_header = request_data.get("headers", {}).get("X-Payment")
            if not pay_header:
                return {
                    "status": 402,
                    "headers": {},
                    "body": {
                        "x402Version": 1,
                        "error": "X-PAYMENT header is required",
                        "accepts": [req_json]
                    }
                }

            try:
                self._verify(pay_header, req_json)
            except Exception as exc:
                return {
                    "status": 402,
                    "headers": {},
                    "body": {
                        "x402Version": 1,
                        "error": f"verification failed: {exc}",
                        "accepts": [req_json]
                    }
                }

            resp = view_fn(request_data, *args, **kwargs)

            try:
                settle_json = self._settle(pay_header, req_json)
                settle_hdr = _encode_settle_header(settle_json)
                resp_headers = resp.get("headers", {})
                resp_headers["X-PAYMENT-RESPONSE"] = settle_hdr
                resp["headers"] = resp_headers
                return resp
            except Exception as exc:
                return {
                    "status": 402,
                    "headers": {},
                    "body": {
                        "x402Version": 1,
                        "error": f"settlement failed: {exc}",
                        "accepts": [req_json]
                    }
                }

        return wrapper
