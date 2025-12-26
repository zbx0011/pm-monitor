"""
分析特定交割合约的价差收敛情况
以 AU2412（2024年12月交割）为例
"""
import akshare as ak
import pandas as pd
from datetime import datetime

OZ_TO_GRAM = 31.1035
RATE = 7.04

print("=" * 60)
print("特定合约价差收敛分析")
print("=" * 60)

# 获取AU2412（2024年12月交割）的历史数据
print("\n正在获取 AU2412 数据...")
au2412 = ak.futures_zh_daily_sina(symbol='AU2412')
print(f"  数据范围: {au2412['date'].min()} ~ {au2412['date'].max()} ({len(au2412)}条)")

# 获取同期国际金价
print("正在获取国际金价...")
xau = ak.futures_foreign_hist(symbol='XAU')
xau['date'] = pd.to_datetime(xau['date'])
xau = xau.set_index('date')
xau['close'] = pd.to_numeric(xau['close'], errors='coerce')

# 合并计算价差
au2412['date'] = pd.to_datetime(au2412['date'])
au2412 = au2412.set_index('date')
au2412['close'] = pd.to_numeric(au2412['close'], errors='coerce')
au2412['xau_cny'] = (xau['close'].reindex(au2412.index, method='ffill') * RATE) / OZ_TO_GRAM
au2412['spread_pct'] = ((au2412['close'] - au2412['xau_cny']) / au2412['xau_cny']) * 100
au2412 = au2412.dropna(subset=['spread_pct'])

print(f"\n{'='*60}")
print("AU2412 价差走势 (合约生命周期)")
print(f"{'='*60}")

# 分阶段统计
print(f"\n上市初期 (前30天):")
early = au2412.head(30)
print(f"  平均价差: {early['spread_pct'].mean():.2f}%")
print(f"  范围: {early['spread_pct'].min():.2f}% ~ {early['spread_pct'].max():.2f}%")

print(f"\n中期 (上市后30-180天):")
mid = au2412.iloc[30:180] if len(au2412) > 180 else au2412.iloc[30:]
if len(mid) > 0:
    print(f"  平均价差: {mid['spread_pct'].mean():.2f}%")
    print(f"  范围: {mid['spread_pct'].min():.2f}% ~ {mid['spread_pct'].max():.2f}%")

print(f"\n临近交割 (最后30天):")
late = au2412.tail(30)
print(f"  平均价差: {late['spread_pct'].mean():.2f}%")
print(f"  范围: {late['spread_pct'].min():.2f}% ~ {late['spread_pct'].max():.2f}%")

print(f"\n最后交易日:")
last = au2412.tail(1)
print(f"  日期: {last.index[0].strftime('%Y-%m-%d')}")
print(f"  价差: {last['spread_pct'].values[0]:.2f}%")

print(f"\n{'='*60}")
print("结论: 价差是否收敛?")
print(f"{'='*60}")
start_spread = au2412['spread_pct'].iloc[0]
end_spread = au2412['spread_pct'].iloc[-1]
print(f"  上市时价差: {start_spread:.2f}%")
print(f"  交割时价差: {end_spread:.2f}%")
print(f"  收敛幅度: {start_spread - end_spread:.2f}个百分点")
