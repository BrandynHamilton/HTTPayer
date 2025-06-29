// Main exports for the HTTPayer TypeScript SDK
import { HttpayerClient } from './client';
import { X402Gate } from './gate';

export { HttpayerClient } from './client';
export { X402Gate } from './gate';
export * from './core';
export * from './types';

// Default export for convenience
export default {
  HttpayerClient,
  X402Gate,
}; 