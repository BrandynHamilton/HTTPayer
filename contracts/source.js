const apiUrl = args[0];
const method = args[1] || "GET";
const payload = args[2] ? JSON.parse(args[2]) : {};
const apiKey = "chainlinkhack2025";
const httpayerUrl = "http://app.httpayer.com/httpayer"

const response = await Functions.makeHttpRequest({
    url: httpayerUrl, // Public HttPayer relay endpoint
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
    },
    data: {
        api_url: apiUrl,
        method: method,
        payload: payload
    },
});

if (response.error) {
    throw Error("HTTPayer call failed: " + JSON.stringify(response.error));
}

const { data } = response;
if (!data || !data.body) {
    throw Error("Invalid HTTPayer response body: " + JSON.stringify(response));
}

return Functions.encodeString(data.body.toString());