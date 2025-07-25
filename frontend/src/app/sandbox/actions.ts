"use server";

import {
    DEMO_SERVER_URL,
    HTTPAYER_URL,
    TREASURY_URL,
} from "../../constants/endpoints";

// Read the private API key on the server
const API_KEY = process.env.HTTPAYER_API_KEY;

type TestResult = {
    success: boolean;
    data?: unknown;
    error?: string;
};

// This is the Server Action that the client will call.
export async function runServerTest(testName: string): Promise<TestResult> {
    if (!API_KEY) {
        return {
            success: false,
            error: "HTTPAYER_API_KEY is not set on the server.",
        };
    }

    try {
        let result: unknown;
        switch (testName) {
            case "HTTPayer Health": {
                const res = await fetch(
                    `${HTTPAYER_URL.replace("/httpayer", "")}/health`,
                );
                if (!res.ok) throw new Error(`Status ${res.status}`);
                result = await res.json();
                break;
            }
            case "Treasury Health": {
                const res = await fetch(`${TREASURY_URL}/health`);
                if (!res.ok) throw new Error(`Status ${res.status}`);
                result = await res.json();
                break;
            }
            case "Demo Server Health": {
                const res = await fetch(`${DEMO_SERVER_URL}/health`);
                if (!res.ok) throw new Error(`Status ${res.status}`);
                result = await res.json();
                break;
            }
            case "Basic Proxy (HTTPayer)": {
                const res = await fetch(HTTPAYER_URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "x-api-key": API_KEY,
                    },
                    body: JSON.stringify({
                        api_url: `${DEMO_SERVER_URL}/base-weather`,
                        method: "GET",
                    }),
                });
                if (!res.ok) throw new Error(`Status ${res.status}`);
                result = await res.json();
                break;
            }
            case "402 Payment Flow (HTTPayer)": {
                const res = await fetch(HTTPAYER_URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "x-api-key": API_KEY,
                    },
                    body: JSON.stringify({
                        api_url: `${DEMO_SERVER_URL}/avalanche-weather`,
                        method: "GET",
                    }),
                });
                if (!res.ok) throw new Error(`Status ${res.status}`);
                result = await res.json();
                break;
            }
            default:
                throw new Error("Invalid test name provided.");
        }
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: (error as Error).message };
    }
}
