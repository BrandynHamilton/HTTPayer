# HTTPayer

**HTTPayer** is a server framework and SDK designed to automate stablecoin
payments using the x402 protocol. It enables Web2 applications to seamlessly
handle HTTP 402 Payment Required responses, facilitating automated payments via
CCIP-Terminal and USDC across multiple EVM chains.

---

## TODO

### Frontend Demo App (Next.js, TypeScript, Tailwind CSS)

- [x] Set up Next.js app with App Router and TypeScript
- [x] Configure Tailwind CSS and global styles
- [x] Add TanStack Query (react-query) for server state management
- [x] Add wagmi/viem for wallet connection and signature support
- [ ] Create `src/components/` directory for reusable UI components
- [ ] Implement `Header` component (wallet connect, title, client component)
- [ ] Implement `Dashboard` component (live balances, status, polling Treasury
      API)
- [ ] Implement `PaymentDemo` component (trigger/visualize x402 payment,
      interact with Orchestration API)
- [ ] Wire up TanStack Query for all backend data fetching (Treasury,
      Orchestration)
- [ ] Implement API integration per Backend Interaction Specifications in
      `frontend/ARCHITECTURE.md`
- [ ] Enforce type safety: define all API types in `src/types/`, use Zod schemas
      in `src/schemas/`
- [ ] Validate all environment variables at runtime (Zod)
- [ ] Implement robust error handling and user-friendly error states
- [ ] Add dark mode support via Tailwind (ensure `<html class="dark">`)
- [ ] Reference and follow all rules in `.cursor/rules/` (state management,
      styling, component structure, API interaction, wallet interaction, backend
      contract, code generation)
- [ ] Add README instructions for local dev, environment setup, and contributing
- [ ] Polish UI/UX for demo (loading states, empty states, responsive design)
- [ ] Prepare for Vercel deployment (env vars, config)
- [ ] (Optional) Add manual cross-chain transfer demo (Treasury API)
- [ ] (Optional) Add recent transactions/status list (Treasury API)

---

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
- `NEXT_PUBLIC_TREASURY_API_URL` — URL of the Treasury Service
- `NEXT_PUBLIC_HTTPAYER_API_KEY` — API key for backend authentication

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
