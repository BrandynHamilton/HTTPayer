"use client";

import { useState } from "react";
import { runServerTest } from "./actions"; // Import the Server Action

export default function SandboxPage() {
	const [results, setResults] = useState<Record<string, unknown>>({});
	const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});

	const handleTest = async (testName: string) => {
		setIsLoading((prev) => ({ ...prev, [testName]: true }));
		const result = await runServerTest(testName);
		if (result.success) {
			setResults((prev) => ({ ...prev, [testName]: result.data }));
		} else {
			setResults((prev) => ({
				...prev,
				[testName]: { error: result.error },
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
		<div style={{ fontFamily: "monospace", padding: "2rem" }}>
			<h1>Backend Service Sandbox</h1>
			<p>
				Click the buttons to securely test the deployed backend services via a
				Server Action.
			</p>
			<div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
				{testNames.map((name) => (
					<div key={name}>
						<button
							type="button"
							onClick={() => handleTest(name)}
							disabled={isLoading[name]}
						>
							{isLoading[name] ? "Loading..." : `Test: ${name}`}
						</button>
						{results[name] && (
							<pre
								style={{
									backgroundColor: "#f0f0f0",
									color: "#111",
									padding: "1rem",
									marginTop: "0.5rem",
									whiteSpace: "pre-wrap",
									wordBreak: "break-all",
								}}
							>
								{JSON.stringify(results[name], null, 2)}
							</pre>
						)}
					</div>
				))}
			</div>
		</div>
	);
}
