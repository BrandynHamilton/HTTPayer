import express from "express";
import dotenv from "dotenv";
import bodyParser from "body-parser";
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { wrapFetchWithPayment, decodeXPaymentResponse } from "x402-fetch";
import { fetch as undiciFetch, RequestInit as UndiciRequestInit } from "undici";
import {
  baseSepolia,
  avalancheFuji,
  sepolia,
  Chain,
} from "viem/chains";

const CHAIN_MAP: Record<string, Chain> = {
  "base-sepolia": baseSepolia,
  "avalanche-fuji": avalancheFuji,
  "sepolia": sepolia,
};

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
app.use(bodyParser.json());

// Load first PRIVATE_KEY from comma-separated PRIVATE_KEYS
let rawKeys = process.env.PRIVATE_KEYS;
if (!rawKeys) throw new Error("Missing PRIVATE_KEYS in .env");

let rawPk = rawKeys.split(",")[0].trim();
if (!rawPk.startsWith("0x")) rawPk = "0x" + rawPk;

const PRIVATE_KEY = rawPk as `0x${string}`;

// Main endpoint
app.post("/httpayer", async (req, res) => {
  const { api_url, method, payload } = req.body;

  const requestInit: UndiciRequestInit = {
    method,
    headers: { "Content-Type": "application/json" },
    body: method !== "GET" ? JSON.stringify(payload) : undefined,
  };

  try {
    // First attempt (unauthenticated)
    const initialResp = await undiciFetch(api_url, requestInit as any);

    if (initialResp.status !== 402) {
      const body = await initialResp.text();
      res.status(initialResp.status).send(body);
      return;
    }

    // Extract JSON from 402 body to get `accepts` list
    const errorJson = await initialResp.json() as { accepts?: any[] };
    const accepts = errorJson.accepts || [];
    const exactScheme = accepts.find((x: any) => x.scheme === "exact");

    if (!exactScheme || !exactScheme.network) {
      res.status(400).json({ error: "Missing 'exact' scheme or network in paymentRequirements" });
      return;
    }

    const network = exactScheme.network;
    if (!CHAIN_MAP[network]) {
      res.status(400).json({ error: `Unsupported network: ${network}` });
      return;
    }

    const chain = CHAIN_MAP[network];

    // ——— Dynamically create wallet client for that chain ———
    const account = privateKeyToAccount(PRIVATE_KEY);
    const walletClient = createWalletClient({
      account,
      transport: http(),
      chain,
    });

    // ——— Use this client to wrap fetch ———
    const fetchWithPayment = wrapFetchWithPayment(
      undiciFetch as unknown as typeof globalThis.fetch,
      walletClient
    );

    // Retry with payment
    const paidResp = await fetchWithPayment(api_url, requestInit as any);

    // Optional: Handle callback
    const xHeader = paidResp.headers.get("x-payment-response");
    if (xHeader) {
      const paymentInfo = decodeXPaymentResponse(xHeader);
      if (paymentInfo.callbackUrl) {
        const callbackResp = await undiciFetch(paymentInfo.callbackUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tx_hash: paymentInfo.txHash }),
        });

        if (!callbackResp.ok) {
          res.status(500).json({ error: "Callback failed" });
          return;
        }
      }
    }

    const body = await paidResp.text();
    res.status(paidResp.status).send(body);
    return;
  } catch (err: any) {
    console.error("Server error:", err);
    res.status(500).json({ error: err.message || "Unknown error" });
    return;
  }
});

app.listen(PORT, () => {
  console.log(`httpayer server running on port ${PORT}`);
});
