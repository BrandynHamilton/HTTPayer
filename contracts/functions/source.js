const apiUrl = args[0];
const methodUrl = args[1];

const apiKey = "chainlinkhack2025";
const httpayerUrl = "https://app.httpayer.com/pay";

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
  },
});

// Prefer raw .text, else fallback to stringified .data
let resultString = response.text;
if (!resultString && response.data) {
  resultString = JSON.stringify(response.data);
}

if (!resultString) {
  resultString = "Missing response body";
}

return Functions.encodeString(resultString);
