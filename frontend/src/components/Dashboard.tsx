"use client";

import { useEffect, useState } from "react";
import { Wallet } from "lucide-react";

type BalanceResponse = {
  address: string;
  avg_burn: number;
  balance: number;
  chain: "base" | "avalanche";
  runway: {
    days: number | null;
    hours: number | null;
    months: number | null;
    years: number | null;
  };
}[];

export function Dashboard() {
  const [balances, setBalances] = useState<BalanceResponse>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_TREASURY_API_URL}/balances`)
      .then((res) => res.json())
      .then((data: BalanceResponse) => {
        setBalances(data);
      })
      .catch((err) => console.error("Error fetching balances:", err));
  }, []);

  // Helper to get total balance for each chain
  const getChainBalance = (chain: "base" | "avalanche") => {
    const chainEntries = balances.filter((b) => b.chain === chain);
    const total = chainEntries.reduce((sum, b) => sum + b.balance, 0);
    return total.toFixed(2);
  };

  const cardClasses = "bg-gray-800 p-6 rounded-lg shadow-lg";
  const titleClasses = "text-lg font-semibold text-gray-300 mb-4 flex items-center gap-2";

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <div className={cardClasses}>
        <h2 className={titleClasses}>
          <Wallet className="w-5 h-5" />
          Base Sepolia Balance
        </h2>
        <p className="text-2xl font-mono text-white">
          {getChainBalance("base")} USDC
        </p>
      </div>

      <div className={cardClasses}>
        <h2 className={titleClasses}>
          <Wallet className="w-5 h-5" />
          Avalanche Fuji Balance
        </h2>
        <p className="text-2xl font-mono text-white">
          {getChainBalance("avalanche")} USDC
        </p>
      </div>
    </div>
  );
}
