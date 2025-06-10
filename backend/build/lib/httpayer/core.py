import time
import json
import base64
import secrets
import requests

from eth_account import Account
from eth_account.messages import encode_typed_data

# ——————————————————————————————————————————
# Utility: create EIP-3009 authorization + signature
# ——————————————————————————————————————————
def _make_authorization(from_addr: str, to_addr: str, value: str, valid_secs: int = 6000):
    """Build the EIP-3009 authorization object."""
    valid_after  = 0
    valid_before = int(time.time()) + valid_secs
    nonce        = "0x" + secrets.token_hex(32)
    return {
        "from":        from_addr,
        "to":          to_addr,
        "value":       value,
        "validAfter":  str(valid_after),
        "validBefore": str(valid_before),
        "nonce":       nonce
    }

def _sign_exact(
    private_key: str,
    domain: dict,
    types: dict,
    primary_type: str,
    message: dict
) -> str:
    """EIP-712 encode → sign → return hex signature."""
    eip712_data = {
        "types":       types,
        "domain":      domain,
        "primaryType": primary_type,
        "message":     message
    }
    signable = encode_typed_data(full_message=eip712_data)
    acct     = Account.from_key(private_key)
    signed   = acct.sign_message(signable)
    return "0x" + signed.signature.hex()

# ——————————————————————————————————————————
# Core wrapper
# ——————————————————————————————————————————
def wrap_request_with_payment(
    session: requests.Session,
    payer_private_key: str,
    *,
    max_value: int,
    facilitator_verify_url: str,
    facilitator_settle_url: str
):
    """
    Returns a `get(url, **kwargs)`-like function that:
      1) does session.get(...)
      2) if status != 402 → returns it
      3) parses 402 JSON for paymentRequirements (assumes 'accepts' list)
      4) picks the first 'exact' scheme
      5) builds & signs EIP-3009 payload
      6) POSTS proof to facilitator /verify (optional) then /settle
      7) retries session.get(...) with X-PAYMENT header
    """

    def paid_get(url: str, **kwargs):
        # 1) initial request
        resp = session.get(url, **kwargs)
        if resp.status_code != 402:
            return resp

        body = resp.json()
        accepts = body.get("accepts", [])
        # pick first exact
        pr = next(filter(lambda x: x.get("scheme")=="exact", accepts), None)
        if not pr:
            raise RuntimeError("No 'exact' paymentRequirements in 402 payload")

        # 2) validate maxAmountRequired
        raw_amount = int(pr["maxAmountRequired"])
        if raw_amount > max_value:
            raise RuntimeError(f"Required {raw_amount} > max_value {max_value}")

        # 3) build auth object
        auth = _make_authorization(
            from_addr=Account.from_key(payer_private_key).address,
            to_addr=pr["payTo"],
            value=str(raw_amount)
        )

        print(f'response info: {pr["extra"]["name"], pr["extra"]["version"]}')
        print(json.dumps(pr, indent=2))

        # 4) prepare EIP-712 domain/types/message
        domain = {
            "name":              "USDC",
            "version":           "2",
            "chainId":           84531,
            "verifyingContract": pr["asset"]
        }
        types = {
            "EIP712Domain": [
                {"name":"name","type":"string"},
                {"name":"version","type":"string"},
                {"name":"chainId","type":"uint256"},
                {"name":"verifyingContract","type":"address"},
            ],
            "TransferWithAuthorization": [
                {"name":"token","type":"address"},
                {"name":"from","type":"address"},
                {"name":"to","type":"address"},
                {"name":"value","type":"uint256"},
                {"name":"validAfter","type":"uint256"},
                {"name":"validBefore","type":"uint256"},
                {"name":"nonce","type":"bytes32"},
            ],
        }
        message = {
            "token":       pr["asset"],
            "from":        auth["from"],
            "to":          auth["to"],
            "value":       raw_amount,
            "validAfter":  int(auth["validAfter"]),
            "validBefore": int(auth["validBefore"]),
            "nonce":       auth["nonce"],
        }

        # 5) sign EIP-3009
        print("\n=== DEBUG: EIP-3009 SIGNING ===")
        print("Domain:", json.dumps(domain, indent=2))
        print("Types:", json.dumps(types, indent=2))
        print("Message:", json.dumps(message, indent=2))
        print('Signing...')
        signed = Account.sign_typed_data(
        private_key=payer_private_key,
        domain_data=domain,
        message_types={
        "TransferWithAuthorization": types["TransferWithAuthorization"]
        },
        message_data=message
        )
        sig = "0x" + signed.signature.hex()

        # 6) build X-PAYMENT header
        payload = {
            "x402Version": 1,
            "scheme":      "exact",
            "network":     pr["network"],
            "payload": {
                "signature":     sig,
                "authorization": auth
            }
        }
        compact = json.dumps(payload, separators=(",",":")).encode()
        header_value = base64.b64encode(compact).decode()

        print("\n=== DEBUG: X-PAYMENT HEADER ===")
        print("Payload JSON:", json.dumps(payload, indent=2))
        print("Base64 Header:", header_value)
        print("Decoded JSON again:", json.loads(base64.b64decode(header_value)))
        print("────────────────────────────────────────────────────────────────────────\n")

        verify_body = {
            "x402Version": 1,
            "paymentHeader": header_value,
            "paymentRequirements": pr
        }

        # 7) optional: verify with facilitator
        verify_resp = session.post(
            facilitator_verify_url,
            json=verify_body
        )

        print(">>> POST /verify body:", json.dumps(verify_body, indent=2))
        print("<<< /verify response:", verify_resp.status_code, verify_resp.text)
        verify_json = verify_resp.json()
        if not verify_json.get("isValid", False):
            raise RuntimeError(f"Facilitator verify failed: {verify_json}")

        # 8) settle on chain (via facilitator)
        settle_resp = session.post(
            facilitator_settle_url,
            json={"x402Version":1, "paymentHeader": header_value, "paymentRequirements": pr}
        )
        if not settle_resp.ok:
            raise RuntimeError(f"Facilitator settle failed: {settle_resp.text}")

        # 9) retry original request with X-PAYMENT
        headers = kwargs.setdefault("headers", {})
        headers["X-PAYMENT"] = header_value
        # ensure we don’t loop forever
        headers["X-RETRY"]   = "1"

        return session.get(url, **kwargs)

    return paid_get
