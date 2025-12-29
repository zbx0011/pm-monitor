"""检查TvDatafeed获取的CME合约数据"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

print("=" * 60)
print("检查 PLJ2026 (铂金 2026年4月) 分钟数据")
print("=" * 60)

try:
    # 获取最新的分钟数据
    df = tv.get_hist(symbol='PLJ2026', exchange='NYMEX', interval=Interval.in_1_minute, n_bars=10)
    
    if df is not None and len(df) > 0:
        print(f"{'时间':<20} | {'收盘价(USD/oz)':>15} | {'High':>10} | {'Low':>10}")
        print("-" * 65)
        for idx, row in df.tail(10).iterrows():
            print(f"{idx.strftime('%Y-%m-%d %H:%M'):<20} | {row['close']:>15.2f} | {row['high']:>10.2f} | {row['low']:>10.2f}")
        
        last_price = df.iloc[-1]['close']
        print(f"\n最新价格: {last_price}")
        print(f"用户报告价格: 2385.1")
        print(f"差异: {last_price - 2385.1:.2f}")
    else:
        print("未获取到数据")
except Exception as e:
    print(f"获取失败: {e}")

print("\n" + "=" * 60)
