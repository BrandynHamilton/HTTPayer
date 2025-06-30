const apiUrl = args[0];
const methodUrl = args[1];

let payload;
try {
    payload = JSON.parse(args[2]);
    if (payload === null) payload = null;
} catch {
    payload = methodUrl === "GET" ? null : {};
}

const apiKey = "chainlinkhack2025";
const httpayerUrl = "http://provider.boogle.cloud:31157/httpayer";

const response = await Functions.makeHttpRequest({
    url: httpayerUrl,
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
    },
    data: {
        api_url: apiUrl,
        method: methodUrl,
        payload: payload,
    },
});

// ─── Extract nested body ────────────────────────────────────────
let resultString;

try {
    const level1 = response?.data;
    const level2 = level1?.body;
    const level3 = level2?.data?.body ?? level2;  // handles both formats

    if (typeof level3 === "string") {
        resultString = level3;
    } else if (level3 && typeof level3 === "object") {
        resultString = JSON.stringify(level3);
    } else {
        resultString = "Missing or invalid body";
    }
} catch (e) {
    resultString = "Failed to parse body: " + e.message;
}

// ─── Final fallback ─────────────────────────────────────────────
if (typeof resultString !== "string") {
    resultString = "Unexpected result type";
}

return Functions.encodeString(resultString.slice(0, 200));
