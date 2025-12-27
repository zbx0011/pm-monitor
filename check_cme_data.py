"""检查TvDatafeed获取的CME合约数据"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

print("=" * 60)
print("检查CME合约数据 (TvDatafeed)")
print("=" * 60)

# 铂金 PLV2026
print("\n【CME铂金 PLV2026 (NYMEX)】")
try:
    df = tv.get_hist(symbol='PLV2026', exchange='NYMEX', interval=Interval.in_daily, n_bars=5)
    if df is not None and len(df) > 0:
        print(f"{'日期':<12} | {'收盘价(USD/oz)':>15}")
        print("-" * 30)
        for idx, row in df.tail(5).iterrows():
            print(f"{idx.strftime('%Y-%m-%d'):<12} | {row['close']:>15.2f}")
    else:
        print("无数据")
except Exception as e:
    print(f"获取失败: {e}")

# 钯金 PAM2026
print("\n【CME钯金 PAM2026 (NYMEX)】")
try:
    df = tv.get_hist(symbol='PAM2026', exchange='NYMEX', interval=Interval.in_daily, n_bars=5)
    if df is not None and len(df) > 0:
        print(f"{'日期':<12} | {'收盘价(USD/oz)':>15}")
        print("-" * 30)
        for idx, row in df.tail(5).iterrows():
            print(f"{idx.strftime('%Y-%m-%d'):<12} | {row['close']:>15.2f}")
    else:
        print("无数据")
except Exception as e:
    print(f"获取失败: {e}")

print("\n" + "=" * 60)
