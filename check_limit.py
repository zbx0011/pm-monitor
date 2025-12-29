import os
import platform
if platform.system() == 'Windows':
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import akshare as ak
try:
    print('Checking PT2610...')
    df = ak.futures_zh_minute_sina(symbol='PT2610', period='1')
    print(f'Count: {len(df)}')
    print(f'Start: {df["datetime"].iloc[0]}')
    print(f'End: {df["datetime"].iloc[-1]}')
except Exception as e:
    print(f'Error: {e}')
