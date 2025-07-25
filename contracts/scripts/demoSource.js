(async () => {
    const apiUrl = "http://provider.akash-palmito.org:30862/base-weather";
    const methodUrl = "GET";

    let payload = null;

    const apiKey = "chainlinkhack2025";
    const httpayerUrl = "http://app.httpayer.com/httpayer";

    const response = await fetch(httpayerUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": apiKey,
        },
        body: JSON.stringify({
            api_url: apiUrl,
            method: methodUrl,
            payload: payload,
        }),
    });

    const data = await response.json();
    console.log("Response:", data);

    let resultString;
    try {
        if (typeof data === "string") {
            resultString = data;
        } else if (data && typeof data === "object") {
            resultString = JSON.stringify(data);
        } else {
            resultString = "Missing or invalid body";
        }
    } catch (e) {
        resultString = "Failed to parse body: " + e.message;
    }

    console.log("Result:", JSON.stringify(data).slice(0, 200));
})();
