from textwrap import indent
import click
import os
from dotenv import load_dotenv
from python_viem import get_chain_by_id, get_chain_by_name
from regex import F
import requests
import json
from ccip_terminal import USDC_MAP, network_func
import pandas as pd
from typing import Literal, TypedDict
from decimal import Decimal
from web3 import Web3

from httpayer.treasury.burn_rate import (fetch_authorized_burns,
    rolling_burn, current_usdc_balance, runway_metrics)

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

# def rolling_burn(
#     df: pd.DataFrame, window_days: int = 7
# ) -> tuple[Decimal, pd.DataFrame]:
#     """Return avg daily burn-rate (USDC) over `window_days` and the daily series."""
#     day = pd.Timedelta(days=1)
#     daily = (
#         df.set_index("ts")["usdc"]
#         .resample("1D")
#         .sum(min_count=1)   # USDC spent per calendar day
#     )
#     roll = daily.rolling(f"{window_days}D").mean()
#     avg = Decimal(str(roll.dropna().iloc[-1] if len(roll.dropna()) else 0))
#     return avg, daily.to_frame("daily_spend")

# def current_usdc_balance(w3: Web3, contract_addr: str, wallet: str) -> Decimal:
#     erc20 = w3.eth.contract(address=contract_addr, abi=[
#         { "constant":True,"inputs":[{"name":"_owner","type":"address"}],
#           "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],
#           "type":"function" }
#     ])
#     bal_raw = erc20.functions.balanceOf(wallet).call()
#     return Decimal(bal_raw) / Decimal(10**6)

# def runway_metrics(bal: Decimal, burn_per_day: Decimal) -> dict[str, float]:
#     if burn_per_day == 0:
#         return {
#             "days": float("inf"),
#             "months": float("inf"),
#             "hours": float("inf"),
#             "years": float("inf"),
#         }
#     days = float(bal / burn_per_day)
#     return {
#         "days":   days,
#         "months": days / 30.437,   # avg days/month
#         "hours":  days * 24,
#         "years":  days / 365.25    # includes leap years
#     }

# def main(chain):
#     if chain == 'base':
#         chain_name = 'Base Sepolia'
#     elif chain == 'avalanche':
#         chain_name = 'Avalanche Fuji'

#     AUTH_SELECTOR = "0x7b04882a"

#     print(f"Using chain: {chain}")

#     print(f"Using chain: {chain_name}")

#     chain_id = get_chain_by_name(chain_name)["id"]
#     print(F"Chain ID for {chain_name}: {chain_id}")

#     url = "https://api.etherscan.io/v2/api"

#     print(f'base address: {USDC_MAP[chain]}')

#     params = {
#         "chainid": chain_id,
#         "module": "account",
#         "action": "tokentx",
#         "contractaddress": USDC_MAP[chain],
#         'address': ACCOUNT_ADDRESS,
#         "fromBlock": 0,
#         "toBlock": "latest",
#         "apikey": ETHERSCAN_API_KEY,
#         "sort": "asc"
#     }

#     rows: list[dict] = requests.get(url, params=params, timeout=15).json()["result"]
#     print(f'rows: {rows}')

#     df = (
#         pd.DataFrame(rows)
#         .rename(columns={"timeStamp": "ts", "value": "raw_value"})
#         .assign(
#             ts=lambda d: pd.to_datetime(d.ts.astype(int), unit="s", utc=True),
#             raw_value=lambda d: d.raw_value.astype("Int64"),
#             out=lambda d: d["from"].str.lower() == ACCOUNT_ADDRESS.lower(),
#             is_402=lambda d: d["functionName"].str.contains("transferWithAuthorization", case=False, na=False),
#             usdc=lambda d: d.raw_value / 10**6,
#         )
#         .query("out and is_402")
#         .loc[:, ["ts", "hash", "usdc"]]
#         .sort_values("ts")
#     )

#     return df

if __name__ == "__main__":

    chain = "base"  # or "avalanche"
    ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS", "0x6f8550D4B3Af628d5eDe06131FE60A1d2A5DE2Ab")

    print(f"Pulling transfers for {ACCOUNT_ADDRESS} on {chain}…")
    df_tx = fetch_authorized_burns(ACCOUNT_ADDRESS, chain)
    print(f"Found {len(df_tx):,} outbound USDC transfers")

    breakpoint()

    avg_7d, daily = rolling_burn(df_tx, window_days=7)
    print(f"🟠  Rolling 7-day burn-rate: {avg_7d:.2f} USDC / day")

    w3 = network_func(chain)

    bal = current_usdc_balance(w3, USDC_MAP[chain], ACCOUNT_ADDRESS)
    print(f"🟢  Current USDC balance:   {bal:.2f}")

    runway = runway_metrics(bal, avg_7d)
    print(
        f"🛣️   Runway ≈ {runway['days']:.1f} days "
        f"({runway['months']:.2f} mo, {runway['years']:.2f} yrs ≈ {runway['hours']:.0f} h)"
    )


