# HTTPayer

**Automated, cross-chain stablecoin payments for APIs, agents, and smart
contracts — powered by x402, Chainlink CCIP, and EIP-3009.**

## What is HTTPayer?

HTTPayer is the missing link for monetizing APIs and digital services with
crypto. It's a server framework and SDK suite that brings the long-awaited "HTTP
402 Payment Required" standard to life for the Web3 era, letting any API, app,
or smart contract require and automate stablecoin payments (USDC) across chains.

Built on x402, Chainlink CCIP, and EIP-3009, HTTPayer makes crypto payments as
simple as traditional API keys:

- **No wallet UX required:** Account abstraction and automated payment flows
  mean users and agents can pay for APIs without manual wallet steps.
- **Multi-chain by default:** Accept payments from multiple EVM chains (Base
  Sepolia, Avalanche Fuji, and more), with liquidity managed by a treasury
  service using Chainlink CCIP.
- **For devs, agents, and contracts:** Simple Python/TypeScript SDKs enable
  instant paywalling, while Chainlink Functions let smart contracts consume paid
  APIs and receive valuable data (weather, credit scores, etc.).

## Why HTTPayer?

HTTPayer transforms stablecoin payments into a drop-in middleware layer—just
like Stripe, but composable, cross-chain, and designed for the future of Web3:

- **Monetize APIs in minutes:** Drop-in Python/TypeScript SDKs for instant
  paywalling, no deep crypto infrastructure needed.
- **Automate everything:** Handles 402 responses, payment signing, and retries
  automatically—enabling seamless access for users, agents, and smart contracts.
- **Cross-chain liquidity:** Treasury service manages USDC across EVM chains
  using Chainlink CCIP, unlocking new DeFi primitives and composable finance.
- **Smart contract integration:** Chainlink Functions let contracts trigger
  off-chain paid API calls, bridging on-chain logic with real-world data.
- **Built for the future:** Designed for DeFi, tokenization, AI agents, and
  agentic automation.

**Real impact:**

- **For Developers:** Instant API monetization without complex crypto
  infrastructure
- **For Users & AI Agents:** Seamless, automated access to paid APIs and
  services
- **For Smart Contracts:** Secure, on-chain interaction with monetized off-chain
  APIs
- **For the Web3 Ecosystem:** A real, interoperable way to do Stripe-style
  payments with crypto—composable, cross-chain, and future-proof

## Example Use Cases

**🔗 API Monetization**\
Instantly add stablecoin paywalls to any API—weather data, financial feeds, AI
models, or premium content.

**🤖 AI Agent Payments**\
Let autonomous bots and AI agents pay for data and services on demand, enabling
truly autonomous workflows.

**📊 Smart Contract Data Access**\
Enable on-chain logic to securely access paid, off-chain APIs—credit scores,
real-world events, IoT data.

**🌉 Cross-chain DeFi**\
Move and manage USDC liquidity across EVM chains for composable finance
applications and multi-chain protocols.

## Quick Start

### Try the Python SDK

```bash
pip install httpayer
```

```python
from httpayer import HttPayerClient
client = HttPayerClient()
response = client.request("GET", "http://provider.akash-palmito.org:30862/base-weather")
print(response.json())  # Automatic payment + data access
```

### Try the TypeScript SDK

```bash
npm install httpayer-ts
```

```typescript
import { HttpayerClient } from "httpayer-ts";
const client = new HttpayerClient();
const response = await client.get("http://provider.akash-palmito.org:30862/base-weather");
console.log(response.data);  # Seamless 402 handling
```

### Protect Your APIs

```python
# Python - Flask/FastAPI
from httpayer import X402Gate

@gate.gate
def premium_endpoint():
    return {"data": "premium content"}
```

```typescript
// TypeScript - Express
import { X402Gate } from "httpayer-ts";
app.get(
  "/premium",
  x402Gate.gate((req, res) => {
    res.json({ data: "premium content" });
  }),
);
```

## Technical Architecture

HTTPayer is a modular, multi-language system designed for production use across
multiple chains and environments.

### Core Components

**🔧 Backend Services**

- **TypeScript Node.js Server:** Orchestrates x402 payment flows, EIP-3009
  signing, and 402 retry logic. Exposes `/httpayer` endpoint for automated
  payment and resource fetching.
- **Python Treasury Server:** Manages cross-chain USDC balances, gas estimation,
  and liquidity using Chainlink CCIP. Handles transfers, burn rates, and
  liquidity management.
- **Facilitator Server:** Chain-specific payment verification and settlement for
  multiple EVM chains.
- **Demo Server:** Real 402-gated endpoints for testing and demonstration.

**📦 Developer SDKs**

- **Python SDK (`httpayer`):** Published to PyPI. Includes `HttPayerClient` for
  automatic payment handling and `X402Gate` decorator for protecting
  Flask/FastAPI endpoints.
- **TypeScript SDK (`httpayer-ts`):** Published to npm. Features
  `HttpayerClient` for 402 handling in Node.js/browser and `X402Gate` middleware
  for Express.js, plus EIP-712/EIP-3009 signing utilities.

**⛓️ Smart Contract Integration**

- **Chainlink Functions:** Allows smart contracts to trigger HTTPayer payment
  flows and consume paid APIs on-chain.

**🌐 Supported Networks**

- Base Sepolia (testnet)
- Avalanche Fuji (testnet)
- Ethereum Sepolia (testnet)
- Easily extensible to mainnets and other EVM chains

**🚀 Deployment** All services are containerized and deployed to production. See
backend documentation for live endpoints and setup instructions.

## Learn More

**📋 Product & Strategy**

- [`PRD.md`](./PRD.md) — Product requirements, user stories, success metrics,
  and strategic roadmap
- [`TODO.md`](./TODO.md) — Current development priorities and project roadmap

**🔧 Technical Documentation**

- [`backend/README.md`](./backend/README.md) — Backend setup, environment
  variables, API endpoints, and deployment
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — System architecture, data flows, and
  integration patterns

**📚 SDK Documentation**

- [`packages/python/README.md`](./packages/python/README.md) — Python SDK usage,
  examples, and API reference
- [`packages/typescript/httpayer-ts/README.md`](./packages/typescript/httpayer-ts/README.md)
  — TypeScript SDK usage, examples, and API reference

**🤝 Contributing**

- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — Setup instructions, coding standards,
  and contribution guidelines

## License

MIT
