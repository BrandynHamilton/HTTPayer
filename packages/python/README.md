# HTTPayer – Python SDK

**HTTPayer** is a Python SDK and decorator toolkit for accessing `402 Payment Required` resources using the [x402 protocol](https://github.com/x402/spec). It integrates with the HTTPayer router to enable seamless off-chain stablecoin payments using [EIP-3009](https://eips.ethereum.org/EIPS/eip-3009) and tokenized authorization headers.

This package provides:

- `HTTPayerClient`: a programmatic client for automatically paying 402 responses using a hosted HTTPayer server
- `X402Gate`: a decorator for protecting Web2 API endpoints using 402-compliant authorization and on-chain token metadata
- Environment-variable support for network/facilitator configuration

---

## Features

- Unified HTTPayer router integration
- Automatic retry on `402` with `X-PAYMENT` headers
- Flask endpoint protection with `X402Gate`
- EVM token metadata verification (name/version via `web3`)
- Compatible with Base Sepolia, Avalanche Fuji, and other testnets

---

## Installation

Install from source or using `pip`:

```bash
pip install httpayer
```

Install with demo dependencies (for Flask/CCIP demos):

```bash
pip install httpayer[demo]
```

---

## Environment Setup

For use of the HTTPayerClient class, you copy the `.env.sample` file into a `.env` file and fill the HTTPAYER_API_KEY variable with your API key.

```env
HTTPAYER_API_KEY=your-api-key
```

While the X402Gate class itself doesn't read environment variables, the test script included here does require several variables. To run that script it is reccomended you copy the `.env.sample` file into a `.env` file and fill in for the following:

```env
NETWORK=base
FACILITATOR_URL=https://x402.org
RPC_GATEWAY=https://your-gateway.example
PAY_TO_ADDRESS=0xYourReceivingAddress
```

---

## Usage

### HTTPayerClient

A client for paying 402-gated endpoints using a hosted HTTPayer router.

```python
from httpayer import HTTPayerClient

client = HTTPayerClient()

response = client.request("GET", "https://demo.httpayer.com/base-weather")

print(response.status_code)      # 200
print(response.headers)          # Includes X-PAYMENT-RESPONSE
print(response.json())           # Actual resource data
```

You can also manually call `pay_invoice(...)` if you already received a 402 response.

---

### X402Gate Decorator

A gate/decorator for protecting Flask API routes using x402 payment authorization headers.

```python
from httpayer import X402Gate
from web3 import Web3
from flask import Flask, request, jsonify, make_response

gate = X402Gate(
    pay_to="0xYourReceivingAddress",
    network="base-sepolia",
    asset_address="0xTokenAddress",
    max_amount=1000,  # atomic units (e.g. 0.001 USDC = 1000)
    asset_name="USD Coin",
    asset_version="2",
    facilitator_url="https://x402.org"
)

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return "<h1>Weather Server</h1><p>Welcome to the Weather Server!</p>"

    @app.route("/weather")
    @gate.gate
    def weather():
        response = make_response(jsonify({"weather": "sunny", "temp": 75}))
        return response

    return app
```

We can dynamically generate the payment requirements in our Flask app and add it to specific endpoints in our app. Each endpoint can have its own specialized payment instructions.

```python

gate_usdc = X402Gate(
    pay_to=...,
    network="base-sepolia",
    asset_address=USDC_ADDRESS,
    max_amount=1000000,
    ...
)

gate_dai = X402Gate(
    pay_to=...,
    network="avalanche-fuji",
    asset_address=DAI_ADDRESS,
    max_amount=2000000,
    ...
)

@app.route("/api/usdc-data")
@gate_usdc.gate
def usdc_endpoint():
    ...

@app.route("/api/dai-data")
@gate_dai.gate
def dai_endpoint():
    ...

```

---

## Examples

### test1.py – Programmatic Client Example

Runs multiple GET requests to x402-protected endpoints and prints response metadata.

```bash
python tests/test1.py
```

### test2.py – Flask Weather Server Demo

Starts a local API server with `/weather` and `/post-weather` endpoints that require a valid `X-PAYMENT` header:

```bash
python tests/test2.py
```

**_Note_** The HTTPayer server cannot pay a locally-hosted endpoint. You will need to use the x402 [Javascript](https://github.com/coinbase/x402/tree/main) or [Python](https://github.com/coinbase/x402/tree/main/python/x402) SDK to pay and test these endpoints if deployed locally.

Send payment using HTTPayer to the GET method endpoint:

```bash
http POST http://app.httpayer.com/pay \
  api_url=http://demo-server:5035/weather \
  method=GET \
  x-api-key:your-api-key
```

Send payment using HTTPayer to the POST method endpoint

```bash
http POST http://app.httpayer.com/pay \
  api_url=http://demo-server:5035/post-weather \
  method=POST \
  payload=YourCity \
  x-api-key:your-api-key
```

---

## Project Structure

```
httpayer/                 # Main package
├── __init__.py
├── client.py            # HTTPayerClient class
├── gate.py              # X402Gate and helpers
tests/
├── test1.py             # Client-based demo
├── test2.py             # Flask server demo
.env.sample              # Environment config template
pyproject.toml
README.md
```

---

## License

MIT License. See [LICENSE](LICENSE) for full details.

---

## Author

Created by [Brandyn Hamilton](mailto:brandynham1120@gmail.com)
