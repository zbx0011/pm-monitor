import akshare as ak
import pandas as pd
from datetime import datetime

print(f"Current Time: {datetime.now()}")

try:
    print("Fetching GFEX PT2610...")
    df = ak.futures_zh_minute_sina(symbol='PT2610', period='1')
    if df is not None and not df.empty:
        last_row = df.iloc[-1]
        print(f"Latest GFEX Data: {last_row['datetime']} | Price: {last_row['close']}")
    else:
        print("GFEX Data Empty")
except Exception as e:
    print(f"GFEX Error: {e}")
