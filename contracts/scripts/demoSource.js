(async () => {
    const apiUrl = "http://localhost:5036/base-weather";
    const methodUrl = "GET";

    let payload = null;

    const apiKey = "chainlinkhack2025";
    const httpayerUrl = "http://localhost:30001/httpayer";

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
        const body = data?.data?.body;
        if (typeof body === "string") {
            resultString = body;
        } else if (body && typeof body === "object") {
            resultString = JSON.stringify(body);
        } else if (typeof data === "string") {
            resultString = data;
        } else {
            resultString = "Missing or invalid body";
        }
    } catch (e) {
        resultString = "Failed to parse body: " + e.message;
    }

    console.log("Result:", resultString.slice(0, 200));
})();
