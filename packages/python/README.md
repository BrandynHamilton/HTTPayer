# HTTPayer – Python SDK

**HTTPayer** is a Python SDK and decorator toolkit for accessing `402 Payment Required` resources using the [x402 protocol](https://github.com/x402/spec). It integrates with the HTTPayer router to enable seamless off-chain stablecoin payments using [EIP-3009](https://eips.ethereum.org/EIPS/eip-3009) and tokenized authorization headers.

This package provides:

- `HttPayerClient`: a programmatic client for automatically paying 402 responses using a hosted HTTPayer server
- `X402Gate`: a decorator for protecting Web2 API endpoints using 402-compliant authorization and on-chain token metadata
- Environment-variable support for network/facilitator configuration

---

## Features

- Unified HTTPayer router integration
- Automatic retry on `402` with `X-PAYMENT` headers
- Framework-agnostic endpoint protection with `X402Gate`
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

Create a `.env` file or set environment variables directly:

```env
NETWORK_TYPE=testnet
NETWORK=base
FACILITATOR_URL=https://x402.org
HTTPAYER_API_KEY=your-api-key
RPC_GATEWAY=https://your-gateway.example
PAY_TO_ADDRESS=0xYourReceivingAddress
```

---

## Usage

### HttPayerClient

A client for paying 402-gated endpoints using a hosted HTTPayer router.

```python
from httpayer import HttPayerClient

client = HttPayerClient()

response = client.request("GET", "http://provider.akash-palmito.org:30862/base-weather")

print(response.status_code)      # 200
print(response.headers)          # Includes X-PAYMENT-RESPONSE
print(response.json())           # Actual resource data
```

You can also manually call `pay_invoice(...)` if you already received a 402 response.

---

### X402Gate Decorator

A gate/decorator for protecting Web2 API routes using x402 payment authorization headers.

```python
from httpayer import X402Gate
from web3 import Web3

gate = X402Gate(
    pay_to="0xYourReceivingAddress",
    network="base-sepolia",
    asset_address="0xTokenAddress",
    max_amount=1000,  # atomic units (e.g. 0.001 USDC = 1000)
    asset_name="USD Coin",
    asset_version="2",
    facilitator_url="https://x402.org"
)

@gate.gate
def protected_resource(request_data):
    return {
        "status": 200,
        "headers": {},
        "body": {"message": "Access granted."}
    }

# Call using:
response = protected_resource({
    "headers": {"X-Payment": "<base64 header>"},
    "url": "http://your-api.com/protected"
})
```

---

## Examples

### test1.py – Programmatic Client Example

Runs multiple GET requests to x402-protected endpoints and prints response metadata.

```bash
python tests/test1.py
```

### test2.py – Flask Weather Server Demo

Starts a local API server (`/weather`) that requires a valid `X-PAYMENT` header:

```bash
python tests/test2.py
```

Send payment using HTTPayer:

```bash
http POST http://localhost:31157/httpayer \
  api_url=http://localhost:50358/weather \
  method=GET \
  x-api-key:your-api-key
```

---

## Development

### Build & Publish

```bash
uv venv
uv sync
python -m build
twine upload dist/*
```

### Optional Dev Tools

Install development extras:

```bash
pip install .[dev]
```

---

## Project Structure

```
httpayer/                 # Main package
├── __init__.py
├── client.py            # HttPayerClient class
├── gate.py              # X402Gate and helpers
tests/
├── test1.py             # Client-based demo
├── test2.py             # Flask server demo
.env.sample              # Environment config template
pyproject.toml           # Build config (PEP 621)
README.md
```

---

## License

MIT License. See [LICENSE](LICENSE) for full details.

---

## Author

Created by [Brandyn Hamilton](mailto:brandynham1120@gmail.com)
