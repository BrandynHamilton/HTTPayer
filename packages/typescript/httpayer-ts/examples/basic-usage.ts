import { HttpayerClient } from '../src/client';

// Example usage of the HTTPayer TypeScript SDK
async function basicExample() {
  console.log('--- HTTPayer TypeScript SDK Basic Example ---');

  // Initialize the client with default settings
  // Uses HTTPAYER_API_KEY=chainlinkhack2025 by default
  const client = new HttpayerClient();

  // Example API endpoint that requires payment
  const targetApiUrl = 'http://provider.akash-palmito.org:30862/base-weather';

  try {
    console.log(`Making request to: ${targetApiUrl}`);
    
    // This will automatically handle 402 payments
    const response = await client.payInvoice(
      targetApiUrl,
      'GET',
      {}
    );

    console.log('✅ Payment successful!');
    console.log('Response status:', response.status);
    console.log('Response data:', response.data);
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

// Example using the request method
async function requestExample() {
  console.log('\n--- Using request() method ---');
  
  const client = new HttpayerClient();
  const targetApiUrl = 'http://provider.akash-palmito.org:30862/avalanche-weather';

  try {
    console.log(`Making request to: ${targetApiUrl}`);
    
    // This will automatically handle 402 payments
    const response = await client.request('GET', targetApiUrl);
    
    console.log('✅ Request successful!');
    console.log('Response status:', response.status);
    console.log('Response data:', response.data);
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

// Example using convenience methods
async function convenienceExample() {
  console.log('\n--- Using convenience methods ---');
  
  const client = new HttpayerClient();
  const targetApiUrl = 'http://provider.akash-palmito.org:30862/base-weather';

  try {
    console.log(`Making GET request to: ${targetApiUrl}`);
    
    // Using the get() convenience method
    const response = await client.get(targetApiUrl);
    
    console.log('✅ GET request successful!');
    console.log('Response status:', response.status);
    console.log('Response data:', response.data);
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

// Run all examples
async function runExamples() {
  await basicExample();
  await requestExample();
  await convenienceExample();
}

// Only run if this file is executed directly
if (require.main === module) {
  runExamples().catch(console.error);
}

export { basicExample, requestExample, convenienceExample }; 