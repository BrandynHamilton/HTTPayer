# HTTPayer TypeScript SDK

A comprehensive TypeScript/JavaScript SDK for HTTPayer - enabling automated stablecoin payments using the x402 protocol. This SDK provides seamless integration for handling HTTP 402 Payment Required responses in Web2 applications.

## Features

- 🔄 **Automatic 402 Handling**: Automatically intercepts and handles HTTP 402 Payment Required responses
- 💳 **Multi-chain Support**: Works with Base Sepolia, Avalanche Fuji, and other EVM chains
- 🛡️ **Express.js Integration**: Built-in decorators and middleware for protecting endpoints
- 🔐 **EIP-712 Signing**: Secure payment signing using EIP-712 and EIP-3009 standards
- 📦 **TypeScript First**: Full TypeScript support with comprehensive type definitions
- ⚡ **Lightweight**: Minimal dependencies, uses native Node.js fetch

## Installation

```bash
npm install httpayer-ts
```

## Quick Start

### Basic Usage

```typescript
import { HttpayerClient } from 'httpayer-ts';

// Initialize client with default settings
const client = new HttpayerClient();

// Make a request that automatically handles 402 payments
const response = await client.payInvoice(
  'http://provider.akash-palmito.org:30862/base-weather',
  'GET',
  {}
);

console.log('Response:', response.data);
// Output: { temp: 75, weather: 'sunny' }
```

### Using Convenience Methods

```typescript
import { HttpayerClient } from 'httpayer-ts';

const client = new HttpayerClient();

// GET request with automatic 402 handling
const getResponse = await client.get('http://example.com/api/protected-resource');

// POST request with automatic 402 handling
const postResponse = await client.post('http://example.com/api/protected-resource', {
  data: 'some data'
});
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

| Method | Description |
|--------|-------------|
| `payInvoice(apiUrl: string, method: string, payload: any)` | Pay a 402 payment directly |
| `request(method: string, url: string, options?: any)` | Make a request with automatic 402 handling |
| `get(url: string, options?: any)` | GET request with automatic 402 handling |
| `post(url: string, data: any, options?: any)` | POST request with automatic 402 handling |

### X402Gate

Decorator for protecting Express.js endpoints with x402 payments.

```typescript
import { X402Gate } from 'httpayer-ts';
import express from 'express';

const app = express();

const x402Gate = new X402Gate({
  payTo: '0x58a4Cae5e8dDA3a5614972F34951e482a29ef0f0',
  network: 'base-sepolia',
  assetAddress: '0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8C',
  maxAmount: 1000000, // 1 USDC (6 decimals)
  assetName: 'USD Coin',
  assetVersion: '2',
  facilitatorUrl: 'http://provider.boogle.cloud:32179'
});

// Protect an endpoint using decorator
app.get('/protected-weather', x402Gate.gate((req, res) => {
  res.json({
    weather: 'sunny',
    temperature: 25,
    location: 'Base Sepolia'
  });
}));

// Or use as middleware for multiple endpoints
app.use('/api', x402Gate.middleware());

app.get('/api/premium-data', (req, res) => {
  res.json({
    data: 'premium content',
    accessLevel: 'paid'
  });
});
```

### Core Functions

The SDK also exports core functions for advanced usage:

```typescript
import { 
  decodeXPayment, 
  makeAuthorization, 
  signExact, 
  createPaymentPayload,
  encodePaymentHeader 
} from 'httpayer-ts';

// Decode x402 payment headers
const payload = decodeXPayment(headerString);

// Create authorization object
const auth = makeAuthorization(fromAddr, toAddr, value, validSeconds);

// Sign payment with EIP-712
const signature = await signExact(privateKey, domain, types, primaryType, message);

// Create and encode payment payload
const paymentPayload = createPaymentPayload(signature, auth, network);
const header = encodePaymentHeader(paymentPayload);
```

## Examples

### Complete Express.js Server

```typescript
import express from 'express';
import { X402Gate } from 'httpayer-ts';

const app = express();
app.use(express.json());

// Configure X402Gate
const x402Gate = new X402Gate({
  payTo: '0x1234567890123456789012345678901234567890',
  network: 'base-sepolia',
  assetAddress: '0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8C',
  maxAmount: 1000000,
  assetName: 'USD Coin',
  assetVersion: '2',
  facilitatorUrl: 'http://provider.boogle.cloud:32179'
});

// Health check (no payment required)
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Protected endpoint
app.get('/protected-weather', x402Gate.gate((req, res) => {
  res.json({
    weather: 'sunny',
    temperature: 25,
    location: 'Base Sepolia',
    timestamp: new Date().toISOString()
  });
}));

// API routes with middleware
app.use('/api', x402Gate.middleware());

app.get('/api/premium-data', (req, res) => {
  res.json({
    data: 'premium content',
    accessLevel: 'paid',
    timestamp: new Date().toISOString()
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
```

### Advanced Client Usage

```typescript
import { HttpayerClient } from 'httpayer-ts';

const client = new HttpayerClient(
  'http://custom-httpayer-server.com/httpayer',
  'your-api-key'
);

// Handle multiple requests
async function fetchMultipleResources() {
  const endpoints = [
    'http://provider.akash-palmito.org:30862/base-weather',
    'http://provider.akash-palmito.org:30862/avalanche-weather'
  ];

  const responses = await Promise.all(
    endpoints.map(url => client.get(url))
  );

  responses.forEach((response, index) => {
    console.log(`Response ${index + 1}:`, response.data);
  });
}

// Error handling
async function safeRequest() {
  try {
    const response = await client.payInvoice(
      'http://example.com/api/protected-resource',
      'GET',
      {}
    );
    return response.data;
  } catch (error) {
    console.error('Payment failed:', error.message);
    // Handle error appropriately
    throw error;
  }
}
```

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

# Development mode (watch for changes)
npm run dev

# Lint code
npm run lint
```

## Testing

The SDK includes comprehensive tests:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npx jest tests/client.test.ts
```

## Supported Networks

- **Base Sepolia**: Testnet for Base protocol
- **Avalanche Fuji**: Testnet for Avalanche
- **Ethereum Sepolia**: General Ethereum testnet

## Error Handling

The SDK provides detailed error messages for common scenarios:

- Missing API key or router URL
- Network connectivity issues
- Invalid payment requirements
- Authentication failures
- Payment verification failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions, please visit the [HTTPayer repository](https://github.com/BrandynHamilton/HTTPayer). 