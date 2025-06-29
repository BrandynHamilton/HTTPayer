import express from 'express';
import { X402Gate } from '../src/gate';

// Example Express.js server using X402Gate
const app = express();
app.use(express.json());

// Configure X402Gate for protecting endpoints
const x402Gate = new X402Gate({
  payTo: '0x1234567890123456789012345678901234567890',
  network: 'base-sepolia',
  assetAddress: '0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8C',
  maxAmount: 1000000, // 1 USDC (6 decimals)
  assetName: 'USD Coin',
  assetVersion: '2',
  facilitatorUrl: 'http://provider.boogle.cloud:32179'
});

// Health check endpoint (no payment required)
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Protected endpoint using X402Gate
app.get('/protected-weather', x402Gate.gate((req, res) => {
  // This handler only runs if payment is verified
  res.json({
    weather: 'sunny',
    temperature: 25,
    location: 'Base Sepolia',
    timestamp: new Date().toISOString()
  });
}));

// Alternative: using middleware approach
app.use('/api', x402Gate.middleware());

app.get('/api/premium-data', (req, res) => {
  // This handler only runs if payment is verified (via middleware)
  res.json({
    data: 'premium content',
    accessLevel: 'paid',
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Server error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Express server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`🔒 Protected endpoint: http://localhost:${PORT}/protected-weather`);
  console.log(`🔒 API endpoint: http://localhost:${PORT}/api/premium-data`);
});

export { app, x402Gate }; 