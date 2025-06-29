import { HttpayerRequest, HttpayerResponse } from './types';

/**
 * Unified HTTPayer client for managing 402 payments.
 */
export class HttpayerClient {
  private routerUrl: string;
  private apiKey: string;

  constructor(routerUrl?: string, apiKey?: string) {
    this.routerUrl = routerUrl || process.env.X402_ROUTER_URL || 'http://provider.boogle.cloud:31157/httpayer';
    this.apiKey = apiKey || process.env.HTTPAYER_API_KEY || 'chainlinkhack2025';

    if (!this.routerUrl || !this.apiKey) {
      throw new Error('Router URL and API Key must be configured!');
    }
  }

  /**
   * Pay a 402 payment (using the router service).
   */
  async payInvoice(apiUrl: string, apiMethod: string = 'GET', apiPayload: any = {}): Promise<HttpayerResponse> {
    return this.payViaRouter(apiUrl, apiMethod, apiPayload);
  }

  /**
   * Call the hosted /HTTPayer endpoint to handle payment and retry.
   */
  private async payViaRouter(apiUrl: string, apiMethod: string, apiPayload: any): Promise<HttpayerResponse> {
    if (!this.routerUrl) {
      throw new Error('Router URL not configured!');
    }

    const data: HttpayerRequest = {
      api_url: apiUrl,
      method: apiMethod,
      payload: apiPayload
    };

    const headers = {
      'Content-Type': 'application/json',
      'x-api-key': this.apiKey
    };

    try {
      const response = await fetch(this.routerUrl, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`HTTPayer request failed: ${response.status} ${response.statusText}`);
      }

      const responseData = await response.json();
      
      return {
        status: response.status,
        data: responseData,
        headers: Object.fromEntries(response.headers.entries())
      };
    } catch (error) {
      throw new Error(`HTTPayer request failed: ${error}`);
    }
  }

  /**
   * Automatically handle 402 Payment Required HTTP flow.
   */
  async request(method: string, url: string, options: any = {}): Promise<HttpayerResponse> {
    try {
      const response = await fetch(url, {
        method: method,
        ...options
      });

      if (response.status === 402) {
        const apiPayload = options.json || {};
        return this.payInvoice(url, method, apiPayload);
      }

      const responseData = await response.json();
      
      return {
        status: response.status,
        data: responseData,
        headers: Object.fromEntries(response.headers.entries())
      };
    } catch (error) {
      throw new Error(`Request failed: ${error}`);
    }
  }

  /**
   * Convenience method for GET requests.
   */
  async get(url: string, options: any = {}): Promise<HttpayerResponse> {
    return this.request('GET', url, options);
  }

  /**
   * Convenience method for POST requests.
   */
  async post(url: string, data: any = {}, options: any = {}): Promise<HttpayerResponse> {
    return this.request('POST', url, {
      ...options,
      json: data
    });
  }
} 