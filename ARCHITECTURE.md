# HTTPayer Backend Architecture

## 1. Overview

The HTTPayer backend is a modular, multi-language system designed to automate
and manage stablecoin payments (USDC) using the x402 protocol. It enables
seamless HTTP 402 Payment Required flows for Web2/Web3 applications, supporting
multi-chain operations and composable integration via SDKs.

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
    payment and access.

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
    settlement, supports multiple chains.
- **Demo Server (Flask):**
  - `x402_servers/x402_server.py`: Example endpoints for x402 payment flows.
- **Python SDK:**
  - `httpayer/`: Client and decorator classes for integrating x402 payment logic
    into Python apps.
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
- **SDK:**
  - `client.py`: `HttPayerClient` for programmatic payment flows.
  - `gate.py`: `X402Gate` decorator for 402-gated endpoints.
  - `core.py`: EIP-712/EIP-3009 signing, payment header encoding/decoding.
- **ABI:**
  - `abi/erc20.json`: ERC20 ABI for on-chain contract interaction.

---

## 3. Key Flows

### A. Payment Flow

1. **User/API Client** requests a resource.
2. **Service** responds with HTTP 402 and payment requirements.
3. **HTTPayer** (TS or Python SDK) presents payment details, connects wallet,
   and signs transaction (EIP-712/EIP-3009).
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
  Avalanche, etc.).
- **SDKs:** Python SDK (`httpayer/`), planned JS/TS SDK
  (`src/types/x402-fetch.d.ts`).
- **Demo/Test:** Example servers and test scripts for integration and
  onboarding.

---

## 4. Directory and File Reference

- **TypeScript:**
  - `src/server.ts`, `src/demoServer.ts`, `src/types/`
- **Python Treasury:**
  - `treasury/main.py`, `treasury/cli.py`, `treasury/burn_rate.py`,
    `treasury/liquidity.py`
- **Facilitator:**
  - `facilitator/facilitator.py`
- **SDK:**
  - `httpayer/client.py`, `httpayer/gate.py`, `httpayer/core.py`
- **Demo/Test:**
  - `x402_servers/x402_server.py`, `tests/`, `treasury/tests/`
- **ABI:**
  - `abi/erc20.json`
- **Docker:**
  - `Dockerfile`: Multi-stage build for Node and Python services.

---

## 5. Deployment & Operations

- **Dockerized:** Multi-stage Dockerfile runs all services in one container for
  demo/testing.
- **Environment:** `.env` for secrets and API keys.
- **Endpoints:**
  - `/httpayer`, `/treasury/*`, `/facilitator/*`, `/avalanche-weather`,
    `/base-weather`, etc.
- **Deployed to:** Akash (see backend/README.md for URLs).

---

## 6. Extending & Integrating

- **Add new chains:** Update facilitator and treasury logic.
- **Integrate SDK:** Use Python SDK for 402-gated endpoints or payment
  automation.
- **Frontend:** Planned minimalist UI for human-in-the-loop payments.

---

## 7. References

- See `backend/README.md` for setup, usage, and endpoint details.
- See `PRD.md` for product requirements and roadmap.
