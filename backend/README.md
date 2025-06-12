# HttPayer Backend

The HttPayer backend consists of two coordinated services:

1. **TypeScript (Node.js/Express)** – Implements an HTTP endpoint to auto-pay `402 Payment Required` requests using the x402 protocol and EIP-3009 signatures.
2. **Python (Flask)** – Provides Chainlink CCIP-powered treasury operations for cross-chain USDC transfers and gas estimation logic.

---

## 🔧 Requirements

- Node.js (>= 18.x)
- Python 3.10+
- Docker (optional for containerized deployment)
- `uv` or `pip` + `venv` for Python dependency management

---

## 📁 Project Structure

```
backend/
├── src/                  # TypeScript backend source
│   ├── server.ts         # Main x402 payment client API
│   ├── demoServer.ts     # Demo weather API protected by x402
│   └── types/            # custom TS types
├── dist/                 # Compiled JS from `tsc`
├── treasury/             # Python CCIP + treasury server
│   └── main.py
├── abi/                  # ERC-20 ABI for transfers
├── Dockerfile            # Node backend container spec
├── package.json          # Node dependencies
├── tsconfig.json         # TypeScript compiler config
├── requirements.txt      # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1. TypeScript Backend

#### Setup

```bash
cd backend
npm install
npx tsc    # or: npm run dev
```

#### Run Dev Server

```bash
npm run dev  # Uses ts-node
# OR for compiled JS:
node dist/server.js
```

### 2. Python Treasury Server

#### Setup

```bash
cd backend/treasury
uv venv   # or python -m venv .venv
uv pip install -r requirements.txt
```
> Ensure `.env` contains `PRIVATE_KEYS`, `ACCOUNT_ADDRESS`, etc.

#### Run Server

```bash
python treasury_server.py
```

---

## 🔄 Environment Variables

Create a `.env` file at project root:

```
PRIVATE_KEYS=0xabc...,0xdef...
ACCOUNT_ADDRESS=0xabc...
PORT=3000
```

---

## 🧪 Endpoints

### TypeScript (x402 Auto-Pay)

| Method | Endpoint       | Description                               |
|--------|----------------|-------------------------------------------|
| POST   | `/httpayer`    | Automatically pays `402` endpoint         |

Request JSON:
```json
{
  "api_url": "http://localhost:4021/weather",
  "method": "GET",
  "payload": {}
}
```

---

### Python (Treasury + CCIP)

| Method | Endpoint           | Description                            |
|--------|--------------------|----------------------------------------|
| GET    | `/balances`        | Fetch gas-aware balance info           |
| POST   | `/transfer`        | Trigger USDC CCIP transfer             |
| POST   | `/check_status`    | Check CCIP transfer status             |
| POST   | `/manage_liquidity`| Placeholder for liquidity logic        |

---

## 🐳 Docker (Optional)

Build container for `httpayer`:

```Dockerfile
# Dockerfile
FROM node:18
WORKDIR /app
COPY . .
RUN npm install && npm run build
CMD ["node", "dist/server.js"]
```

Build and run:

```bash
docker build -t httpayer-backend .
docker run -p 3000:3000 --env-file .env httpayer-backend
```

---

## 📌 Notes

- `demoServer.js` provides a sample protected endpoint (`/weather`) using x402.
- `httpayer` coordinates payment flows while `treasury_server.py` ensures liquidity is available via CCIP.
- You can extend the system by scheduling liquidity operations using `apscheduler`.

---

## 🧠 Credits

Built for composable Web2↔Web3 infrastructure using Chainlink CCIP, x402, and EIP-3009 token standards.