from diskcache import Cache
# from chartengineer import ChartMaker  # Temporarily disabled due to kaleido dependency issues
from pathlib import Path
import pandas as pd

CACHE_PATH = Path(__file__).resolve().parents[2] / "cache_dir"
print(f"Cache path: {CACHE_PATH}")
cache = Cache(CACHE_PATH)
def main():
    print("Cache contents:")
    for key in cache:
        print(f'Key: {key}, Value: {cache[key]}')

    data = cache.get('data', None)

    if data is not None:
        print(f"Retrieved data from cache: {data}")

    balances  = data.get('balances', None)
    print(f"Balances: {balances}")

    balances_df = pd.DataFrame(balances)
    print(f"Balances DataFrame:\n{balances_df}")

    chain_balances = balances_df.groupby('chain')[['balance']].sum()
    print(f"Chain Balances:\n{chain_balances}")

    address_balances = balances_df.groupby('address')[['balance']].sum()
    print(f"Address Balances:\n{address_balances}")

    cm = ChartMaker()
    cm.build(
        df=balances_df,
        groupby_col='chain',
        num_col='balance',
        title='Chain Balances',
        chart_type='pie',
        options = {
            'margin':dict(t=100),'annotations':True,
            'tickprefix':{'y1':'$'},'hole_size':0.5,
            'line_width':0,
            'texttemplate':'%{label}<br>%{percent}',
            'show_legend':False,'legend_placement':{'x':1.1,'y':1},
            'textinfo':'percent+label'
        }
    )
    cm.add_title()
    cm.save_fig(save_directory='img')

    return data

if __name__ == "__main__":
    print("Starting cache test...")
    main()
    print("Cache test completed.")