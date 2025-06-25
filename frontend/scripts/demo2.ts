// test-402-flow.ts

// IMPORTANT: Run `ts-node src/demoServer.ts` in another terminal before running this script.

import "dotenv/config";
import { DEMO_SERVER_URL, HTTPAYER_URL } from "./vars";

// The API key is now loaded from the environment
const API_KEY = process.env.HTTPAYER_API_KEY;

if (!API_KEY) {
    throw new Error(
        "HTTPAYER_API_KEY is not set. Please create a .env file in the /frontend directory.",
    );
}

// The demo server has a /avalanche-weather endpoint that requires payment
const TARGET_402_API_URL = `${DEMO_SERVER_URL}/avalanche-weather`;

async function test402PaymentFlow() {
    console.log("--- Testing the 402 Payment Flow ---");
    console.log(`Targeting the demo server at: ${TARGET_402_API_URL}`);

    try {
        const response = await fetch(HTTPAYER_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
            },
            body: JSON.stringify({
                api_url: TARGET_402_API_URL,
                method: "GET", // The paid resource is a GET request
                payload: {}, // No payload needed for GET
            }),
        });

        // The httpayer should resolve the 402 and return a 200 OK from the demo server
        console.log(`Final response status from httpayer: ${response.status}`);
        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(
                `Expected a successful response, but got ${response.status}`,
            );
        }

        console.log("Success! The 402 payment was handled correctly.");
        console.log("Final response from target API:", responseData);

        // Check if the response is what we expect from the demo server
        if (responseData.weather) {
            console.log(
                `✅ Test Passed: Received weather data: '${responseData.weather}'.`,
            );
        } else {
            console.error(
                "❌ Test Failed: Did not receive the expected content.",
            );
        }
    } catch (error) {
        console.error("An error occurred during the test:", error);
    }
}

// --- Other "Legit" Tests ---

async function testAuthenticationFailure() {
    console.log("\n--- Testing Authentication Failure ---");
    const response = await fetch(HTTPAYER_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": "WRONG_KEY", // Using an incorrect API key
        },
        body: JSON.stringify({
            api_url: TARGET_402_API_URL,
            method: "GET",
            payload: {},
        }),
    });

    console.log(`Response status: ${response.status}`);
    if (response.status === 401) {
        console.log(
            "✅ Test Passed: Server correctly returned 401 Unauthorized.",
        );
    } else {
        console.error(
            `❌ Test Failed: Expected status 401, but got ${response.status}.`,
        );
    }
}

// --- Run the tests ---
async function runAllTests() {
    await test402PaymentFlow();
    await testAuthenticationFailure();
}

runAllTests();
