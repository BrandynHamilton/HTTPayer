// index.ts
import dotenv from "dotenv";
import path from "path";

// Load .env from parent directory
dotenv.config({ path: path.resolve(__dirname, "../.env") });

import { wrapFetchWithPayment, decodeXPaymentResponse } from "x402-fetch";
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { baseSepolia } from "viem/chains";

// 1) Grab and validate private key from env
let rawPk = process.env.PRIVATE_KEY;
if (!rawPk) {
  throw new Error("Missing PRIVATE_KEY in ../.env");
}
if (!rawPk.startsWith("0x")) {
  rawPk = "0x" + rawPk;
}
const PRIVATE_KEY = rawPk as `0x${string}`;

// 2) Build wallet client
const account = privateKeyToAccount(PRIVATE_KEY);
const walletClient = createWalletClient({
  chain: baseSepolia,
  transport: http(),
  account,
});

// 3) Wrap fetch with X-PAYMENT logic
const fetchWithPayment = wrapFetchWithPayment(fetch, walletClient);

// 4) Make the paid request
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
