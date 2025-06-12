import express from "express";
import dotenv from "dotenv";
import bodyParser from "body-parser";
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { wrapFetchWithPayment, decodeXPaymentResponse } from "x402-fetch";
import { fetch as undiciFetch } from "undici";
import { baseSepolia, avalancheFuji, celoAlfajores, optimismSepolia, mainnet, sepolia, } from "viem/chains";
const CHAIN_MAP = {
    "base-sepolia": baseSepolia,
    "avalanche-fuji": avalancheFuji,
    "celo-alfajores": celoAlfajores,
    "optimism-sepolia": optimismSepolia,
    "ethereum": mainnet,
    "sepolia": sepolia,
};
// Load environment variables
dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;
app.use(bodyParser.json());
// Validate PRIVATE_KEY
let rawPk = process.env.PRIVATE_KEY;
if (!rawPk)
    throw new Error("Missing PRIVATE_KEY in .env");
if (!rawPk.startsWith("0x"))
    rawPk = "0x" + rawPk;
const PRIVATE_KEY = rawPk;
// Main endpoint
app.post("/httpayer", async (req, res) => {
    const { api_url, method, payload } = req.body;
    const requestInit = {
        method,
        headers: { "Content-Type": "application/json" },
        body: method !== "GET" ? JSON.stringify(payload) : undefined,
    };
    try {
        // First attempt (unauthenticated)
        const initialResp = await undiciFetch(api_url, requestInit);
        if (initialResp.status !== 402) {
            const body = await initialResp.text();
            res.status(initialResp.status).send(body);
            return;
        }
        // Extract JSON from 402 body to get `accepts` list
        const errorJson = await initialResp.json();
        const accepts = errorJson.accepts || [];
        const exactScheme = accepts.find((x) => x.scheme === "exact");
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
        const fetchWithPayment = wrapFetchWithPayment(undiciFetch, walletClient);
        // Retry with payment
        const paidResp = await fetchWithPayment(api_url, requestInit);
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
    }
    catch (err) {
        console.error("Server error:", err);
        res.status(500).json({ error: err.message || "Unknown error" });
        return;
    }
});
app.listen(PORT, () => {
    console.log(`httpayer server running on port ${PORT}`);
});
