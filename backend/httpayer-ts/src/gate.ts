import { 
  X402GateConfig, 
  PaymentRequirements,
  TransferWithAuthorizationMessage 
} from './types';
import { 
  decodeXPayment, 
  createDomain, 
  createEIP712Types 
} from './core';

/**
 * X402Gate decorator for protecting endpoints with x402 payments.
 * This is a TypeScript equivalent of the Python X402Gate class.
 */
export class X402Gate {
  private payTo: string;
  private network: string;
  private assetAddress: string;
  private maxAmount: number;
  private assetName: string;
  private assetVersion: string;
  private verifyUrl: string;
  private settleUrl: string;

  constructor(config: X402GateConfig) {
    this.payTo = config.payTo.toLowerCase();
    this.network = config.network;
    this.assetAddress = config.assetAddress.toLowerCase();
    this.maxAmount = config.maxAmount;
    this.assetName = config.assetName;
    this.assetVersion = config.assetVersion;
    
    const base = config.facilitatorUrl.replace(/\/$/, '');
    this.verifyUrl = `${base}/facilitator/verify`;
    this.settleUrl = `${base}/facilitator/settle`;
  }

  /**
   * Verify payment with facilitator.
   */
  private async verify(header: string, requirements: PaymentRequirements): Promise<any> {
    const payload = decodeXPayment(header);
    
    const response = await fetch(this.verifyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        x402Version: 1,
        paymentPayload: payload,
        paymentRequirements: requirements,
      }),
    });

    if (!response.ok) {
      throw new Error(`Verification failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Settle payment with facilitator.
   */
  private async settle(header: string, requirements: PaymentRequirements): Promise<any> {
    const payload = decodeXPayment(header);
    
    const response = await fetch(this.settleUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        x402Version: 1,
        paymentPayload: payload,
        paymentRequirements: requirements,
      }),
    });

    if (!response.ok) {
      throw new Error(`Settlement failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create payment requirements object.
   */
  private createPaymentRequirements(baseUrl: string): PaymentRequirements {
    return {
      scheme: 'exact',
      network: this.network.toLowerCase(),
      maxAmountRequired: this.maxAmount.toString(),
      resource: baseUrl,
      description: '',
      mimeType: '',
      payTo: this.payTo,
      maxTimeoutSeconds: 60,
      asset: this.assetAddress,
      extra: {
        name: this.assetName,
        version: this.assetVersion,
      },
    };
  }

  /**
   * Gate decorator for Express.js routes.
   * Usage: app.get('/protected', x402Gate.gate((req, res) => { ... }))
   */
  gate(handler: (req: any, res: any) => any) {
    return async (req: any, res: any) => {
      const baseUrl = `${req.protocol}://${req.get('host')}${req.originalUrl}`;
      const requirements = this.createPaymentRequirements(baseUrl);

      // Check for X-Payment header
      const paymentHeader = req.headers['x-payment'];
      if (!paymentHeader) {
        return res.status(402).json({
          x402Version: 1,
          error: 'X-PAYMENT header is required',
          accepts: [requirements],
        });
      }

      // Verify payment
      try {
        await this.verify(paymentHeader, requirements);
      } catch (error) {
        return res.status(402).json({
          x402Version: 1,
          error: `verification failed: ${error}`,
          accepts: [requirements],
        });
      }

      // Execute protected handler
      const result = await handler(req, res);

      // Settle payment
      try {
        const settleJson = await this.settle(paymentHeader, requirements);
        const settleHeader = Buffer.from(JSON.stringify(settleJson)).toString('base64');
        res.set('X-PAYMENT-RESPONSE', settleHeader);
      } catch (error) {
        return res.status(402).json({
          x402Version: 1,
          error: `settlement failed: ${error}`,
          accepts: [requirements],
        });
      }

      return result;
    };
  }

  /**
   * Middleware for Express.js.
   * Usage: app.use(x402Gate.middleware())
   */
  middleware() {
    return async (req: any, res: any, next: any) => {
      const baseUrl = `${req.protocol}://${req.get('host')}${req.originalUrl}`;
      const requirements = this.createPaymentRequirements(baseUrl);

      const paymentHeader = req.headers['x-payment'];
      if (!paymentHeader) {
        return res.status(402).json({
          x402Version: 1,
          error: 'X-PAYMENT header is required',
          accepts: [requirements],
        });
      }

      try {
        await this.verify(paymentHeader, requirements);
        req.x402Requirements = requirements;
        req.x402Header = paymentHeader;
        next();
      } catch (error) {
        return res.status(402).json({
          x402Version: 1,
          error: `verification failed: ${error}`,
          accepts: [requirements],
        });
      }
    };
  }
} 