import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval
import time

tv = TvDatafeed()

def check_contract(symbol, exchange='NYMEX'):
    print(f"\nChecking {symbol} on {exchange}...")
    try:
        # Fetch very recent data
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_1_minute, n_bars=10)
        if df is not None and not df.empty:
            print(f"最近 5 分钟收盘价 ({symbol}):")
            for idx, row in df.tail(5).iterrows():
                print(f"{idx.strftime('%H:%M')} : {row['close']}")
            return df.iloc[-1]['close']
        else:
            print("No data found.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Check PLJ2026 (Apr 2026)
check_contract('PLJ2026')

# Check nearby contracts to see if there's confusion
print("\n--- Checking nearby contracts ---")
check_contract('PLF2026') # Jan 2026
check_contract('PLN2026') # Jul 2026
