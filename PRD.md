# Product Requirements Document

**HTTPayer**

# Pitch

### 1. **Overview – What is HTTPayer**

- **HTTPayer** is a server framework and SDK designed to automate stablecoin
  payments using the x402 protocol.
- It makes the **x402 protocol** easy to use — for developers, for apps, and
  even for smart contracts.
- Powered by **Chainlink CCIP**, **Chainlink Functions**, and stablecoins like
  USDC.

### 2. **What is x402 / 402?**

- HTTP 402 means “Payment Required” — a standard response code never fully
  adopted... until now.
- The **x402 protocol** lets you protect any API behind a crypto payment wall.
- But until HTTPayer, it required a wallet, signatures, and custom routing logic
  — hard to build and scale.

### 3. **Why HTTPayer Matters**

- HTTPayer brings x402 to life:
  - Makes it **usable by any dev** with simple Python/TypeScript SDKs.
  - Enables **account abstraction** — no wallet needed to pay.
  - Adds **multi-chain liquidity**, powered by Chainlink CCIP.
  - Automatically retries requests after payment.
- It turns stablecoin payments into a **drop-in middleware layer** — just like
  Stripe or API keys.

### 4. **Architecture Overview**

#### Backend

- **TypeScript Node Server**: Handles x402 retries, EIP-3009 signing, payment
  coordination.
- **Python Treasury (Flask)**: Handles cross-chain USDC transfers, burn
  tracking, gas management using **Chainlink CCIP**.
- **Facilitator Server**: Chain-specific payment verification and settlement
  logic (e.g., Base, Avalanche).
- **Demo Server**: Real 402-protected endpoints for testing.

#### SDKs

- **Python SDK**: Add gate decorator to any route in Flask, FastAPI, etc.
- **TypeScript SDK**: Auto-handle 402 responses in Express or frontend apps.
  Handles EIP-712 + retry flows.

#### Smart Contracts

- HTTPayer also includes a **Chainlink Functions smart contract**.
- This lets smart contracts:
  - Trigger 402-gated API calls via HTTPayer
  - Make stablecoin payments off-chain
  - Receive gated data (weather, credit scores, etc.)
- This closes the loop — now smart contracts can "pay-to-consume" any real-world
  API, securely.

### 5. **What This Unlocks**

- **For Devs**: Monetize APIs in minutes — no crypto infra or wallet UX needed.
- **For Users**: Access paid APIs and services using accounts — no wallet
  required.
- **For Agents**: Enable autonomous actors to consume paid services using
  HTTPayer.
- **For Smart Contracts**: Securely interact with monetized APIs via Chainlink
  Functions.
- **For the Ecosystem**: A real way to do Stripe-style payments with crypto —
  interoperable, composable, and chain-agnostic.

### 6. **Hackathon Alignment**

- **Onchain Finance**: End-to-end USDC flows, composable API monetization.
- **Cross-Chain Solutions**: Chainlink CCIP treasury rebalancing across Base +
  Avalanche.
- **Avalanche Track**: Live contracts + facilitator server deployed on Avalanche
  Fuji.
- **Chainlink Core Prize**: Uses Chainlink **Functions** and **CCIP** to make
  actual state changes based on off-chain logic.

### 7. **Closing**

- HTTPayer turns x402 into real infrastructure — no wallet needed, no hacky
  scripts.
- It’s how smart contracts, agents, and APIs will **talk and transact**.

# Submission Questions

### The problem it solves

The current landscape of onchain payments and monetization is fragmented,
complex, and often inaccessible to both developers and end users. Traditional
payment systems are ill-suited for microtransactions, cross-chain value
transfer, and the programmable finance required by modern DeFi, tokenization,
and AI-driven applications. Developers face high integration barriers, limited
interoperability, and a lack of secure, automated solutions for monetizing APIs
and digital services.

HTTPayer solves these challenges by providing a unified, secure, and
developer-friendly platform for onchain payments and monetization. Leveraging
the x402 protocol, EIP-3009 signatures, and Chainlink CCIP, HTTPayer enables
seamless, automated, and cross-chain payments for API calls and digital
services. The current deployment targets are the Base Sepolia and Avalanche Fuji
(C-Chain) testnets, ensuring robust support for multi-chain development and
testing. This unlocks new possibilities for pay-per-use business models,
decentralized applications, and AI agent interactions—without relying on legacy
payment processors or centralized intermediaries.

By abstracting away the complexity of crypto payments, HTTPayer empowers
developers to easily integrate stablecoin (USDC) microtransactions across
multiple EVM chains, opening the door to a new era of global, permissionless,
and composable onchain finance. The platform is designed to be extensible,
supporting future innovations in DeFi, tokenized assets, and cross-chain
interoperability, and positioning itself as a foundational layer for the next
generation of Web3 and AI-powered economies.

### Challenges We Ran Into

During development, we encountered several notable challenges that shaped the
evolution of HTTPayer's architecture and implementation:

**EIP-3009 Messaging in Python**\
Our initial approach was to implement EIP-3009 messaging in Python, aiming for a
unified backend. However, we found that Python's ecosystem lacked robust
libraries and tooling for EIP-3009 and related Ethereum signature standards.
This led to recurring issues with message encoding and signature verification,
which risked the reliability of payment flows. To address this, we rewrote the
primary payment orchestration server in TypeScript, leveraging the mature
Ethereum tooling available in the Node.js ecosystem. This decision significantly
improved our ability to handle x402 protocol flows and ensured compatibility
with EIP-712 and EIP-3009 standards.

**Initial Deployment Issues**\
Deploying the early versions of HTTPayer surfaced several operational
challenges, including environment inconsistencies and dependency conflicts
between the TypeScript and Python services. These issues occasionally led to
service downtime and complicated the deployment pipeline. By consolidating
critical payment logic in TypeScript and containerizing all services, we
achieved a more stable and reproducible deployment process, as documented in our
architecture and backend guides.

**Avalanche Integration**\
Integrating Avalanche Fuji as a supported chain was a key milestone. While the
process was smoother than anticipated, it required the development of a custom
facilitator service. The default x402 facilitator was designed for Base Sepolia
and did not support Avalanche's network parameters or consensus specifics. By
implementing a dedicated facilitator server for Avalanche, we ensured seamless
multi-chain support and future extensibility for additional EVM-compatible
networks.

### Onchain Finance

**How does this project fit within the track?**

HTTPayer is purpose-built for the Onchain Finance track, directly addressing the
core requirements for Chainlink hackathon eligibility and competitiveness. It
establishes a direct, peer-to-peer payment system for digital services, with all
transactions settled entirely on-chain using stablecoins (USDC) and the x402
protocol. By integrating Chainlink CCIP, HTTPayer enables secure, automated, and
cross-chain USDC transfers, making it possible to build new DeFi protocols,
cross-chain lending/borrowing, and tokenized asset flows.

The backend Treasury service leverages Chainlink CCIP to manage on-chain funds,
burn rates, and liquidity across multiple EVM chains, ensuring composability and
extensibility for DeFi and tokenization use cases. Ongoing work on Chainlink
Functions integration will allow smart contracts to trigger HTTPayer payment
flows, further expanding the project's onchain automation and composability.
HTTPayer also provides SDKs (Python and TypeScript) for easy integration and
extensibility, allowing other developers to build on top of the platform. The
architecture is designed to support future integration with additional Chainlink
services, such as Automation and Data Feeds, further enhancing its capabilities
and alignment with the track's bonus criteria.

By abstracting away the complexity of onchain payments and liquidity, HTTPayer
empowers developers to build the next generation of DeFi and tokenization
applications, making it a strong and extensible fit for the Onchain Finance
track.

### Cross-Chain Solutions

**How does this project fit within the track?**

HTTPayer is purpose-built for a multi-chain world, directly addressing the
Cross-Chain Solutions track. At its core, HTTPayer uses Chainlink CCIP to enable
seamless, secure, and automated USDC transfers across multiple EVM chains (e.g.,
Base Sepolia, Avalanche Fuji). This allows users and protocols to move liquidity
and value between chains without friction, unlocking new cross-chain DeFi
primitives such as:

- Cross-chain DEXs and lending/borrowing protocols
- Multi-chain payment flows for API services and digital goods
- Tokenization and transfer of RWAs and game assets across chains

The backend Treasury service, powered by Chainlink CCIP, manages on-chain funds,
burn rates, and liquidity across chains, ensuring that assets can be
programmatically moved and utilized wherever needed. Ongoing work on Chainlink
Functions integration will allow smart contracts to trigger HTTPayer payment
flows, further enhancing cross-chain composability and automation.

This architecture not only meets but exceeds the track's requirements by:

- Using Chainlink CCIP to make onchain state changes and enable true
  interoperability
- Providing SDKs (Python and TypeScript) for easy integration into any
  cross-chain dApp or protocol
- Laying the foundation for future expansion into additional Chainlink services
  (e.g., Automation, Data Feeds) for bonus points

By abstracting away the complexity of cross-chain payments and liquidity,
HTTPayer empowers developers to build the next generation of cross-chain DeFi,
gaming, and tokenization applications—making it a strong fit for the Cross-Chain
Solutions track.

### Avalanche Track

**How does this project fit within the track?**

HTTPayer is fully deployed and operational on Avalanche Fuji (C-Chain testnet),
meeting the core requirement for the Avalanche track. The project leverages
Avalanche's high throughput, low fees, and EVM compatibility to deliver
seamless, onchain payments and cross-chain DeFi infrastructure. By deploying a
dedicated Facilitator server and smart contracts on Avalanche C-Chain, HTTPayer
enables high-frequency microtransactions, automated agent interactions, and
composable DeFi and tokenization use cases—all natively on Avalanche.

The architecture is designed for extensibility, allowing for future deployment
on custom Avalanche L1s and integration with additional Avalanche-native
features. HTTPayer's modular SDKs (Python and TypeScript) make it easy for other
developers to build on Avalanche, whether for DeFi, NFTs, gaming, or
infrastructure tooling. The project also integrates Chainlink CCIP and is
actively working toward supporting Chainlink Functions and VRF, further
enhancing its capabilities for onchain finance and cross-chain interoperability.

By abstracting away the complexity of onchain payments and liquidity, HTTPayer
empowers the Avalanche ecosystem to build the next generation of decentralized
applications. The project is not only technically robust and innovative, but
also positioned for real-world adoption and future growth within the Avalanche
and broader Web3 community.

### Technical Architecture Overview

HTTPayer is built as a modular, multi-language system comprising several key
components. The current deployment targets are Base Sepolia and Avalanche Fuji
(C-Chain) testnets:

- **TypeScript Service (Node.js/Express):** The main payment client API
  (`backend/src/server.ts`) that intercepts HTTP 402 responses and orchestrates
  the payment process.
- **Python Treasury Service (Flask):** Manages on-chain funds, burn rates,
  liquidity, and Chainlink CCIP-powered cross-chain transfers
  (`backend/treasury/main.py`).
- **Facilitator Service (Flask):** Handles the core x402 protocol logic for
  payment verification and on-chain settlement
  (`backend/facilitator/facilitator.py`), supporting multiple chains with
  dedicated facilitator instances as needed.
- **Python SDK:** Located in `packages/python/httpayer/`, provides client and
  decorator classes for integrating x402 payment logic into Python applications,
  enabling 402-gated endpoints and programmatic payment flows. The Python SDK is
  published to PyPI.
- **TypeScript SDK:** Located in `packages/typescript/httpayer-ts/`, a
  comprehensive SDK for automatic 402 handling, multi-chain support, EIP-712
  signing, and Express.js integration.
- **Chainlink Function:** Ongoing work to enable smart contracts to trigger
  HTTPayer payments via Chainlink Functions.

This architecture ensures a flexible, scalable, and secure system for automated
crypto payments on Base Sepolia and Avalanche Fuji (C-Chain) testnets, with a
clear path to mainnet and additional chain support.
