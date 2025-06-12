import express, { Request, Response } from "express";
import { paymentMiddleware } from "x402-express";
import { Buffer } from "buffer";

const app = express();

// Helper to decode Base64 → JSON
function decodeBase64Json(base64Str: string): any | null {
  try {
    const jsonStr = Buffer.from(base64Str, "base64").toString("utf-8");
    return JSON.parse(jsonStr);
  } catch (err) {
    console.error("Failed to decode Base64 x-payment header:", err);
    return null;
  }
}

app.use(
  paymentMiddleware(
    "0x58a4Cae5e8dDA3a5614972F34951e482a29ef0f0", // receiver wallet
    {
      "GET /weather": {
        price: "$0.001",
        network: "base-sepolia",
      },
    },
    {
      url: "https://x402.org/facilitator",
    }
  )
);

// Protected route
app.get("/weather", (req: Request, res: Response) => {
  const rawHeader = req.headers["x-payment"];
  console.log("=== Raw X-PAYMENT header ===\n", rawHeader);

  const decoded = typeof rawHeader === "string" ? decodeBase64Json(rawHeader) : null;
  console.log("=== Decoded X-PAYMENT ===\n", JSON.stringify(decoded, null, 2));

  if (decoded) {
    console.log("Full payload:", JSON.stringify(decoded.payload, null, 2));
  }

  res.send({
    report: {
      weather: "sunny",
      temperature: 70,
    },
  });
});

app.listen(4021, () => {
  console.log(`Server listening at http://localhost:4021`);
});
