export interface PaymentRequirements {
  scheme: string;
  network: string;
  maxAmountRequired: string;
  resource: string;
  description: string;
  mimeType: string;
  payTo: string;
  maxTimeoutSeconds: number;
  asset: string;
  extra: {
    name: string;
    version: string;
  };
}

export interface Authorization {
  from: string;
  to: string;
  value: string;
  validAfter: string;
  validBefore: string;
  nonce: string;
}

export interface PaymentPayload {
  x402Version: number;
  scheme: string;
  network: string;
  payload: {
    signature: string;
    authorization: Authorization;
  };
}

export interface HttpayerRequest {
  api_url: string;
  method: string;
  payload: any;
}

export interface HttpayerResponse {
  status: number;
  data: any;
  headers?: Record<string, string>;
}

export interface X402GateConfig {
  payTo: string;
  network: string;
  assetAddress: string;
  maxAmount: number;
  assetName: string;
  assetVersion: string;
  facilitatorUrl: string;
}

export interface Domain {
  name: string;
  version: string;
  chainId: number;
  verifyingContract: string;
}

export interface EIP712Types {
  TransferWithAuthorization: Array<{
    name: string;
    type: string;
  }>;
}

export interface TransferWithAuthorizationMessage {
  from: string;
  to: string;
  value: number;
  validAfter: number;
  validBefore: number;
  nonce: string;
} 