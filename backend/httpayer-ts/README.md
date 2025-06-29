# HTTPayer TypeScript SDK

TypeScript/JavaScript SDK for HTTPayer - automated stablecoin payments using x402 protocol.

## Installation

```bash
npm install httpayer-ts
```

## Quick Start

```typescript
import { HttpayerClient } from 'httpayer-ts';

// Initialize client with default settings
const client = new HttpayerClient();

// Make a request that automatically handles 402 payments
const response = await client.payInvoice(
  'http://example.com/api/protected-resource',
  'GET',
  {}
);

console.log('Response:', response.data);
```

## Environment Variables

Set these environment variables or pass them to the constructor:

- `HTTPAYER_API_KEY`: Your HTTPayer API key (default: 'chainlinkhack2025')
- `X402_ROUTER_URL`: HTTPayer router URL (default: 'http://provider.boogle.cloud:31157/httpayer')

## API Reference

### HttpayerClient

Main client for handling 402 payments.

#### Constructor

```typescript
new HttpayerClient(routerUrl?: string, apiKey?: string)
```

#### Methods

- `payInvoice(apiUrl: string, method: string, payload: any)`: Pay a 402 payment
- `request(method: string, url: string, options?: any)`: Make a request with automatic 402 handling
- `get(url: string, options?: any)`: GET request with automatic 402 handling
- `post(url: string, data: any, options?: any)`: POST request with automatic 402 handling

### X402Gate

Decorator for protecting Express.js endpoints with x402 payments.

```typescript
import { X402Gate } from 'httpayer-ts';
import express from 'express';

const app = express();

const x402Gate = new X402Gate({
  payTo: '0x1234...',
  network: 'base-sepolia',
  assetAddress: '0xA0b8...',
  maxAmount: 1000000,
  assetName: 'USD Coin',
  assetVersion: '2',
  facilitatorUrl: 'http://facilitator.example.com'
});

// Protect an endpoint
app.get('/protected', x402Gate.gate((req, res) => {
  res.json({ data: 'protected content' });
}));

// Or use as middleware
app.use('/api', x402Gate.middleware());
```

## Examples

See the `examples/` directory for complete usage examples.

## Development

```bash
# Install dependencies
npm install

# Build the SDK
npm run build

# Run tests
npm test

# Run example
npm run example
```

## License

MIT 