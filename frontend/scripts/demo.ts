// A simple script to test the /httpayer endpoint.
//
// To run this file, you can use ts-node:
// 1. Install ts-node: `npm install -g ts-node`
// 2. Run the script: `ts-node test-httpayer.ts`
//
// Make sure your backend server is running first!

// --- Configuration ---
import "dotenv/config";
import {
    API_KEY,
    DEMO_SERVER_URL,
    HTTPAYER_URL,
} from "../src/constants/endpoints";

// --- Data for the target API ---
const TARGET_API_URL = `${DEMO_SERVER_URL}/base-weather`;
const TARGET_METHOD = "GET";
const TARGET_PAYLOAD = {};

// --- The Fetch Function ---
async function testHttpayerEndpoint() {
    console.log(`Sending request to: ${HTTPAYER_URL}`);
    console.log(`Proxying a ${TARGET_METHOD} request to: ${TARGET_API_URL}`);

    try {
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        };
        if (API_KEY) {
            headers["x-api-key"] = API_KEY;
        }
        const response = await fetch(HTTPAYER_URL, {
            method: "POST",
            headers,
            body: JSON.stringify({
                api_url: TARGET_API_URL,
                method: TARGET_METHOD,
                payload: TARGET_PAYLOAD,
            }),
        });

        console.log(`Response Status from httpayer: ${response.status}`);

        const responseData = await response.json();

        if (!response.ok) {
            console.error("Error from server:", responseData);
            throw new Error(`Request failed with status ${response.status}`);
        }

        console.log("Success! Response from target API:");
        console.log(responseData);
    } catch (error) {
        // This will catch network errors or errors from the throw above.
        console.error("An error occurred during the fetch operation:", error);
    }
}

// --- Run the test ---
testHttpayerEndpoint();
