# treasury/rebalancer.py
from __future__ import annotations
from ast import Tuple
import os, time, logging, math
from decimal import Decimal
from typing import Dict, Literal

import pandas as pd
from dotenv import load_dotenv
from web3 import Web3

from httpayer_core.treasury.burn_rate import (
    fetch_authorized_burns,       
    rolling_burn,
    current_usdc_balance,
    runway_metrics,
)
from ccip_terminal import send_ccip_transfer, USDC_MAP, network_func

################################################################################
# Config
################################################################################

load_dotenv()

ACCOUNT_ADDRESS  = os.getenv("ACCOUNT_ADDRESS")
PRIVATE_KEYS     = os.getenv("PRIVATE_KEYS", "").split(",")      # first key is signer
ETHERSCAN_API_KEY= os.getenv("ETHERSCAN_API_KEY")

# Chains we actively use for httpayer
ACTIVE_CHAINS: Dict[str, str] = {
    "base"      : "Base Sepolia",
    "avalanche" : "Avalanche Fuji",
}

# --- Policy ------------------------------------------------------------------
MIN_DAYS  = 30          # if runway < MIN → top-up
TOP_UP_TO = 60          # after top-up we should have this many days of runway
XFER_GRANULARITY = Decimal("10")   # send amounts in multiples of 10 USDC
MAX_XFER_USDC    = Decimal("5000")  # never move more than this in a single hop
# -----------------------------------------------------------------------------

################################################################################
# Helpers
################################################################################

def round_up(amount: Decimal, step: Decimal) -> Decimal:
    """Round up to the next multiple of `step` (e.g. 10 USDC)."""
    return ( (amount / step).to_integral_value(rounding="ROUND_UP") * step )

def chain_stats(chain: str, window_days: int = 7) -> dict:
    """Return balance, burn-rate, runway‐dict for one chain."""
    df = fetch_authorized_burns(ACCOUNT_ADDRESS, chain)

    burn_per_day, _ = rolling_burn(df, window_days=window_days)
    w3 = network_func(chain)
    bal = current_usdc_balance(w3, USDC_MAP[chain], ACCOUNT_ADDRESS)
    runway = runway_metrics(bal, burn_per_day)

    return {
        "balance"      : bal,              # Decimal USDC
        "burn_per_day" : burn_per_day,     # Decimal USDC / day
        "runway_days"  : runway["days"],   # float
    }

def find_donor(chains: dict[str, dict]) -> str | None:
    """Return the chain with the *largest* runway that is above TOP_UP_TO."""
    donor = max(chains.items(), key=lambda kv: kv[1]["runway_days"])
    if donor[1]["runway_days"] <= TOP_UP_TO:
        return None
    return donor[0]

################################################################################
# Main rebalance loop
################################################################################

def rebalance_once() -> tuple[list[dict], dict]:
    """
    Run one re-balance cycle.

    Returns
    -------
    (tracked_messages, rebalance_summary)

    tracked_messages : list[dict]
        • {message_id, dest_chain}

    rebalance_summary : dict
        {
          "status":   "success" | "partial" | "skipped" | "error",
          "message":  str,                              # short human note
          "actions":  list[dict],                       # every attempted x-chain move
          "skipped":  list[dict],                       # chains skipped with reason
        }
    """
    tracked_messages: list[dict] = []

    # ------------------------------------------------------------------ #
    #  summary skeleton
    # ------------------------------------------------------------------ #
    rebalance_summary: dict = {
        "status":  "init",
        "message": "",
        "actions": [],
        "skipped": [],
    }

    # ------------------------------------------------------------------ #
    #  Current state snapshot
    # ------------------------------------------------------------------ #
    stats: Dict[str, dict] = {c: chain_stats(c) for c in ACTIVE_CHAINS}
    logging.info("Current treasury view:")
    for c, s in stats.items():
        logging.info(
            "• %-9s  balance=%7.2f  burn=%5.2f/d  runway=%6.1f d",
            c, s["balance"], s["burn_per_day"], s["runway_days"]
        )

    # ------------------------------------------------------------------ #
    #  Which chains actually need a top-up?
    # ------------------------------------------------------------------ #
    needs_top_up = {c: s for c, s in stats.items() if s["runway_days"] < MIN_DAYS}
    if not needs_top_up:
        rebalance_summary.update(
            status="skipped",
            message=f"All chains have ≥ {MIN_DAYS}d runway – nothing to do.",
        )
        return tracked_messages, rebalance_summary

    # ------------------------------------------------------------------ #
    #  Find donor chain
    # ------------------------------------------------------------------ #
    donor_chain = find_donor(stats)
    if donor_chain is None:
        rebalance_summary.update(
            status="skipped",
            message="No chain has spare runway to donate.",
        )
        return tracked_messages, rebalance_summary

    donor_balance = stats[donor_chain]["balance"]
    logging.info("Donor selected: %s (balance %.2f USDC)", donor_chain, donor_balance)

    # ------------------------------------------------------------------ #
    #  Iterate over needy chains
    # ------------------------------------------------------------------ #
    for dest_chain, s in needs_top_up.items():
        target = Decimal(s["burn_per_day"]) * Decimal(TOP_UP_TO)
        needed = round_up(target - s["balance"], XFER_GRANULARITY)

        if needed <= 0:
            rebalance_summary["skipped"].append(
                {"chain": dest_chain, "reason": "already funded"}
            )
            continue
        if needed > MAX_XFER_USDC:
            needed = MAX_XFER_USDC
        if needed > donor_balance - XFER_GRANULARITY:
            rebalance_summary["skipped"].append(
                {"chain": dest_chain, "reason": f"donor lacks funds ({needed} USDC)"}
            )
            continue

        logging.info(
            "Rebalancing %.2f USDC  %s ➜ %s  (→ %.0f d runway)",
            needed, donor_chain, dest_chain, TOP_UP_TO
        )

        try:
            receipt, links, success, msg_id = send_ccip_transfer(
                to_address=ACCOUNT_ADDRESS,
                source_chain=donor_chain,
                dest_chain=dest_chain,
                amount=float(needed),
            )

            tx_hash = receipt.transactionHash.hex()

            tracked_messages.append({"message_id": msg_id, "dest_chain": dest_chain})
            rebalance_summary["actions"].append({
                "from": donor_chain,
                "to": dest_chain,
                "amount_usdc": float(needed),
                "message_id": msg_id,
                "tx_hash": tx_hash,
                "success": success,
                "ccip_url": links.get("ccip_url", ""),
            })

            donor_balance -= needed

        except Exception as exc:
            logging.exception("Rebalance failed: %s", exc)
            rebalance_summary["actions"].append({
                "from": donor_chain,
                "to": dest_chain,
                "amount_usdc": float(needed),
                "error": str(exc),
                "success": False,
            })

    # ------------------------------------------------------------------ #
    #  Final summary status
    # ------------------------------------------------------------------ #
    if not rebalance_summary["actions"]:
        # everything skipped
        rebalance_summary.update(
            status="skipped",
            message="No rebalances executed (see 'skipped')."
        )
    elif all(a.get("success") for a in rebalance_summary["actions"]):
        rebalance_summary.update(
            status="success",
            message=f"{len(rebalance_summary['actions'])} rebalances succeeded."
        )
    elif any(a.get("success") for a in rebalance_summary["actions"]):
        rebalance_summary.update(
            status="partial",
            message="Some rebalances succeeded, some failed."
        )
    else:
        rebalance_summary.update(
            status="error",
            message="All attempted rebalances failed."
        )

    return tracked_messages, rebalance_summary

################################################################################
# CLI entry-point
################################################################################

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
#     while True:
#         rebalance_once()
#         time.sleep(60 * 60)   
