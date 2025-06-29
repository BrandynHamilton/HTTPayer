from diskcache import Cache
from chartengineer import ChartMaker
from pathlib import Path
import pandas as pd
import os
from dotenv import load_dotenv

from httpayer.treasury.burn_rate import (fetch_authorized_burns,
    rolling_burn, current_usdc_balance, runway_metrics)

CACHE_PATH = Path(__file__).resolve().parents[2] / "cache_dir"
cache = Cache(CACHE_PATH)
print(f"Cache path: {CACHE_PATH}")

data = cache.get('data', None)
balances  = data.get('balances', None)

print(f"Balances: {balances}")
print(f"Data: {data}")
breakpoint()

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

chain = "base"  # or "avalanche"
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS", "0x6f8550D4B3Af628d5eDe06131FE60A1d2A5DE2Ab")

print(f"Pulling transfers for {ACCOUNT_ADDRESS} on {chain}…")
df_tx = fetch_authorized_burns(ACCOUNT_ADDRESS, chain)
print(f"Found {len(df_tx):,} outbound USDC transfers")

df_tx.set_index("ts", inplace=True)
df_tx.index = pd.to_datetime(df_tx.index)
df_tx.sort_index(inplace=True)

count_df = df_tx.groupby(df_tx.index)[['hash']].count()

cm = ChartMaker()
cm.build(
    df=df_tx.resample('D').sum().fillna(0),
    axes_data = dict(y1=['usdc']),
    title='Chain Balances_1',
    chart_type='bar',
    options = {'margin':dict(t=100),'annotations':True,
                'tickprefix':{'y1':'$'},'auto_title':False,
                'show_legend':True,'legend_placement':{'x':0.01,'y':1.05}},
)
cm.add_title(title='Daily x402 Volume',
             subtitle=f"Total volume: ${df_tx['usdc'].sum():,.2f}")
cm.save_fig(save_directory='img')

print(f"count_df: {count_df}")

cm = ChartMaker()
cm.build(
    df=count_df.resample('D').sum().fillna(0),
    axes_data = dict(y1=['hash']),
    title='Chain Balances_2',
    chart_type='bar',
    options = {'margin':dict(t=100),'annotations':True,
                'tickprefix':{'y1':None},'auto_title':False,
                'show_legend':True,'legend_placement':{'x':0.01,'y':1.05}},
)
cm.add_title(title='Daily x402 Transactions',
             subtitle=f"Total transactions: {count_df['hash'].sum():,}")
cm.save_fig(save_directory='img')