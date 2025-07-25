"use client";

import { Dashboard } from "../components/Dashboard";
import ChainlinkFunctionsStatus from "../components/ChainlinkFunctionsStatus";
import { PaymentDemo } from "../components/PaymentDemo";

export default function Page() {
	return (
		<main className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground p-4 gap-8">
			<section className="w-full max-w-5xl flex flex-col gap-8">
				<h1 className="text-3xl font-bold mb-2 text-center">HTTPayer Demo</h1>
				<Dashboard />
				<PaymentDemo />
				<ChainlinkFunctionsStatus />
			</section>
		</main>
	);
}
