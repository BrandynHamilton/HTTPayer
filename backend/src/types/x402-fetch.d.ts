declare module "x402-fetch" {
  export function wrapFetchWithPayment(fetch: typeof globalThis.fetch, walletClient: any): typeof fetch;
  export function decodeXPaymentResponse(header: string): any;
}
