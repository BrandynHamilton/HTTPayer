# HTTPayer

**HTTPayer** is a server framework and SDK designed to automate stablecoin
payments using the x402 protocol. It enables Web2 applications to seamlessly
handle HTTP 402 Payment Required responses, facilitating automated payments via
CCIP-Terminal and USDC across multiple EVM chains.

## TODO

### Immediate (Current Focus)

- [ ] Complete real API integration in `frontend/src/components/Dashboard.tsx`
      (live balances, CCIP status)

### Next (Critical for Script Alignment)

- [ ] Create `frontend/src/components/ChainlinkFunctionsStatus.tsx` (Client
      Component)
  - [ ] Prominent title: "Chainlink Functions Integration"
  - [ ] Concise, static description (from script)
  - [ ] Status indicator: "Status: In Development (Roadmap)"
  - [ ] Tailwind styling to match dashboard
- [ ] Integrate `ChainlinkFunctionsStatus.tsx` into `frontend/src/app/page.tsx`

### Subsequent (High Priority)

- [ ] Implement real API call in `frontend/src/components/PaymentDemo.tsx`
      (`POST /httpayer`)
- [ ] Ensure all data display in `Dashboard.tsx` and `PaymentDemo.tsx` matches
      backend API response structures
- [ ] Comprehensive testing of all frontend-backend interactions
- [ ] Finalize UI polish and ensure cross-browser/device responsiveness

### Final Step

- [ ] Record the demo video with the script as reference

---

# (Legacy/Meta)

- [x] Set up Next.js app with App Router and TypeScript
- [x] Configure Tailwind CSS and global styles
- [x] Add TanStack Query (react-query) for server state management
- [x] Add wagmi/viem for wallet connection and signature support
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
- [x] Develop/Deploy Chainlink Function for onchain usage
- [x] Publish HTTPayer SDK to PyPi
- [x] Develop HTTPayer Javascript/Typescript SDK
- [x] Develop HTTPayer UI/frontend
- [x] Create `src/components/` directory for reusable UI components
- [x] Add README instructions for local dev, environment setup, and contributing
- [x] Install Tailwind CSS
- [x] Config Vercel
- [x] Deploy HTTPayer frontend first iteration
- [ ] Vibe on!
- [ ] Polish UI/UX
- [ ] (Optional) Add manual cross-chain transfer demo (Treasury API)
- [ ] (Optional) Add recent transactions/status list (Treasury API)
- [ ] Publish HTTPayer SDK to NPM
- [ ] Config Turborepo
- [ ] Config GitHub Actions CI/CD

## Overview

HTTPayer consists of three main components:

### 1. Backend (Python + Node.js)

- **Node.js (Express/TypeScript)**\
  Main server to auto-pay `402 Payment Required` requests using the x402
  protocol and EIP-3009.

- **Python (Flask)**\
  Treasury server that integrates with Chainlink CCIP to perform cross-chain
  USDC transfers, manage gas and balances, and act as a payment facilitator.

- **Additional servers**
  - `facilitator.py`: Enables x402 usage on Avalanche Fuji.
  - `x402_server.py`: Provides demo 402-gated endpoints for Base Sepolia and
    Avalanche testnets.

### 2. Frontend

The HTTPayer frontend is a modern, type-safe demo app built with Next.js (App
Router), TypeScript, and Tailwind CSS. It provides a user interface for
interacting with the HTTPayer backend, demonstrating wallet connection, live
treasury status, and automated x402 payments for 402-gated APIs.

**Tech Stack:**

- Next.js 15 (App Router, React Server Components)
- TypeScript (strict mode)
- Tailwind CSS (utility-first styling)
- TanStack Query (`@tanstack/react-query`) for server state
- wagmi & viem for wallet connection and EIP-712/EIP-3009 signing
- Zod for runtime type validation

**Key Features:**

- **Wallet Connect:** Securely connect your EVM wallet (e.g., MetaMask) to sign
  messages for backend payment flows.
- **Live Dashboard:** Real-time polling of treasury balances and system status
  from the backend Treasury API.
- **Payment Demo:** Trigger and visualize a cross-chain x402 payment to a
  402-gated API, with full backend orchestration.
- **Type Safety:** All API types are defined in `src/types/` and validated at
  runtime with Zod schemas in `src/schemas/`.
- **Strict State Management:** Wallet state via wagmi, server state via TanStack
  Query, local UI state via React `useState`.
- **Dark Mode:** Fully supported via Tailwind's dark mode utilities.

**Architecture:**

- Follows the principles and directory structure in
  [`frontend/ARCHITECTURE.md`](frontend/ARCHITECTURE.md).
- All API interactions strictly conform to the Backend Interaction
  Specifications.
- Coding standards and patterns are enforced via rules in
  [`.cursor/rules/`](frontend/.cursor/rules/).

**Getting Started:**

```bash
cd frontend
pnpm install
cp .env.local.example .env.local # Fill in required env vars
pnpm dev
```

**Environment Variables:**

- `NEXT_PUBLIC_HTTPAYER_API_URL` — URL of the HTTPayer Orchestration Service
  (safe to expose)
- `NEXT_PUBLIC_TREASURY_API_URL` — URL of the Treasury Service (safe to expose)
- `HTTPAYER_API_KEY` — API key for backend authentication (**set this in your
  `.env.local`, never commit or share it, and only use it in server-side code.
  Do NOT use the `NEXT_PUBLIC_` prefix for secrets.**)

> ⚠️ **Security Note:** Only use un-prefixed environment variables (like
> `HTTPAYER_API_KEY`) for secrets, and access them in server-side code only. Any
> variable prefixed with `NEXT_PUBLIC_` will be exposed to the browser. See
> [Next.js docs](https://nextjs.org/docs/app/guides/environment-variables) for
> details.

**See Also:**

- [frontend/ARCHITECTURE.md](frontend/ARCHITECTURE.md) — Full architecture, data
  flow, and API contract
- [frontend/.cursor/rules/](frontend/.cursor/rules/) — Coding standards and best
  practices

### 3. Packages

- **Python SDK (`httpayer/`)**\
  Tools to:

  - Interact with the x402 protocol.
  - Protect Python API endpoints with 402-gating.
  - Send requests through the HTTPayer router server.
  - [PyPi Link](https://pypi.org/project/httpayer/)

- **TypeScript SDK (`httpayer-ts`)**\
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

This enables on-chain logic to securely interact with off-chain monetized APIs
through decentralized compute and automated cross-chain stablecoin payments.

### Deployments

- HTTPayer Account Address:
  [0x6f8550D4B3Af628d5eDe06131FE60A1d2A5DE2Ab](https://sepolia.basescan.org/address/0x6f8550D4B3Af628d5eDe06131FE60A1d2A5DE2Ab)
- HTTPayer Consumer Smart Contract:
  [0xa7ee479017AEcA4fa8844cAe216678F6989FF002](https://sepolia.basescan.org/address/0x338937Ab9453eA2381c49C8b64E2dD2830915793)
