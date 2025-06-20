import time
import json
import base64
import secrets
import requests

from eth_account import Account
from web3 import Web3

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

def _make_authorization(from_addr: str, to_addr: str, value: str, valid_secs: int = 60):
    """Build EIP-3009 authorization object."""
    now = int(time.time())
    return {
        "from": from_addr,
        "to": to_addr,
        "value": value,
        "validAfter": str(now),
        "validBefore": str(now + valid_secs),
        "nonce": "0x" + secrets.token_bytes(32).hex(),
    }

def _sign_exact(private_key: str, domain: dict, types: dict, primary_type: str, message: dict) -> str:
    """EIP-712 sign with eth_account.sign_typed_data()."""
    print(f'EIP-712 full message:\n{json.dumps({"domain": domain, "types": types, "primaryType": primary_type, "message": message}, indent=2)}')
    signed = Account.sign_typed_data(
        private_key=private_key,
        domain_data=domain,
        message_types=types,
        message_data=message
    )
    return "0x" + signed.signature.hex()

def wrap_request_with_payment(session: requests.Session, payer_private_key: str, *,
                               max_value: int,
                               facilitator_verify_url: str,
                               facilitator_settle_url: str):
    """Return `get()`-like function with X-PAYMENT logic."""

    def paid_get(url: str, **kwargs):
        resp = session.get(url, **kwargs)
        if resp.status_code != 402:
            return resp

        body = resp.json()
        accepts = body.get("accepts", [])
        print(f'accepts: {accepts}')
        pr = next((x for x in accepts if x.get("scheme") == "exact"), None)
        if not pr:
            raise RuntimeError("No 'exact' scheme in 402 paymentRequirements")

        raw_amount = str(int(pr["maxAmountRequired"]))
        if int(raw_amount) > max_value:
            raise RuntimeError(f"Required {raw_amount} exceeds max_value {max_value}")

        from_address = Account.from_key(payer_private_key).address
        auth = _make_authorization(
            from_addr=from_address,
            to_addr=pr["payTo"],
            value=raw_amount,
        )

        domain = {
            "name": pr["extra"]["name"],
            "version": pr["extra"]["version"],
            "chainId": 84531,  # Hardcoded for Base Sepolia
            "verifyingContract": Web3.to_checksum_address(pr["asset"])
        }

        types = {
            # "EIP712Domain": [
            #     {"name": "name", "type": "string"},
            #     {"name": "version", "type": "string"},
            #     {"name": "chainId", "type": "uint256"},
            #     {"name": "verifyingContract", "type": "address"},
            # ],
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ]
        }

        message = {
            "from": auth["from"],
            "to": auth["to"],
            "value": int(auth["value"]),
            "validAfter": int(auth["validAfter"]),
            "validBefore": int(auth["validBefore"]),
            "nonce": auth["nonce"],
        }

        sig = _sign_exact(
            private_key=payer_private_key,
            domain=domain,
            types=types,
            primary_type="TransferWithAuthorization",
            message=message
        )

        payload = {
            "x402Version": 1,
            "scheme": "exact",
            "network": pr["network"],
            "payload": {
                "signature": sig,
                "authorization": auth
            }
        }

        compact = json.dumps(payload, separators=(",", ":")).encode()
        header_value = base64.b64encode(compact).decode()

        print("\n=== DEBUG: X-PAYMENT HEADER ===")
        print("Payload JSON:", json.dumps(payload, indent=2))
        print("Base64 Header:", header_value)
        print("Decoded JSON:", json.loads(base64.b64decode(header_value)))
        print("────────────────────────────────────────────────────────────────────────\n")

        # 7) optional: verify with facilitator
        # verify_resp = session.post(
        #     facilitator_verify_url,
        #     json={
        #         "x402Version": 1,
        #         "paymentHeader": header_value,
        #         "paymentRequirements": pr
        #     }
        # )
        # if not verify_resp.ok:
        #     raise RuntimeError(f"Facilitator verify failed: {verify_resp.text}")

        # 8) optional: settle with facilitator
        # settle_resp = session.post(
        #     facilitator_settle_url,
        #     json={
        #         "x402Version": 1,
        #         "paymentHeader": header_value,
        #         "paymentRequirements": pr
        #     }
        # )
        # if not settle_resp.ok:
        #     raise RuntimeError(f"Facilitator settle failed: {settle_resp.text}")

        headers = kwargs.setdefault("headers", {})
        headers["X-PAYMENT"] = header_value
        headers["X-RETRY"] = "1"

        return session.get(url, **kwargs)

    return paid_get
