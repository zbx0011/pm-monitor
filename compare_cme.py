"""对比CME PA2606数据 - 用户截图 vs TvDatafeed"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

print("=" * 70)
print("CME钯金合约数据对比")
print("=" * 70)

# 用户截图数据 (PA2606 = 钯金2606)
print("\n【用户截图数据 - PA2606 2025/12/24】")
print("  开盘: 2011.0")
print("  最高: 2082.5")
print("  收盘: 1844.0")
print("  最低: 1787.5")

# TvDatafeed 获取 PAM2026 (同样是2026年6月到期的钯金合约)
print("\n【TvDatafeed数据 - PAM2026】")
try:
    df = tv.get_hist(symbol='PAM2026', exchange='NYMEX', interval=Interval.in_daily, n_bars=10)
    if df is not None and len(df) > 0:
        print(f"{'日期':<12} | {'开盘':>10} | {'最高':>10} | {'收盘':>10} | {'最低':>10}")
        print("-" * 60)
        for idx, row in df.tail(5).iterrows():
            print(f"{idx.strftime('%Y-%m-%d'):<12} | {row['open']:>10.2f} | {row['high']:>10.2f} | {row['close']:>10.2f} | {row['low']:>10.2f}")
except Exception as e:
    print(f"获取失败: {e}")

# 也尝试获取 PA2606 代码
print("\n【TvDatafeed数据 - PA2606 (尝试)】")
try:
    df = tv.get_hist(symbol='PA2606', exchange='NYMEX', interval=Interval.in_daily, n_bars=10)
    if df is not None and len(df) > 0:
        print(f"{'日期':<12} | {'开盘':>10} | {'最高':>10} | {'收盘':>10} | {'最低':>10}")
        print("-" * 60)
        for idx, row in df.tail(5).iterrows():
            print(f"{idx.strftime('%Y-%m-%d'):<12} | {row['open']:>10.2f} | {row['high']:>10.2f} | {row['close']:>10.2f} | {row['low']:>10.2f}")
    else:
        print("无数据")
except Exception as e:
    print(f"获取失败: {e}")

print("\n" + "=" * 70)
