// ---------------------------------------------------------------------------
// httpayer server – GET/POST proxy that handles 402 “exact” payments
// ---------------------------------------------------------------------------

import { createRequire } from "module";
const require = createRequire(import.meta.url);
(globalThis as any).require = require;

import express from "express";
import dotenv from "dotenv";
import bodyParser from "body-parser";
import cors from "cors";
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { decodeXPaymentResponse, wrapFetchWithPayment } from "x402-fetch";
import { fetch as undiciFetch, RequestInit as UndiciRequestInit } from "undici";
import { avalancheFuji, baseSepolia, Chain, sepolia } from "viem/chains";

// ---------------------------------------------------------------------------
// env + bootstrap
// ---------------------------------------------------------------------------

dotenv.config();
const PORT = Number(process.env.MAIN_PORT ?? 3000);

const app = express();
app.use(bodyParser.json());
app.use(cors({
  origin: "*", 
  methods: ["GET", "POST", "OPTIONS"],
  allowedHeaders: ["Content-Type", "x-api-key"],
}));

app.get("/health", (_req, res) => {
  res.status(200).json({ status: "ok", message: "server running" });
});

// ---------------------------------------------------------------------------
// keys / chain map
// ---------------------------------------------------------------------------

const rawKeys = process.env.PRIVATE_KEYS;
if (!rawKeys) throw new Error("Missing PRIVATE_KEYS in .env");
let pk = rawKeys.split(",")[0].trim();
if (!pk.startsWith("0x")) pk = "0x" + pk;
const PRIVATE_KEY = pk as `0x${string}`;

const apiKey = process.env.HTTPAYER_API_KEY;
if (!apiKey) throw new Error("Missing HTTPAYER_API_KEY in .env");

const CHAIN_MAP: Record<string, Chain> = {
  "base-sepolia": baseSepolia,
  "avalanche-fuji": avalancheFuji,
  sepolia,
};

// ---------------------------------------------------------------------------
// helper – build a clean RequestInit (no content-length on GET)
// ---------------------------------------------------------------------------

function buildInit(
  method: string,
  payload: unknown,
): UndiciRequestInit {
  if (method.toUpperCase() === "GET") {
    return {
      method,
      headers: {}  // add this
    };
  }

  const body = JSON.stringify(payload ?? {});
  return {
    method,
    body,
    headers: { "Content-Type": "application/json" },
  };
}

// ---------------------------------------------------------------------------
// main proxy
// ---------------------------------------------------------------------------

app.post("/pay", async (req, res) => {
  //-------------------------------- auth
  if (req.headers["x-api-key"] !== apiKey) {
    res.status(401).json({ error: "Unauthorized: invalid API key" });
    return;
  }

  const { api_url, method, payload } = req.body as {
    api_url: string;
    method: string;
    payload?: unknown;
  };

  console.log("[httpayer] →", method, api_url);

  const baseInit = buildInit(method, payload);

  try {
    //────────────────── first attempt
    const initialResp = await undiciFetch(api_url, baseInit as any);
    console.log("[httpayer] first status", initialResp.status);

    if (initialResp.status !== 402) {
      res.status(initialResp.status).send(await initialResp.text());
      return;
    }

    //────────────────── extract payment reqs
    const { accepts = [] } = await initialResp.json() as { accepts?: any[] };
    const exact = accepts.find((x) => x.scheme === "exact");

    if (!exact?.network) {
      res.status(400).json({ error: "Missing exact scheme or network" });
      return;
    }

    const chain = CHAIN_MAP[exact.network];
    if (!chain) {
      res.status(400).json({ error: `Unsupported network: ${exact.network}` });
      return;
    }

    //────────────────── set-up paid fetch
    const account = privateKeyToAccount(PRIVATE_KEY);
    const walletClient = createWalletClient({
      account,
      transport: http(),
      chain,
    });
    const fetchWithPay = wrapFetchWithPayment(undiciFetch as any, walletClient);

    const paidInit: UndiciRequestInit & { paymentRequirements: any } = {
      ...baseInit,
      paymentRequirements: [exact],
      headers: {
        ...(baseInit.headers ?? {}),
        connection: "close",
      },
    };

    console.log("[httpayer] fetch init", JSON.stringify(baseInit));

    console.log(
      "[httpayer] paying…",
      `{chain:${chain.name}  to:${exact.payTo}  amount:${exact.maxAmountRequired}}`,
    );

    const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    let paidResp = await fetchWithPay(api_url, paidInit as any);
    console.log("[httpayer] paid status", paidResp.status);

    // Retry once if payment hasn't been picked up yet
    if (paidResp.status === 402) {
      console.warn("[httpayer] got 402 after payment, retrying after delay…");
      await delay(2500); // wait 2.5 seconds
      paidResp = await fetchWithPay(api_url, paidInit as any);
      console.log("[httpayer] retry status", paidResp.status);
    }
    const text = await paidResp.text();

    console.log("[httpayer] paid status", paidResp.status);

    // optional callback
    const payHdr = paidResp.headers.get("x-payment-response");
    if (payHdr) {
      const dec = decodeXPaymentResponse(payHdr);
      if (dec.callbackUrl) {
        undiciFetch(dec.callbackUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tx_hash: dec.txHash }),
        }).catch((e) => console.warn("callback failed", e));
      }
    }

    res.status(paidResp.status).send(text);
  } catch (err: any) {
    console.error("[httpayer] error:", err);
    res.status(500).json({ error: err.message ?? "unknown error" });
  }
});

// ---------------------------------------------------------------------------
// serve
// ---------------------------------------------------------------------------

app.listen(
  PORT,
  "0.0.0.0",
  () => console.log(`httpayer server running on :${PORT}`),
);
