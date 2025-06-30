"use client";

import { useAccount, useConnect, useDisconnect } from "wagmi";

function App() {
	const account = useAccount();
	const { connectors, connect, status, error } = useConnect();
	const { disconnect } = useDisconnect();

	return (
		<div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground p-4">
			<div className="w-full max-w-md bg-white/5 rounded-xl shadow-lg p-8 mb-8 border border-white/10">
				<h2 className="text-2xl font-bold mb-4 text-center">Account</h2>
				<div className="mb-4 text-sm space-y-1">
					<div>
						<span className="font-semibold">Status:</span> {account.status}
					</div>
					<div>
						<span className="font-semibold">Addresses:</span>{" "}
						{JSON.stringify(account.addresses)}
					</div>
					<div>
						<span className="font-semibold">ChainId:</span> {account.chainId}
					</div>
				</div>
				{account.status === "connected" && (
					<button
						type="button"
						onClick={() => disconnect()}
						className="w-full bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-4 rounded transition-colors mb-2"
					>
						Disconnect
					</button>
				)}
			</div>

			<div className="w-full max-w-md bg-white/5 rounded-xl shadow-lg p-8 border border-white/10">
				<h2 className="text-2xl font-bold mb-4 text-center">Connect</h2>
				<div className="flex flex-wrap gap-2 mb-4">
					{connectors.map((connector) => (
						<button
							key={connector.uid}
							onClick={() => connect({ connector })}
							type="button"
							className="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 transition-colors focus:outline-none dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
						>
							{connector.name}
						</button>
					))}
				</div>
				<div className="text-xs text-gray-400 mb-1">{status}</div>
				{error?.message && (
					<div className="text-xs text-red-400">{error.message}</div>
				)}
			</div>
		</div>
	);
}

export default App;
