"use client";

import { useState } from "react";
import { runServerTest } from "./actions"; // Import the Server Action

// Define a normalized result type
interface NormalizedResult {
	success: boolean;
	data?: unknown;
	error?: string;
}

export default function SandboxPage() {
	const [results, setResults] = useState<Record<string, NormalizedResult>>({});
	const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});

	const handleTest = async (testName: string) => {
		setIsLoading((prev) => ({ ...prev, [testName]: true }));
		const result = await runServerTest(testName);
		// Normalize the result structure
		if (result.success) {
			setResults((prev) => ({
				...prev,
				[testName]: { success: true, data: result.data },
			}));
		} else {
			setResults((prev) => ({
				...prev,
				[testName]: { success: false, error: result.error },
			}));
		}
		setIsLoading((prev) => ({ ...prev, [testName]: false }));
	};

	const testNames = [
		"HTTPayer Health",
		"Treasury Health",
		"Demo Server Health",
		"Basic Proxy (HTTPayer)",
		"402 Payment Flow (HTTPayer)",
	];

	return (
		<div className="min-h-screen bg-neutral-900 text-neutral-100 font-mono p-8">
			<h1 className="text-2xl font-bold mb-2">Backend Service Sandbox</h1>
			<p className="mb-8 text-neutral-300">
				Click the buttons to securely test the deployed backend services via a
				Server Action.
			</p>
			<div className="flex flex-col gap-8">
				{testNames.map((name) => {
					const result = results[name];
					return (
						<div key={name}>
							<button
								type="button"
								onClick={() => handleTest(name)}
								disabled={isLoading[name]}
								className="mb-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white font-semibold px-6 py-2 rounded-lg shadow transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-neutral-900"
							>
								{isLoading[name] ? "Loading..." : `Test: ${name}`}
							</button>
							{result && (
								<>
									{!result.success && result.error && (
										<div className="bg-red-600 text-white rounded-lg px-4 py-2 mb-2 font-semibold">
											Error: {result.error}
										</div>
									)}
									{result.success && (
										<pre className="bg-neutral-800 text-neutral-100 rounded-lg p-4 overflow-x-auto border border-neutral-700 text-sm mt-2">
											{JSON.stringify(result.data, null, 2)}
										</pre>
									)}
									{!result.success && (
										<pre className="bg-neutral-800 text-neutral-100 rounded-lg p-4 overflow-x-auto border border-neutral-700 text-sm mt-2">
											{JSON.stringify({ error: result.error }, null, 2)}
										</pre>
									)}
								</>
							)}
						</div>
					);
				})}
			</div>
		</div>
	);
}
