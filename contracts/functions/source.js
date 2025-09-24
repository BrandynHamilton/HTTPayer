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

// 🔹 Try to capture body
let resultString = response.text || "";
if (!resultString && response.data) {
  try {
    resultString = JSON.stringify(response.data);
  } catch (err) {
    resultString = "[Could not stringify response.data]";
  }
}

// 🔹 If still empty, include status + headers for debugging
if (!resultString) {
  resultString = `Empty body (status ${response.status || "unknown"})`;
  if (response.headers) {
    resultString += ` headers=${JSON.stringify(response.headers)}`;
  }
}

return Functions.encodeString(resultString);
