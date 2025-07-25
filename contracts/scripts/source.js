const apiUrl = args[0];
const methodUrl = args[1];

let payload = null;
try {
    payload = JSON.parse(args[2]);
} catch {
    payload = methodUrl === "GET" ? null : {};
}

const apiKey = "chainlinkhack2025";
const httpayerUrl = "http://app.httpayer.com/httpayer";

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

let resultString;

try {
    const data = response.data;
    if (typeof data === "object" && data !== null) {
        resultString = JSON.stringify(data);
    } else if (typeof data === "string") {
        resultString = data;
    } else {
        resultString = "Missing or invalid body";
    }
} catch (e) {
    resultString = "Failed to parse body: " + e.message;
}

console.log("Result:", resultString.slice(0, 200));

return Functions.encodeString(resultString.slice(0, 200));