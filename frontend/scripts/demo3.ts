// frontend/scripts/demo3.ts
// An advanced, realistic script demonstrating a full interaction with the HTTPayer ecosystem.

import {
    API_KEY,
    DEMO_SERVER_URL,
    FACILITATOR_URL,
    HTTPAYER_URL,
    TREASURY_URL,
} from "./vars";

// Helper function to check the health of a service
const checkServiceHealth = async (serviceName: string, healthUrl: string) => {
    try {
        const response = await fetch(healthUrl);
        if (response.ok) {
            console.log(`✅ ${serviceName} is online.`);
            return true;
        }
        throw new Error(`status ${response.status}`);
    } catch (error) {
        console.error(
            `❌ ${serviceName} is offline or unreachable. Error: ${error}`,
        );
        return false;
    }
};

// Helper function to make a POST request to the HTTPayer
const callHttpayer = (targetApiUrl: string) => {
    return fetch(HTTPAYER_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
        body: JSON.stringify({
            api_url: targetApiUrl,
            method: "GET",
            payload: {},
        }),
    });
};

async function runAdvancedDemo() {
    console.log("--- Starting Advanced HTTPayer Demo ---");
    console.log(
        "This script will check all services, query the treasury, and then fetch multiple paid resources in parallel.\n",
    );

    // 1. Perform health checks for all services in parallel
    console.log("Step 1: Checking health of all microservices...");
    const healthChecks = await Promise.all([
        checkServiceHealth(
            "HTTPayer Server",
            `${HTTPAYER_URL.replace("/httpayer", "")}/health`,
        ),
        checkServiceHealth("Treasury Server", `${TREASURY_URL}/health`),
        // checkServiceHealth("Facilitator Server", `${FACILITATOR_URL}/facilitator/health`), // Temporarily disabled
        checkServiceHealth("Demo Server", `${DEMO_SERVER_URL}/health`),
    ]);

    if (healthChecks.some((status) => !status)) {
        console.error(
            "\nAborting demo because one or more services are offline.",
        );
        return;
    }
    console.log("All services are operational.\n");

    // 2. Query the Treasury for its balances
    console.log("Step 2: Fetching treasury balances...");
    try {
        const treasuryResponse = await fetch(`${TREASURY_URL}/balances`);
        const treasuryData = await treasuryResponse.json();
        console.log(
            "Treasury Balances:",
            JSON.stringify(treasuryData, null, 2),
        );
    } catch (error) {
        console.error("Could not fetch treasury balances:", error);
    }

    // 3. Query the Facilitator for supported networks
    console.log(
        "\nStep 3: Fetching supported networks from Facilitator... (Temporarily disabled)",
    );
    /* try {
        const facilitatorResponse = await fetch(`${FACILITATOR_URL}/facilitator/supported`);
        const facilitatorData = await facilitatorResponse.json();
        console.log("Facilitator supports:", facilitatorData);
    } catch (error) {
        console.error("Could not fetch facilitator info:", error);
    } */

    // 4. Fetch multiple 402-protected resources in parallel via HTTPayer
    console.log(
        "\nStep 4: Requesting two paid resources in parallel via HTTPayer...",
    );
    const paidEndpoints = [
        `${DEMO_SERVER_URL}/base-weather`,
        `${DEMO_SERVER_URL}/avalanche-weather`,
    ];

    try {
        // Create an array of promises for the httpayer calls
        const paidRequests = paidEndpoints.map((url) => callHttpayer(url));

        // Use Promise.all to wait for all paid requests to be handled
        const responses = await Promise.all(paidRequests);

        console.log(
            "All paid requests have been successfully processed by HTTPayer.",
        );

        // Extract and log the JSON data from each response
        const results = await Promise.all(responses.map((res) => res.json()));

        console.log("\n--- Final Results ---");
        results.forEach((result, index) => {
            console.log(`Result from ${paidEndpoints[index]}:`);
            console.log(JSON.stringify(result, null, 2), "\n");
        });
    } catch (error) {
        console.error(
            "❌ An error occurred while fetching paid resources:",
            error,
        );
    }

    console.log("--- Advanced Demo Finished ---");
}

runAdvancedDemo();
