"use client";

import type { FC } from "react";

/**
 * ChainlinkFunctionsStatus
 * Narrative/roadmap component for demo alignment.
 * Displays Chainlink Functions integration status and description.
 */
const ChainlinkFunctionsStatus: FC = () => {
	return (
		<section className="w-full max-w-md mx-auto mt-8 bg-white/5 rounded-xl shadow-lg p-8 border border-white/10 flex flex-col items-center text-center">
			<h2 className="text-2xl font-bold mb-2">
				Chainlink Functions Integration
			</h2>
			<p className="text-base text-black-300 mb-4">
				HTTPayer integrates with Chainlink Functions to enable smart contracts
				to programmatically trigger x402 payments and access valuable gated APIs
				(credit scores, financial attestations, weather data, and more) via
				secure, automated cross-chain stablecoin payments. This unlocks on-chain
				logic for off-chain monetized APIs through decentralized compute.
			</p>
			<div className="inline-flex items-center gap-2 px-4 py-2 rounded bg-yellow-100/10 border border-yellow-400/30 text-yellow-400 font-semibold text-sm">
				<span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
				Status: In Development (Roadmap)
			</div>
		</section>
	);
};

export default ChainlinkFunctionsStatus;
