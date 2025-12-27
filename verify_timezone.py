"""验证TvDatafeed时区 - 对比富途截图"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval
from datetime import datetime, timedelta

tv = TvDatafeed()

print("=" * 80)
print("时区验证")
print("=" * 80)

# 当前时间
beijing_now = datetime.now()
us_eastern_now = beijing_now - timedelta(hours=13)  # 冬令时差13小时
print(f"\n当前北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"当前美东时间: {us_eastern_now.strftime('%Y-%m-%d %H:%M:%S')}")

# 获取CME PLV2026 最新数据
print("\n【TvDatafeed CME PLV2026 最新数据】")
cme = tv.get_hist(symbol='PLV2026', exchange='NYMEX', interval=Interval.in_1_hour, n_bars=20)
cme = cme.sort_index()

print(f"{'TvDatafeed时间':<20} | {'假设是北京时间':>20} | {'转美东时间':>20} | {'收盘价':>10}")
print("-" * 80)
for idx in cme.index[-10:]:
    row = cme.loc[idx]
    # 假设TvDatafeed返回的是北京时间
    beijing_time = idx
    us_eastern = idx - timedelta(hours=13)
    print(f"{idx.strftime('%Y-%m-%d %H:%M'):<20} | {beijing_time.strftime('%Y-%m-%d %H:%M'):>20} | {us_eastern.strftime('%Y-%m-%d %H:%M'):>20} | {row['close']:>10.2f}")

print("\n" + "=" * 80)
print("富途截图数据 (美东时间 12/26 08:04):")
print("  最新价: 2487.2")
print("  今开: 2422.7")
print("  昨收: 2302.4")
print("=" * 80)
print("\n请对比: TvDatafeed中哪个时间点的价格与富途接近?")
