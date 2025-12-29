import os
import platform
import sqlite3
import pandas as pd
import akshare as ak
from tvDatafeed import TvDatafeed, Interval
from database import DB_FILE, save_pair_history
import warnings
warnings.filterwarnings('ignore')

# Contracts configuration
PLATINUM_GFEX = ['PT2606', 'PT2610']
PLATINUM_CME = {
    '2601': 'PLF2026',
    '2604': 'PLJ2026',
    '2607': 'PLN2026',
    '2610': 'PLV2026'
}

PALLADIUM_GFEX = ['PD2606', 'PD2608', 'PD2610', 'PD2612']
PALLADIUM_CME = {
    '2603': 'PAH2026',
    '2606': 'PAM2026',
    '2609': 'PAU2026',
    '2612': 'PAZ2026'
}

# Constants
OZ_TO_GRAM = 31.1034768
RATE = 7.25  # Default fallback

# Proxy setup
if platform.system() == 'Windows':
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

def get_exchange_rate():
    try:
        df = ak.fx_spot_quote()
        rate = float(df[df['配对'] == '美元/人民币']['最新价'].values[0])
        print(f"当前汇率: {rate}")
        return rate
    except:
        print(f"汇率获取失败，使用默认值: {RATE}")
        return RATE

def fetch_gfex_hourly(symbol):
    try:
        # Use period='60' for hourly data
        df = ak.futures_zh_minute_sina(symbol=symbol, period='60')
        if df is None or df.empty:
            return None
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()
        # Rename 'close' to 'price' for consistency
        df['price'] = df['close'].astype(float)
        return df[['price']]
    except Exception as e:
        print(f"  Error fetching GFEX {symbol}: {e}")
        return None

def fetch_cme_hourly(tv, symbol):
    try:
        # Use n_bars=1000 to cover enough hourly history (1000 hours ~ 40 days)
        df = tv.get_hist(symbol=symbol, exchange='NYMEX', interval=Interval.in_1_hour, n_bars=1000)
        if df is None or df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df['price'] = df['close'].astype(float)
        return df[['price']]
    except Exception as e:
        print(f"  Error fetching CME {symbol}: {e}")
        return None

def save_hourly_history(metal, pair_name, gfex_contract, cme_contract, history):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    table = 'platinum_pairs' if metal == 'platinum' else 'palladium_pairs'
    
    count = 0
    for item in history:
        try:
            # Use INSERT OR IGNORE to respect existing minute data
            cursor.execute(f'''
                INSERT OR IGNORE INTO {table} 
                (pair_name, gfex_contract, cme_contract, datetime, gfex_price, cme_usd, cme_cny, spread, spread_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pair_name, gfex_contract, cme_contract, 
                  item['date'], item['gfex_price'], item['cme_usd'], item['cme_cny'], 
                  item['spread'], item['spread_pct']))
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            # print(e)
            pass
    
    conn.commit()
    conn.close()
    return count

def process_metal(metal_name, gfex_symbols, cme_map, tv, rate):
    print(f"\nProcessing {metal_name}...")
    
    # 1. Fetch all data
    gfex_data = {}
    for s in gfex_symbols:
        print(f"  Fetching GFEX {s}...")
        df = fetch_gfex_hourly(s)
        if df is not None:
            gfex_data[s] = df
            
    cme_data = {}
    for k, v in cme_map.items():
        print(f"  Fetching CME {v}...")
        df = fetch_cme_hourly(tv, v)
        if df is not None:
            cme_data[v] = df
            
    # 2. Match pairs
    for g_sym in gfex_data:
        g_expiry = g_sym[-4:] # 2606
        for c_code, c_sym in cme_map.items():
            pair_name = f"{g_expiry}-{c_code}"
            
            if c_sym not in cme_data:
                continue
                
            df_g = gfex_data[g_sym].copy()
            df_c = cme_data[c_sym].copy()
            
            # Merge
            df_merged = pd.merge_asof(
                df_g, df_c, 
                left_index=True, right_index=True,
                suffixes=('_gfex', '_cme'),
                direction='nearest',
                tolerance=pd.Timedelta('2h') # Hourly data might be slightly offset
            ).dropna()
            
            if df_merged.empty:
                continue
                
            # Calculate
            history = []
            for idx, row in df_merged.iterrows():
                gfex_price = row['price_gfex']
                cme_usd = row['price_cme']
                cme_cny = cme_usd * rate / OZ_TO_GRAM
                spread = gfex_price - cme_cny
                spread_pct = (spread / cme_cny) * 100
                
                history.append({
                    'date': idx.strftime('%Y-%m-%d %H:%M'), # Format matches DB
                    'gfex_price': gfex_price,
                    'cme_usd': cme_usd,
                    'cme_cny': cme_cny,
                    'spread': spread,
                    'spread_pct': spread_pct
                })
                
            # Save
            inserted = save_hourly_history(metal_name, pair_name, g_sym, c_sym, history)
            print(f"  Saved {pair_name}: {inserted} new records (from {len(history)} total)")

def main():
    print("Starting Hourly History Import...")
    tv = TvDatafeed()
    rate = get_exchange_rate()
    
    process_metal('platinum', PLATINUM_GFEX, PLATINUM_CME, tv, rate)
    process_metal('palladium', PALLADIUM_GFEX, PALLADIUM_CME, tv, rate)
    print("\nImport Completed!")

if __name__ == "__main__":
    main()
