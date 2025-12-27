"""验证12月18日数据"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval
from datetime import datetime, timedelta

tv = TvDatafeed()

print("=" * 80)
print("验证 PLV2026 在 2025-12-18 的数据")
print("=" * 80)

cme = tv.get_hist(symbol='PLV2026', exchange='NYMEX', interval=Interval.in_1_hour, n_bars=500)
cme = cme.sort_index()

# 查找12月18日的所有数据
dec18_data = cme[(cme.index >= datetime(2025, 12, 18)) & (cme.index < datetime(2025, 12, 19))]

print("\nTvDatafeed 返回的 PLV2026 12月18日所有小时数据:")
print(f"{'北京时间':<20} | {'美东时间':<20} | {'开盘':>10} | {'最高':>10} | {'最低':>10} | {'收盘':>10}")
print("-" * 90)
for idx in dec18_data.index:
    row = dec18_data.loc[idx]
    us_time = idx - timedelta(hours=13)
    print(f"{idx.strftime('%Y-%m-%d %H:%M'):<20} | {us_time.strftime('%Y-%m-%d %H:%M'):<20} | {row['open']:>10.2f} | {row['high']:>10.2f} | {row['low']:>10.2f} | {row['close']:>10.2f}")

print("\n" + "=" * 80)
print("富途截图数据 (美东时间 12/18 02:00):")
print("  开盘: 2050.9")
print("  最高: 2055.0")
print("  最低: 2049.7")
print("  收盘: 2049.7")
print("=" * 80)
