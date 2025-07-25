# HTTPayer Backend Architecture

## 1. Overview

The HTTPayer backend is a modular, multi-language system designed to automate
and manage stablecoin payments (USDC) using the x402 protocol. It enables
seamless HTTP 402 Payment Required flows for Web2/Web3 applications, supporting
multi-chain operations and composable integration via SDKs. The project now
includes a `packages/` directory containing both Python and TypeScript SDKs,
with the Python SDK published to PyPI and the TypeScript SDK published to npm. A
modern frontend is implemented using Next.js and Tailwind CSS, providing a user
interface for wallet connection, payment demos, and live treasury status.

---

## 2. C4 Model Breakdown

### A. Context

- **Actors:**
  - End Users / AI Agents
  - Service Providers (API/content hosts)
  - Blockchain Networks (EVM chains)
  - Wallet Providers (e.g., MetaMask)
- **System Boundary:**
  - HTTPayer mediates between users, providers, and blockchains, automating
    payment and access. The frontend provides a human-in-the-loop interface for
    interacting with the backend and SDKs.

### B. Containers

- **TypeScript Service (Node.js/Express):**
  - `src/server.ts`: Main x402 payment client API, intercepts HTTP 402,
    orchestrates payment.
  - `src/demoServer.ts`: Demo API protected by x402 for testing.
  - `dist/`: Compiled JS output.
- **Python Treasury Service (Flask):**
  - `treasury/main.py`: Manages on-chain funds, burn rate, liquidity, and
    CCIP-powered cross-chain transfers.
  - `treasury/cli.py`: CLI for treasury operations and wallet management.
- **Facilitator Service (Flask):**
  - `facilitator/facilitator.py`: Protocol logic for payment verification and
    settlement. **A dedicated facilitator instance is deployed for each
    supported chain (e.g., Avalanche Fuji requires its own facilitator with
    chain-specific configuration, as the default x402 facilitator only supports
    Base Sepolia).**
- **Demo Server (Flask):**
  - `x402_servers/x402_server.py`: Example endpoints for x402 payment flows.
- **Frontend (Next.js/TypeScript/Tailwind):**
  - Provides a modern UI for wallet connection, payment demos, and live treasury
    status. Deployed to Vercel.
- **SDKs (in `packages/`):**
  - **Python SDK:** `packages/python/httpayer/` – Client and decorator classes
    for integrating x402 payment logic into Python apps. Published to PyPI.
  - **TypeScript SDK:** `packages/typescript/httpayer-ts/` – Comprehensive SDK
    for Node.js/Express and frontend integration. Published to npm.
- **Tests:**
  - `tests/`, `treasury/tests/`: Usage examples and integration tests.

### C. Components

- **TypeScript:**
  - `server.ts`, `demoServer.ts`, `types/x402-fetch.d.ts`: HTTP endpoints,
    payment orchestration, type definitions.
- **Python Treasury:**
  - `main.py`: Flask app, routes for treasury, balances, burn rate, liquidity,
    transfer, and status.
  - `burn_rate.py`, `liquidity.py`: Burn rate analytics, liquidity management.
- **Facilitator:**
  - `facilitator.py`: `/verify` and `/settle` endpoints for payment proof and
    on-chain settlement.
- **SDKs:**
  - Python: `packages/python/httpayer/` (see also `packages/python/README.md`)
  - TypeScript: `packages/typescript/httpayer-ts/` (see also
    `packages/typescript/httpayer-ts/README.md`)
- **Frontend:**
  - `frontend/`: Next.js app, UI components, dashboard, payment demo, Tailwind
    CSS styling. See also `frontend/ARCHITECTURE.md` for frontend-specific
    details.
- **ABI:**
  - `abi/erc20.json`: ERC20 ABI for on-chain contract interaction.

---

## 3. Key Flows

### A. Payment Flow

1. **User/API Client** requests a resource (via SDK or frontend UI).
2. **Service** responds with HTTP 402 and payment requirements.
3. **HTTPayer** (TS or Python SDK, or via frontend) presents payment details,
   connects wallet, and signs transaction (EIP-712/EIP-3009).
4. **Facilitator** verifies and settles payment on-chain.
5. **Treasury** tracks balances, burn rates, and liquidity.
6. **Access** is granted upon payment confirmation.

### B. Treasury Management

- **Burn Rate:** `treasury/burn_rate.py` computes rolling spend and runway.
- **Liquidity:** `treasury/liquidity.py` manages cross-chain balances and
  rebalancing.
- **Transfers:** `/treasury/transfer` endpoint and CLI for USDC CCIP transfers.

### C. Extensibility

- **Multi-chain:** Facilitator and treasury support multiple EVM chains (Base,
  Avalanche, etc.). **Adding a new chain may require deploying a new facilitator
  instance with chain-specific logic and configuration.**
- **SDKs:** Python SDK (`packages/python/httpayer/`), TypeScript SDK
  (`packages/typescript/httpayer-ts/`).
- **Demo/Test:** Example servers and test scripts for integration and
  onboarding.
- **Chainlink Function:** In development — will enable on-chain invocation of
  HTTPayer payment flows via Chainlink Functions, allowing smart contracts to
  trigger off-chain paid API calls.
- **Frontend:** Modern UI for human-in-the-loop payments, wallet connection, and
  live status.

---

## 4. Directory and File Reference

- **TypeScript:**
  - `src/server.ts`, `src/demoServer.ts`, `src/types/`
- **Python Treasury:**
  - `treasury/main.py`, `treasury/cli.py`, `treasury/burn_rate.py`,
    `treasury/liquidity.py`
- **Facilitator:**
  - `facilitator/facilitator.py`
- **SDKs:**
  - Python: `packages/python/httpayer/`, `packages/python/README.md`
  - TypeScript: `packages/typescript/httpayer-ts/`,
    `packages/typescript/httpayer-ts/README.md`
- **Frontend:**
  - `frontend/`, `frontend/ARCHITECTURE.md`
- **Demo/Test:**
  - `x402_servers/x402_server.py`, `tests/`, `treasury/tests/`
- **ABI:**
  - `abi/erc20.json`
- **Docker:**
  - `Dockerfile`: Multi-stage build for Node and Python services.

---

## 5. Deployment & Operations

- **Dockerized:** Multi-stage Dockerfile runs all services (Node, Python, and
  frontend) in one container for demo/testing.
- **Frontend:** Deployed to Vercel for production/staging.
- **Environment:** `.env` for secrets and API keys.
- **Endpoints:**
  - `/httpayer`, `/treasury/*`, `/facilitator/*`, `/avalanche-weather`,
    `/base-weather`, frontend routes, etc.
- **Deployed to:** Akash (backend), Vercel (frontend). See backend/README.md for
  backend URLs.

---

## 6. Extending & Integrating

- **Add new chains:** Update facilitator and treasury logic. **For some chains,
  this means deploying a new facilitator instance with chain-specific
  configuration (e.g., Avalanche Fuji).**
- **Integrate SDK:** Use Python SDK (published to PyPI) for 402-gated endpoints
  or payment automation. Use TypeScript SDK (published to npm) for
  Node.js/Express or frontend integration.
- **Frontend:** Use the Next.js app for wallet connection, payment demos, and
  live dashboard. See `frontend/ARCHITECTURE.md` for details.
- **Chainlink Function:** In development — will enable smart contracts to
  trigger HTTPayer payments via Chainlink Functions.

---

## 7. References

- See `README.md` for a high-level project overview and value proposition.
- See `backend/README.md` for setup, usage, and endpoint details.
- See `PRD.md` for product requirements and roadmap.
- See `frontend/ARCHITECTURE.md` for frontend architecture and data flow.
- See `packages/python/README.md` and
  `packages/typescript/httpayer-ts/README.md` for SDK usage.
