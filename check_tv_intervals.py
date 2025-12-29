import os
from tvDatafeed import TvDatafeed, Interval
import time

# 启用代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

tv = TvDatafeed()
symbol = 'PLJ2026'
exchange = 'NYMEX'

print(f"Checking {symbol} on {exchange}...")

def check(interval_name, interval_obj):
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval_obj, n_bars=5)
        if df is not None and not df.empty:
            last = df.iloc[-1]
            print(f"[{interval_name}] Time: {last.name} | Close: {last['close']}")
        else:
            print(f"[{interval_name}] No Data")
    except Exception as e:
        print(f"[{interval_name}] Error: {e}")

check("1 Min", Interval.in_1_minute)
check("5 Min", Interval.in_5_minute)
check("15 Min", Interval.in_15_minute)
check("1 Hour", Interval.in_1_hour)
check("Daily", Interval.in_daily)
