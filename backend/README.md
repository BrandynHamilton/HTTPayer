# HTTPayer Backend

The HTTPayer backend consists of two coordinated services:

1. **TypeScript (Node.js/Express)** – Implements an HTTP endpoint to auto-pay
   `402 Payment Required` requests using the x402 protocol and EIP-3009
   signatures.
2. **Python (Flask)** – Provides Chainlink CCIP-powered treasury operations for
   cross-chain USDC transfers and gas estimation logic.

Additionally, there are several other servers necessary for demos and
multi-chain functionality:

1. **Facilitator Server (Flask)** - Enables x402 usage on Avalanche and other
   EVM chains via dedicated facilitator instances.
2. **x402 Demo Server (Flask)** - An endpoint for HTTPayer tests and demos which
   can handle both Base Sepolia and Avalanche Fuji x402 processes.

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
|   ├── test1.py          # W.I.P. Python payment client API
|   ├── test2.py          # Calls 402 endpoint w/ HTTPayer
├── dist/                 # Compiled JS from `tsc`
├── treasury/             # Python CCIP + treasury server
│   ├── main.py
|   └── cli.py
├── facilitator/          # Facilitator server
|   └── facilitator.py
├── httpayer_core/        # HTTPayer core Python scripts
├── abi/                  # ERC-20 ABI
├── Dockerfile            # Backend container spec
├── package.json          # Node dependencies
├── tsconfig.json         # TypeScript compiler config
├── pyproject.toml        # Python dependencies
└── README.md
packages/
├── python/
│   ├── httpayer/         # Python SDK (published to PyPI)
│   └── README.md
├── typescript/
│   ├── httpayer-ts/      # TypeScript SDK
│   └── README.md
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

## SDKs

- **Python SDK:** Located in `packages/python/httpayer/`, published to PyPI. See
  `packages/python/README.md` for usage and examples.
- **TypeScript SDK:** Located in `packages/typescript/httpayer-ts/`. See
  `packages/typescript/httpayer-ts/README.md` for usage and examples.

---

## Tests

The `tests` directory provides examples of how to use the HTTPayer API.

- test2.py demonstrates how to use the API w/ the `requests` library

## Deployments

- HTTPayer Server: http://provider.boogle.cloud:31157/httpayer
- Treasury Server: http://provider.boogle.cloud:32279/treasury
- Facilitator Server: http://provider.boogle.cloud:32179
- Demo Server: http://provider.akash-palmito.org:30862

## Notes

- `src/server.ts` coordinates payment flows while `treasury/main.py` ensures
  liquidity is available via CCIP.
- `facilitator/facilitator.py` was created because the default facilitator
  server for the x402 protocol only supports base sepolia. The facilitator we
  deploy here supports avalanche fuji and other EVM chains as needed.
- The SDKs in `packages/` enable integration with both Python and
  TypeScript/JavaScript applications. The Python SDK is published to PyPI for
  easy installation.
- Ongoing work: Chainlink Function integration to enable smart contracts to
  trigger HTTPayer payments.

---

## Credits

Built for composable Web2↔Web3 infrastructure using Chainlink CCIP, x402, and
EIP-3009 token standards.
