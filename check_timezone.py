"""检查时区问题 - CME数据的时间戳是什么时区"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import akshare as ak
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from datetime import datetime

tv = TvDatafeed()

print("=" * 80)
print("检查时区问题")
print("=" * 80)

# 获取广期所 PT2610 小时数据
print("\n【广期所 PT2610 - 应该是北京时间】")
gfex = ak.futures_zh_minute_sina(symbol='PT2610', period='60')
gfex['datetime'] = pd.to_datetime(gfex['datetime'])
print(gfex[['datetime', 'close']].tail(10).to_string(index=False))

# 获取CME PLV2026 小时数据
print("\n【CME PLV2026 - TvDatafeed原始时间戳】")
cme = tv.get_hist(symbol='PLV2026', exchange='NYMEX', interval=Interval.in_1_hour, n_bars=50)
cme = cme.sort_index()
print("最后10条数据:")
for idx in cme.index[-10:]:
    print(f"  {idx} -> close: {cme.loc[idx, 'close']:.2f}")

print("\n" + "=" * 80)
print("分析:")
print("  - 如果CME时间戳是美东时间(EST/EDT), 北京时间 = 美东时间 + 13小时")
print("  - 广期所开盘时间: 北京时间 09:00-15:00")
print("  - CME NYMEX 开盘时间: 美东时间 18:00(前一天)-17:00")
print("=" * 80)
