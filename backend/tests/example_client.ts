// index.ts

import dotenv from "dotenv";
dotenv.config();

import { wrapFetchWithPayment, decodeXPaymentResponse } from "x402-fetch";
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { baseSepolia } from "viem/chains";

//
// 1) Grab the raw env var (TS thinks it’s just string | undefined).
//
let rawPk = process.env.PRIVATE_KEY;
if (!rawPk) {
  throw new Error("Missing PRIVATE_KEY in .env");
}

// 2) If it doesn’t already start with “0x”, prepend it.
if (!rawPk.startsWith("0x")) {
  rawPk = "0x" + rawPk;
}

// 3) Now assert the type is `0x${string}` so TS is happy.
const PRIVATE_KEY = rawPk as `0x${string}`;

// 4) Derive a viem account
const account = privateKeyToAccount(PRIVATE_KEY);

// 5) Build a Viem wallet client on Base Sepolia
const walletClient = createWalletClient({
  chain: baseSepolia,
  transport: http(),
  account,
});

// 6) Wrap global fetch with payment support
const fetchWithPayment = wrapFetchWithPayment(fetch, walletClient);

// 7) Call the protected endpoint
const url = "http://localhost:4021/weather";

(async () => {
  try {
    const response = await fetchWithPayment(url, { method: "GET" });
    const body = await response.json();
    console.log("Response body:", body);

    const header = response.headers.get("x-payment-response");
    if (header) {
      const paymentResponse = decodeXPaymentResponse(header);
      console.log("Payment response:", paymentResponse);
    } else {
      console.warn("No x-payment-response header present");
    }
  } catch (err: any) {
    console.error("Paid fetch error:", err.response?.data?.error || err.message);
  }
})();
