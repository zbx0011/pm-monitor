import akshare as ak
import os
import platform

if platform.system() == 'Windows':
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

try:
    df = ak.futures_zh_minute_sina(symbol='PT2610', period='1')
    print(f"Total rows: {len(df)}")
    print(f"First: {df['datetime'].iloc[0]}")
    print(f"Last: {df['datetime'].iloc[-1]}")
except Exception as e:
    print(f"Error: {e}")
