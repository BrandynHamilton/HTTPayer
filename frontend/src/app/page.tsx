"use client";

import { Dashboard } from "../components/Dashboard";
import ChainlinkFunctionsStatus from "../components/ChainlinkFunctionsStatus";
// import PaymentDemo from "../components/PaymentDemo"; // Uncomment when implemented

export default function Page() {
	return (
		<main className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground p-4 gap-8">
			<section className="w-full max-w-5xl flex flex-col gap-8">
				<h1 className="text-3xl font-bold mb-2 text-center">HTTPayer Demo</h1>
				<Dashboard />
				{/* <PaymentDemo /> */}
				<div className="w-full max-w-md mx-auto">
					<div className="bg-yellow-900/10 border border-yellow-400/30 rounded-lg p-4 text-yellow-300 text-center mb-4">
						<span className="font-semibold">PaymentDemo coming soon!</span>
					</div>
				</div>
				<ChainlinkFunctionsStatus />
			</section>
		</main>
	);
}
