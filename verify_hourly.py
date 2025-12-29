import os
import platform
import akshare as ak

# Set proxy for Windows
if platform.system() == 'Windows':
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

try:
    print("Checking PT2610 hourly data...")
    # Fetch 60-minute bars
    df = ak.futures_zh_minute_sina(symbol='PT2610', period='60')
    print(f"Count: {len(df)}")
    if not df.empty:
        print(f"Start: {df['datetime'].iloc[0]}")
        print(f"End: {df['datetime'].iloc[-1]}")
    else:
        print("Dataframe is empty.")

except Exception as e:
    print(f"Error: {e}")
