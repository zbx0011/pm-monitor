"""获取广期所铂金和CME铂金其他月份合约的小时数据"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import akshare as ak
import pandas as pd
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

print("=" * 100)
print("获取铂金各月份合约小时数据")
print("=" * 100)

# ========== 广期所铂金合约 ==========
print("\n【广期所铂金合约】")
print("-" * 100)

# 尝试获取不同月份的合约
gfex_contracts = ['PT2506', 'PT2510', 'PT2606', 'PT2610']

for symbol in gfex_contracts:
    try:
        df = ak.futures_zh_minute_sina(symbol=symbol, period='60')
        if df is not None and len(df) > 0:
            df['datetime'] = pd.to_datetime(df['datetime'])
            latest = df.iloc[-1]
            print(f"  {symbol}: 最新 {latest['datetime'].strftime('%Y-%m-%d %H:%M')} | 收盘: {latest['close']:.2f} | 数据条数: {len(df)}")
    except Exception as e:
        print(f"  {symbol}: 获取失败 - {e}")

# ========== CME铂金合约 ==========
print("\n【CME铂金合约 (NYMEX)】")
print("-" * 100)

# CME铂金期货使用 PLxYYYY 格式 (x=月份代码: F=1月, G=2月, H=3月, J=4月, K=5月, M=6月, N=7月, Q=8月, U=9月, V=10月, X=11月, Z=12月)
# 或者 PLxYY 格式
cme_contracts = [
    ('PLF2025', '2025年1月'),
    ('PLJ2025', '2025年4月'), 
    ('PLN2025', '2025年7月'),
    ('PLV2025', '2025年10月'),
    ('PLF2026', '2026年1月'),
    ('PLJ2026', '2026年4月'),
    ('PLN2026', '2026年7月'),
    ('PLV2026', '2026年10月'),
]

for symbol, desc in cme_contracts:
    try:
        df = tv.get_hist(symbol=symbol, exchange='NYMEX', interval=Interval.in_1_hour, n_bars=50)
        if df is not None and len(df) > 0:
            df = df.sort_index()
            latest_time = df.index[-1]
            latest_close = df['close'].iloc[-1]
            print(f"  {symbol} ({desc}): 最新 {latest_time.strftime('%Y-%m-%d %H:%M')} | 收盘: ${latest_close:.2f} | 数据条数: {len(df)}")
    except Exception as e:
        print(f"  {symbol} ({desc}): 获取失败 - {e}")

print("\n" + "=" * 100)
