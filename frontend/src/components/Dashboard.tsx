"use client";

import { Wallet, CheckCircle, XCircle } from "lucide-react";

const staticData = {
	base: {
		usdc_balance: "1,234.56",
		eth_balance: "0.123",
	},
	avalanche: {
		usdc_balance: "5,678.90",
		avax_balance: "0.456",
	},
	facilitators: {
		base: "online",
		avalanche: "online",
	},
};

const StatusIndicator = ({
	status,
}: { status: "online" | "offline" | "unknown" }) => {
	const isOnline = status === "online";
	const Icon = isOnline ? CheckCircle : XCircle;
	const color = isOnline ? "text-green-400" : "text-red-400";

	return (
		<span className={`inline-flex items-center gap-1 font-semibold ${color}`}>
			<Icon className="w-4 h-4" />
			{status.charAt(0).toUpperCase() + status.slice(1)}
		</span>
	);
};

export function Dashboard() {
	const cardClasses = "bg-gray-800 p-6 rounded-lg shadow-lg";
	const titleClasses =
		"text-lg font-semibold text-gray-300 mb-4 flex items-center gap-2";

	return (
		<div className="grid grid-cols-1 gap-6 md:grid-cols-3">
			<div className={cardClasses}>
				<h2 className={titleClasses}>
					<Wallet className="w-5 h-5" />
					Base Sepolia Balance
				</h2>
				<div className="space-y-2">
					<p className="text-2xl font-mono">
						{staticData.base.usdc_balance} USDC
					</p>
					<p className="text-sm font-mono text-gray-400">
						{staticData.base.eth_balance} ETH
					</p>
				</div>
			</div>
			<div className={cardClasses}>
				<h2 className={titleClasses}>
					<Wallet className="w-5 h-5" />
					Avalanche Fuji Balance
				</h2>
				<div className="space-y-2">
					<p className="text-2xl font-mono">
						{staticData.avalanche.usdc_balance} USDC
					</p>
					<p className="text-sm font-mono text-gray-400">
						{staticData.avalanche.avax_balance} AVAX
					</p>
				</div>
			</div>
			<div className={cardClasses}>
				<h2 className={titleClasses}>System Status</h2>
				<div className="space-y-2 text-sm">
					<p>
						Base Facilitator:{" "}
						<StatusIndicator
							status={staticData.facilitators.base as "online"}
						/>
					</p>
					<p>
						AVAX Facilitator:{" "}
						<StatusIndicator
							status={staticData.facilitators.avalanche as "online"}
						/>
					</p>
				</div>
			</div>
		</div>
	);
}
