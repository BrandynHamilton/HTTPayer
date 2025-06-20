from ccip_terminal.core import track_ccip_messages
import datetime as dt
import pandas as pd
from pathlib import Path
import json
from httpayer.treasury.liquidity import rebalance_once

LOG_PATH = Path("rebalance_log.csv")

def main():
    messages, rebalance_summary = rebalance_once()

    print("Rebalance Summary:")
    print(json.dumps(rebalance_summary, indent=2))
    
    # Capture log entry
    timestamp = dt.datetime.utcnow().isoformat(timespec="seconds")
    
    # Flatten each action into its own row
    actions  = rebalance_summary.get("actions", [])
    skipped  = rebalance_summary.get("skipped", [])
    run_note = rebalance_summary.get("message")   # may be None

    # 1)  CSV timeseries log  ───────────────────────────────────────────
    rows = []

    for r in actions:
        rows.append({
            "timestamp"   : timestamp,
            "from"        : r["from"],
            "to"          : r["to"],
            "amount_usdc" : r["amount_usdc"],
            "success"     : r["success"],
            "message_id"  : r.get("message_id"),
            "tx_hash"     : r.get("tx_hash"),
            "status"      : "action",
        })

    for s in skipped:
        rows.append({
            "timestamp"   : timestamp,
            "from"        : None,
            "to"          : s["chain"],
            "amount_usdc" : None,
            "success"     : False,
            "message_id"  : None,
            "tx_hash"     : None,
            "status"      : f"skipped: {s['reason']}",
        })

    # If there really was nothing to do, still write a row for posterity
    if not rows:
        rows.append({
            "timestamp"   : timestamp,
            "from"        : None,
            "to"          : None,
            "amount_usdc" : None,
            "success"     : None,
            "message_id"  : None,
            "tx_hash"     : None,
            "status"      : run_note or "no-op",
        })

    df = pd.DataFrame(rows)
    if LOG_PATH.exists():
        df.to_csv(LOG_PATH, mode="a", index=False, header=False)
    else:
        df.to_csv(LOG_PATH, index=False)

    # 2)  Console output  ───────────────────────────────────────────────
    if actions:
        for r in actions:
            print(f"{r['from']} ➜  {r['to']} | {r['amount_usdc']} USDC | success={r['success']}")
    else:
        print(run_note or "No rebalance actions this run.")

    for s in skipped:
        print(f"Skipped: {s['chain']} | Reason: {s['reason']}")

    # Message tracking
    if messages:
        track_ccip_messages(
            messages,
            wait_for_status=True,
            poll_interval=60,
            max_retries=10
        )
    else:
        print("No messages to track.")

if __name__ == "__main__":
    print("Starting liquidity rebalance script...")
    main()
