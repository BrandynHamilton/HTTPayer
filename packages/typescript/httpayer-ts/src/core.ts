import { ethers } from 'ethers';
import crypto from 'crypto';
import { 
  PaymentPayload, 
  Authorization, 
  Domain, 
  EIP712Types, 
  TransferWithAuthorizationMessage 
} from './types';

/**
 * Decode a base64-encoded X-PAYMENT header back into its structured JSON form.
 */
export function decodeXPayment(header: string): PaymentPayload {
  try {
    const decodedBytes = Buffer.from(header, 'base64');
    const decodedJson = JSON.parse(decodedBytes.toString());
    
    if (typeof decodedJson !== 'object' || decodedJson === null) {
      throw new Error('Decoded X-PAYMENT is not a JSON object');
    }
    
    return decodedJson as PaymentPayload;
  } catch (error) {
    throw new Error(`Invalid X-PAYMENT header: ${error}`);
  }
}

/**
 * Build EIP-3009 authorization object.
 */
export function makeAuthorization(
  fromAddr: string, 
  toAddr: string, 
  value: string, 
  validSecs: number = 60
): Authorization {
  const now = Math.floor(Date.now() / 1000);
  const nonce = '0x' + crypto.randomBytes(32).toString('hex');
  
  return {
    from: fromAddr,
    to: toAddr,
    value: value,
    validAfter: now.toString(),
    validBefore: (now + validSecs).toString(),
    nonce: nonce,
  };
}

/**
 * EIP-712 sign with ethers.js.
 */
export async function signExact(
  privateKey: string, 
  domain: Domain, 
  types: EIP712Types, 
  primaryType: string, 
  message: TransferWithAuthorizationMessage
): Promise<string> {
  const wallet = new ethers.Wallet(privateKey);
  
  const domainData = {
    name: domain.name,
    version: domain.version,
    chainId: domain.chainId,
    verifyingContract: domain.verifyingContract,
  };

  const signature = await wallet.signTypedData(
    domainData,
    types as unknown as Record<string, ethers.TypedDataField[]>,
    message
  );

  return signature;
}

/**
 * Encode settle header for response.
 */
export function encodeSettleHeader(settleJson: any): string {
  const compact = JSON.stringify(settleJson);
  return Buffer.from(compact).toString('base64');
}

/**
 * Create payment payload for x402 protocol.
 */
export function createPaymentPayload(
  signature: string,
  authorization: Authorization,
  network: string
): PaymentPayload {
  return {
    x402Version: 1,
    scheme: 'exact',
    network: network,
    payload: {
      signature: signature,
      authorization: authorization,
    },
  };
}

/**
 * Encode payment payload to base64 header.
 */
export function encodePaymentHeader(payload: PaymentPayload): string {
  const compact = JSON.stringify(payload);
  return Buffer.from(compact).toString('base64');
}

/**
 * Create EIP-712 domain for USDC transfers.
 */
export function createDomain(
  assetName: string,
  assetVersion: string,
  chainId: number,
  assetAddress: string
): Domain {
  return {
    name: assetName,
    version: assetVersion,
    chainId: chainId,
    verifyingContract: assetAddress,
  };
}

/**
 * Create EIP-712 types for TransferWithAuthorization.
 */
export function createEIP712Types(): EIP712Types {
  return {
    TransferWithAuthorization: [
      { name: 'from', type: 'address' },
      { name: 'to', type: 'address' },
      { name: 'value', type: 'uint256' },
      { name: 'validAfter', type: 'uint256' },
      { name: 'validBefore', type: 'uint256' },
      { name: 'nonce', type: 'bytes32' },
    ],
  };
} 