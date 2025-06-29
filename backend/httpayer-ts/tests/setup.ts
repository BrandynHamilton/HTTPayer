// Jest setup file

// Global test configuration
beforeAll(() => {
  // Set test environment variables
  process.env.HTTPAYER_API_KEY = 'chainlinkhack2025';
  process.env.X402_ROUTER_URL = 'http://provider.boogle.cloud:31157/httpayer';
});

afterAll(() => {
  // Clean up
  delete process.env.HTTPAYER_API_KEY;
  delete process.env.X402_ROUTER_URL;
}); 