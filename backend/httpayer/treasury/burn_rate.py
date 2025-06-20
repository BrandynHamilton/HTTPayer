from typing import Literal, TypedDict
from decimal import Decimal
from web3 import Web3
from python_viem import get_chain_by_id, get_chain_by_name
from ccip_terminal import USDC_MAP, network_func
import requests
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

def get_input_selector(tx_hash: str, chain_id: int) -> str:
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": chain_id,
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": tx_hash,
        "apikey": ETHERSCAN_API_KEY,
    }
    input_data = requests.get(url, params=params, timeout=15).json()["result"]["input"]
    print(f"Input data for {tx_hash}: {input_data}")
    return input_data[:10]  # first 4 bytes + 0x

def rolling_burn(
    df: pd.DataFrame, window_days: int = 7
) -> tuple[Decimal, pd.DataFrame]:
    """Return avg daily burn-rate (USDC) over `window_days` and the daily series."""
    day = pd.Timedelta(days=1)
    daily = (
        df.set_index("ts")["usdc"]
        .resample("1D")
        .sum(min_count=1)   # USDC spent per calendar day
    )
    roll = daily.rolling(f"{window_days}D").mean()
    avg = Decimal(str(roll.dropna().iloc[-1] if len(roll.dropna()) else 0))
    return avg, daily.to_frame("daily_spend")

def current_usdc_balance(w3: Web3, contract_addr: str, wallet: str) -> Decimal:
    erc20 = w3.eth.contract(address=contract_addr, abi=[
        { "constant":True,"inputs":[{"name":"_owner","type":"address"}],
          "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],
          "type":"function" }
    ])
    bal_raw = erc20.functions.balanceOf(wallet).call()
    return Decimal(bal_raw) / Decimal(10**6)

def runway_metrics(bal: Decimal, burn_per_day: Decimal) -> dict[str, float]:
    if burn_per_day == 0:
        return {
            "days": float("inf"),
            "months": float("inf"),
            "hours": float("inf"),
            "years": float("inf"),
        }
    days = float(bal / burn_per_day)
    return {
        "days":   days,
        "months": days / 30.437,   # avg days/month
        "hours":  days * 24,
        "years":  days / 365.25    # includes leap years
    }

def fetch_authorized_burns(account_address, chain='base'):
    if chain == 'base':
        chain_name = 'Base Sepolia'
    elif chain == 'avalanche':
        chain_name = 'Avalanche Fuji'

    # print(f"Using chain: {chain_name}")

    chain_id = get_chain_by_name(chain_name)["id"]
    # print(F"Chain ID for {chain_name}: {chain_id}")

    url = "https://api.etherscan.io/v2/api"

    # print(f'base address: {USDC_MAP[chain]}')

    params = {
        "chainid": chain_id,
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDC_MAP[chain],
        'address': account_address,
        "fromBlock": 0,
        "toBlock": "latest",
        "apikey": ETHERSCAN_API_KEY,
        "sort": "asc"
    }

    rows: list[dict] = requests.get(url, params=params, timeout=15).json()["result"]

    # ── 0 transfers → return an *empty* frame but with a real DateTimeIndex ──
    if not rows:
        return pd.DataFrame({
            "ts": pd.to_datetime([], utc=True),
            "usdc": [],
            "hash": []
        })
    
    # print(f'rows: {len(rows)}')

    df = (
        pd.DataFrame(rows)
          .rename(columns={"timeStamp": "ts", "value": "raw_value"})
          .assign(
              ts        = lambda d: pd.to_datetime(d.ts.astype(int),
                                                   unit="s", utc=True, errors="coerce"),
              raw_value = lambda d: d.raw_value.astype("int64"),
              out       = lambda d: d["from"].str.lower() == account_address.lower(),
              is_402 = lambda d: d["functionName"].str.contains("transferWithAuthorization", case=False, na=False)
                 if "functionName" in d else pd.Series([False] * len(d), index=d.index),
              usdc      = lambda d: d.raw_value / 10**6,
          )
          .query("out and is_402")
          .dropna(subset=["ts"])
          .set_index("ts")         
          .sort_index()
          .loc[:, ["usdc", "hash"]] 
    )

    return df.reset_index()

