# HTTPayer Backend

The HTTPayer backend consists of two coordinated services:

1. **TypeScript (Node.js/Express)** – Implements an HTTP endpoint to auto-pay `402 Payment Required` requests using the x402 protocol and EIP-3009 signatures.
2. **Python (Flask)** – Provides Chainlink CCIP-powered treasury operations for cross-chain USDC transfers and gas estimation logic.

Additionally, there are several other servers necessary for demos and multi-chain funcionality:

1. **Facilitator Server (Flask)** - Enables x402 usage on Avalanche.
2. **x402 Demo Server (Flask)** - An endpoint for HTTPayer tests and demos which can handle both Base Sepolia and Avalanche Fuji x402 processes.

A Python SDK was also created to interact with both the x402 protocol and HTTPayer server. It enables 402 gating of endpoints via a decorator class, as well as a client class to handle 402 status codes through the HTTPayer server.

The backend is currently deployed to Akash; links can be found below.

---

## Requirements

- Node.js (>= 18.x)
- Python 3.10+
- Docker (optional for containerized deployment)
- `uv` or `pip` + `venv` for Python dependency management

---

## Project Structure

```
backend/
├── src/                  # TypeScript backend source
│   ├── server.ts         # Main x402 payment client API
│   ├── demoServer.ts     # Demo weather API protected by x402
│   └── types/            # Custom TS types
├── tests/
|   |── test1.py          # W.I.P. Python payment client API
|   |── test2.py          # Calls 402 endpoint w/ HTTPayer
|   |── test3.py          # Calls 402 endpoint w/ SDK
|   └── test4.py          # Tests HTTPayer 402 gate class
├── dist/                 # Compiled JS from `tsc`
├── treasury/             # Python CCIP + treasury server
│   |── main.py
|   └── cli.py
├── facilitator/          # Facilitator server
|   |── facilitator.py
├── httpayer/             # HTTPayer Python SDK
├── abi/                  # ERC-20 ABI
├── Dockerfile            # Backend container spec
├── package.json          # Node dependencies
├── tsconfig.json         # TypeScript compiler config
├── pyproject.toml        # Python dependencies
└── README.md
```

---

## Getting Started

### 1. TypeScript Backend

#### Setup

```bash
cd backend
npm install
npx tsc    # or: npm run dev
```

#### Run Server

```bash
npm run dev  # Uses ts-node
# OR for compiled JS:
node dist/server.js
```

### 2. Python Treasury Server

#### Setup

```bash
uv venv   # or python -m venv .venv
uv sync
```

> Ensure `.env` contains `PRIVATE_KEYS`, `ACCOUNT_ADDRESS`, etc.

#### Run Server

```bash
uv run python treasury/main.py
```

### 3. Python Facilitator Server

#### Setup

```bash
uv venv   # or python -m venv .venv
uv sync
```

#### Run Server

```bash
uv run python facilitator/facilitator.py
```

### 4. Python Demo Server

#### Setup

```bash
uv venv   # or python -m venv .venv
uv sync
```

#### Run Server

```bash
uv run python x402_servers/x402_server.py
```

---

## Environment Variables

Create a `.env` file at project root:

```
PRIVATE_KEYS=abc...,def...
ACCOUNT_ADDRESS=0xabc...
ALCHEMY_API_KEY= abc123...
ETHERSCAN_API_KEY= xyz789...
```

For SDK usage only, simply copy .env.sample to .env (all that is needed is HTTPAYER_API_KEY)

---

## Endpoints

### HTTPayer Server

| Method | Endpoint    | Description                       |
| ------ | ----------- | --------------------------------- |
| GET    | `/health`   | API health endpoint               |
| POST   | `/httpayer` | Automatically pays `402` endpoint |

Request JSON:

```json
{
  "api_url": "http://provider.akash-palmito.org:30862/avalanche-weather",
  "method": "GET",
  "payload": {}
}
```

#### Authentication required

Include your API key in the request headers using the x-api-key header:

```http
x-api-key: YOUR_HTTPAYER_API_KEY
```

---

### Treasury Server

| Method | Endpoint                     | Description                  |
| ------ | ---------------------------- | ---------------------------- |
| GET    | `/treasury/health`           | API health endpoint          |
| GET    | `/treasury/balances`         | Fetch gas-aware balance info |
| POST   | `/treasury/burn_rate`        | Burn rate stats by chain     |
| POST   | `/treasury/transfer`         | Trigger USDC CCIP transfer   |
| POST   | `/treasury/check_status`     | Check CCIP transfer status   |
| POST   | `/treasury/manage_liquidity` | Manages liquidity via CCIP   |

### Facilitator Server

| Method | Endpoint                 | Description                                          |
| ------ | ------------------------ | ---------------------------------------------------- |
| GET    | `/facilitator/health`    | API health endpoint                                  |
| GET    | `/facilitator/supported` | Fetch supported network info                         |
| POST   | `/facilitator/verify`    | Verify a payment with a supported scheme and network |
| POST   | `/facilitator/settle`    | Settle a payment with a supported scheme and network |

### Demo Server

| Method | Endpoint             | Description            |
| ------ | -------------------- | ---------------------- |
| GET    | `health`             | API health endpoint    |
| GET    | `/avalanche-weather` | Avalanche 402 endpoint |
| GET    | `/base-weather`      | Base 402 endpoint      |

---

## Python SDK

- HTTPayerClient(router_url=None, api_key=None)
  Passing router_url and api_key are optional. By default the class checks .env for X402_ROUTER_URL and HTTPAYER_API_KEY.

Example usage:

```python

from httpayer import HttPayerClient

url="http://provider.akash-palmito.org:30862/avalanche-weather" # 402 protected endpoint

client = HttPayerClient() # Initiates client object
response = client.request("GET", url) # Sends API call to HTTPayer server

```

- X402Gate(
  pay_to # address to receive payment
  network # viem network id of preferred blockchain
  asset_address # token address to receive
  max_amount # raw amount of token to receive
  asset_name # onchain resolved name
  asset_version # onchain resolved version
  facilitator_url # URL for facilitator server
  )

Example usage:

```python

from httpayer import X402Gate
import os
from dotenv import load_dotenv
from ccip_terminal.metadata import USDC_MAP

load_dotenv()

ERC20_ABI_PATH = 'abi/erc20.json'

with open(ERC20_ABI_PATH, 'r') as f:
  ERC20_ABI = f.read()

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org")
GATEWAY = os.getenv("GATEWAY", "https://api.avax-test.network/ext/bc/C/rpc")
NETWORK = 'avalanche' # resolves to avalanche-fuji

w3 = Web3(Web3.HTTPProvider(GATEWAY))

token_address = USDC_MAP.get(NETWORK)

token_contract = w3.to_checksum_address(token_address)
token = w3.eth.contract(address=token_contract, abi=ERC20_ABI)
name_onchain    = token.functions.name().call()
version_onchain = token.functions.version().call()

extra = {"name": name_onchain, "version": version_onchain}

gate = X402Gate(
    pay_to=PAY_TO_ADDRESS,
    network=network_id,
    asset_address=token_address,
    max_amount=1000, # raw amount, actually is 0.001 USDC
    asset_name=extra["name"],
    asset_version=extra["version"],
    facilitator_url=FACILITATOR_URL
)

```

## Tests

The `tests` directory provides examples of how to use the HTTPayer API and Python SDK.

- test2.py demonstrates how to use the API w/ the `requests` library
- test3.py demonstates how to use the API w/ the Python SDK
- test4.py demonstrates how to gate an API endpoint using the Python SDK

## Deployments

- HTTPayer Server: http://provider.boogle.cloud:31157/httpayer
- Treasury Server: http://provider.boogle.cloud:32279/treasury
- Facilitator Server: http://provider.boogle.cloud:32179
- Demo Server: http://provider.akash-palmito.org:30862

## Notes

- `src/server.ts` coordinates payment flows while `treasury/main.py` ensures liquidity is available via CCIP.

- `facilitator/facilitator.py` was created because the default facilitator server for the x402 protocol only supports base sepolia. The facilitator we deploy here supports avalanche fuji.

---

## Credits

Built for composable Web2↔Web3 infrastructure using Chainlink CCIP, x402, and EIP-3009 token standards.
