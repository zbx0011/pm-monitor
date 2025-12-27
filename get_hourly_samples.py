"""获取上周数据 - 修正CME时间偏移"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import akshare as ak
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from datetime import datetime, timedelta

RATE = 7.04
OZ_TO_GRAM = 31.1035

tv = TvDatafeed()

print("=" * 130)
print("上周数据样本 (已修正CME时间偏移)")
print("说明: CME用14:00北京时间的K线 = 富途显示的美东02:00")
print("=" * 130)

# 广期所 PT2610
gfex_pt = ak.futures_zh_minute_sina(symbol='PT2610', period='60')
gfex_pt['datetime'] = pd.to_datetime(gfex_pt['datetime'])
gfex_pt = gfex_pt.set_index('datetime').sort_index()

# CME PLV2026
cme_pt = tv.get_hist(symbol='PLV2026', exchange='NYMEX', interval=Interval.in_1_hour, n_bars=500)
cme_pt = cme_pt.sort_index()

last_week_start = datetime(2025, 12, 16)
last_week_end = datetime(2025, 12, 22, 23, 59)

# 只取每天15:00的广期所数据
gfex_pt_15 = gfex_pt[(gfex_pt.index >= last_week_start) & (gfex_pt.index <= last_week_end)]
gfex_pt_15 = gfex_pt_15[gfex_pt_15.index.hour == 15]

print("\n【铂金 PT2610 vs PLV2026】")
print("-" * 130)
print(f"{'广期所(北京)':<18} | {'CME K线(北京)':<18} | {'富途显示(美东)':<18} | {'PT2610':>10} | {'PLV2026':>10} | {'折算':>8} | {'价差':>8} | {'溢价%':>7}")
print("-" * 130)

for idx, row in gfex_pt_15.iterrows():
    # 广期所15:00，匹配CME 14:00的K线 (因为TvDatafeed用开始时间，富途用结束时间)
    cme_target = idx - timedelta(hours=1)  # 14:00
    time_diff = abs((cme_pt.index - cme_target).total_seconds())
    matches = cme_pt[time_diff <= 1800]
    
    if len(matches) > 0:
        gfex_price = float(row['close'])
        cme_row = matches.iloc[0]
        cme_time_bj = matches.index[0]
        cme_time_us = cme_time_bj - timedelta(hours=13) + timedelta(hours=1)  # 转美东 + 1小时 = 富途显示时间
        cme_usd = float(cme_row['close'])
        cme_cny = cme_usd * RATE / OZ_TO_GRAM
        spread = gfex_price - cme_cny
        spread_pct = (spread / cme_cny) * 100
        
        print(f"{idx.strftime('%Y-%m-%d %H:%M'):<18} | {cme_time_bj.strftime('%Y-%m-%d %H:%M'):<18} | {cme_time_us.strftime('%Y-%m-%d %H:%M'):<18} | {gfex_price:>10.2f} | {cme_usd:>10.2f} | {cme_cny:>8.2f} | {spread:>+8.2f} | {spread_pct:>+7.2f}%")

# 钯金同理
gfex_pd = ak.futures_zh_minute_sina(symbol='PD2606', period='60')
gfex_pd['datetime'] = pd.to_datetime(gfex_pd['datetime'])
gfex_pd = gfex_pd.set_index('datetime').sort_index()

cme_pd = tv.get_hist(symbol='PAM2026', exchange='NYMEX', interval=Interval.in_1_hour, n_bars=500)
cme_pd = cme_pd.sort_index()

gfex_pd_15 = gfex_pd[(gfex_pd.index >= last_week_start) & (gfex_pd.index <= last_week_end)]
gfex_pd_15 = gfex_pd_15[gfex_pd_15.index.hour == 15]

print("\n【钯金 PD2606 vs PAM2026】")
print("-" * 130)
print(f"{'广期所(北京)':<18} | {'CME K线(北京)':<18} | {'富途显示(美东)':<18} | {'PD2606':>10} | {'PAM2026':>10} | {'折算':>8} | {'价差':>8} | {'溢价%':>7}")
print("-" * 130)

for idx, row in gfex_pd_15.iterrows():
    cme_target = idx - timedelta(hours=1)
    time_diff = abs((cme_pd.index - cme_target).total_seconds())
    matches = cme_pd[time_diff <= 1800]
    
    if len(matches) > 0:
        gfex_price = float(row['close'])
        cme_row = matches.iloc[0]
        cme_time_bj = matches.index[0]
        cme_time_us = cme_time_bj - timedelta(hours=13) + timedelta(hours=1)
        cme_usd = float(cme_row['close'])
        cme_cny = cme_usd * RATE / OZ_TO_GRAM
        spread = gfex_price - cme_cny
        spread_pct = (spread / cme_cny) * 100
        
        print(f"{idx.strftime('%Y-%m-%d %H:%M'):<18} | {cme_time_bj.strftime('%Y-%m-%d %H:%M'):<18} | {cme_time_us.strftime('%Y-%m-%d %H:%M'):<18} | {gfex_price:>10.2f} | {cme_usd:>10.2f} | {cme_cny:>8.2f} | {spread:>+8.2f} | {spread_pct:>+7.2f}%")

print("\n" + "=" * 130)
print("汇率: 7.04 | 1盎司 = 31.1035克")
print("=" * 130)
