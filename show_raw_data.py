"""分别显示两边原始数据 - 供用户验证"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import akshare as ak
import pandas as pd
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

print("=" * 80)
print("原始数据 - 供验证 (请对比您的行情软件)")
print("=" * 80)

# ========== 广期所 PT2610 ==========
print("\n【广期所 PT2610 - 最近10条小时数据】")
print("数据源: akshare futures_zh_minute_sina")
print("-" * 60)
gfex_pt = ak.futures_zh_minute_sina(symbol='PT2610', period='60')
gfex_pt['datetime'] = pd.to_datetime(gfex_pt['datetime'])
print(f"{'时间':<20} | {'开盘':>10} | {'最高':>10} | {'最低':>10} | {'收盘':>10}")
print("-" * 60)
for _, row in gfex_pt.tail(10).iterrows():
    print(f"{row['datetime'].strftime('%Y-%m-%d %H:%M'):<20} | {row['open']:>10.2f} | {row['high']:>10.2f} | {row['low']:>10.2f} | {row['close']:>10.2f}")

# ========== CME PLV2026 ==========
print("\n【CME PLV2026 - 最近10条小时数据】")
print("数据源: TvDatafeed (TradingView)")
print("-" * 60)
cme_pt = tv.get_hist(symbol='PLV2026', exchange='NYMEX', interval=Interval.in_1_hour, n_bars=50)
cme_pt = cme_pt.sort_index()
print(f"{'时间':<20} | {'开盘':>10} | {'最高':>10} | {'最低':>10} | {'收盘':>10}")
print("-" * 60)
for idx in cme_pt.index[-10:]:
    row = cme_pt.loc[idx]
    print(f"{idx.strftime('%Y-%m-%d %H:%M'):<20} | {row['open']:>10.2f} | {row['high']:>10.2f} | {row['low']:>10.2f} | {row['close']:>10.2f}")

# ========== 广期所 PD2606 ==========
print("\n【广期所 PD2606 - 最近10条小时数据】")
print("-" * 60)
gfex_pd = ak.futures_zh_minute_sina(symbol='PD2606', period='60')
gfex_pd['datetime'] = pd.to_datetime(gfex_pd['datetime'])
print(f"{'时间':<20} | {'开盘':>10} | {'最高':>10} | {'最低':>10} | {'收盘':>10}")
print("-" * 60)
for _, row in gfex_pd.tail(10).iterrows():
    print(f"{row['datetime'].strftime('%Y-%m-%d %H:%M'):<20} | {row['open']:>10.2f} | {row['high']:>10.2f} | {row['low']:>10.2f} | {row['close']:>10.2f}")

# ========== CME PAM2026 ==========
print("\n【CME PAM2026 - 最近10条小时数据】")
print("-" * 60)
cme_pd = tv.get_hist(symbol='PAM2026', exchange='NYMEX', interval=Interval.in_1_hour, n_bars=50)
cme_pd = cme_pd.sort_index()
print(f"{'时间':<20} | {'开盘':>10} | {'最高':>10} | {'最低':>10} | {'收盘':>10}")
print("-" * 60)
for idx in cme_pd.index[-10:]:
    row = cme_pd.loc[idx]
    print(f"{idx.strftime('%Y-%m-%d %H:%M'):<20} | {row['open']:>10.2f} | {row['high']:>10.2f} | {row['low']:>10.2f} | {row['close']:>10.2f}")

print("\n" + "=" * 80)
print("请对比以上数据与您的行情软件，确认时间和价格是否一致")
print("=" * 80)
