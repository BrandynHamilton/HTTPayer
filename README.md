# HTTPayer

**HTTPayer** is a server framework and SDK designed to automate stablecoin
payments using the x402 protocol. It enables Web2 applications to seamlessly
handle HTTP 402 Payment Required responses, facilitating automated payments via
CCIP-Terminal and USDC across multiple EVM chains.

---

## TODO

- [x] Develop payer server (src/server.ts)
- [x] Develop treasury server (treasury/main.py)
- [x] Develop facilitator server (facilitator/facilitator.py)
- [x] Develop demo servers (x402_servers/x402.py)
- [x] Develop HTTPayer Python SDK
- [x] Deploy HTTPayer servers to cloud
  - [x] payer server
  - [x] treasury server
  - [x] Avalanche facilitator server
  - [x] demo servers
- [x] Develop HTTPayer UI/frontend
- [ ] Deploy HTTPayer frontend
- [x] Develop/Deploy Chainlink Function for onchain usage
- [x] Publish HTTPayer SDK to PyPi
- [x] Develop HTTPayer Javascript/Typescript SDK
- [ ] Publish HTTPayer SDK to NPM
- [ ] Config Turborepo
- [ ] Config Vercel
- [ ] Config GitHub Actions CI/CD

---

## Overview

HTTPayer consists of three main components:

### 1. Backend (Python + Node.js)

- **Node.js (Express/TypeScript)**  
  Main server to auto-pay `402 Payment Required` requests using the x402 protocol and EIP-3009.

- **Python (Flask)**  
  Treasury server that integrates with Chainlink CCIP to perform cross-chain USDC transfers, manage gas and balances, and act as a payment facilitator.

- **Additional servers**
  - `facilitator.py`: Enables x402 usage on Avalanche Fuji.
  - `x402_server.py`: Provides demo 402-gated endpoints for Base Sepolia and Avalanche testnets.

### 2. Frontend

### 3. Packages

- **Python SDK (`httpayer/`)**  
  Tools to:

  - Interact with the x402 protocol.
  - Protect Python API endpoints with 402-gating.
  - Send requests through the HTTPayer router server.
  - [PyPi Link](https://pypi.org/project/httpayer/)

- **TypeScript SDK (`httpayer-ts`)**  
  Enables:
  - Automatic 402 handling and retries.
  - Protection of Express routes.
  - EIP-712 signing and payment logic in frontends or backend Node.js apps.

### 4. Smart Contract Integration (Chainlink Functions)

HTTPayer integrates with **Chainlink Functions** to allow smart contracts to:

- Programmatically trigger x402 payments via HTTPayer backend.
- Consume valuable gated APIs such as:
  - Credit scores
  - Financial attestations
  - Weather data
  - Bank balance proofs

This enables on-chain logic to securely interact with off-chain monetized APIs through decentralized compute and automated cross-chain stablecoin payments.

---

## Deployments

- HTTPayer Account Address: [0x6f8550D4B3Af628d5eDe06131FE60A1d2A5DE2Ab](https://sepolia.basescan.org/address/0x6f8550D4B3Af628d5eDe06131FE60A1d2A5DE2Ab)
- HTTPayer Consumer Smart Contract: [0xa7ee479017AEcA4fa8844cAe216678F6989FF002](https://sepolia.basescan.org/address/0x338937Ab9453eA2381c49C8b64E2dD2830915793)
