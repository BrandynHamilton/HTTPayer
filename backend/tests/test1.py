from httpayer_core import wrap_request_with_payment
import requests
import os
from dotenv import load_dotenv
load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")

session = requests.Session()
# session.headers.update({…}) if you need global headers/API-keys, etc.

# Pass in your private key and optionally a max spend (in raw USDC units)
paid_get = wrap_request_with_payment(
    session=session,
    payer_private_key=PRIVATE_KEY,
    max_value=1000,                       # e.g. allow up to 1000 raw USDC
    facilitator_verify_url="https://x402.org/facilitator/verify",
    facilitator_settle_url="https://x402.org/facilitator/settle",
)

# Then use paid_get exactly like requests.get:
resp = paid_get("http://localhost:4021/weather")
print(resp.status_code, resp.json())

