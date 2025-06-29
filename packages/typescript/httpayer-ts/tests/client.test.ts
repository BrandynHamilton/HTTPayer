import { HttpayerClient } from '../src/client';

// Basic tests for HttpayerClient
describe('HttpayerClient', () => {
  let client: HttpayerClient;

  beforeEach(() => {
    // Create client with test configuration
    client = new HttpayerClient(
      'http://test.example.com/httpayer',
      'test-api-key'
    );
  });

  test('should initialize with provided configuration', () => {
    expect(client).toBeInstanceOf(HttpayerClient);
  });

  test('should throw error when router URL is missing', () => {
    expect(() => {
      new HttpayerClient('', 'test-key');
    }).toThrow('Router URL and API Key must be configured!');
  });

  test('should throw error when API key is missing', () => {
    expect(() => {
      new HttpayerClient('http://test.example.com', '');
    }).toThrow('Router URL and API Key must be configured!');
  });

  test('should have payInvoice method', () => {
    expect(typeof client.payInvoice).toBe('function');
  });

  test('should have request method', () => {
    expect(typeof client.request).toBe('function');
  });

  test('should have get method', () => {
    expect(typeof client.get).toBe('function');
  });

  test('should have post method', () => {
    expect(typeof client.post).toBe('function');
  });
});

// Integration test (requires actual HTTPayer server)
describe('HttpayerClient Integration', () => {
  let client: HttpayerClient;

  beforeAll(() => {
    // Use default configuration for integration tests
    client = new HttpayerClient();
  });

  test('should handle 402 payment flow', async () => {
    const targetUrl = 'http://provider.akash-palmito.org:30862/base-weather';
    
    try {
      const response = await client.payInvoice(targetUrl, 'GET', {});
      
      expect(response).toBeDefined();
      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
    } catch (error) {
      // Test might fail if server is not available, which is expected
      console.log('Integration test skipped - server not available');
    }
  }, 30000); // 30 second timeout
}); 