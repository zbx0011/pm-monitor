from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import os
import platform

if platform.system() == 'Windows':
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

try:
    tv = TvDatafeed()
    print("Fetching USDCNH hourly data...")
    # FX_IDC is a common exchange for Forex in TV
    # USDCNH is Offshore RMB, which trades 24h and is close to market rate
    df = tv.get_hist(symbol='USDCNH', exchange='FX_IDC', interval=Interval.in_1_hour, n_bars=100)
    
    if df is not None and not df.empty:
        print(f"Count: {len(df)}")
        print(f"Start: {df.index[0]}")
        print(f"End: {df.index[-1]}")
        print("Last 5 rates:")
        print(df['close'].tail())
    else:
        print("USDCNH data is empty.")

except Exception as e:
    print(e)
