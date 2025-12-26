"""
验证收敛分析数据的正确性
抽查几个日期的价差计算
"""
import akshare as ak
import pandas as pd

OZ_TO_GRAM = 31.1035
RATE = 7.04

print("="*60)
print("数据验证: AU2412 特定日期价差核对")
print("="*60)

# 获取AU2412数据
au = ak.futures_zh_daily_sina(symbol='AU2412')
au['date'] = pd.to_datetime(au['date'])
au = au.set_index('date').sort_index()
au['close'] = pd.to_numeric(au['close'], errors='coerce')

# 获取XAU数据
xau = ak.futures_foreign_hist(symbol='XAU')
xau['date'] = pd.to_datetime(xau['date'])
xau = xau.set_index('date').sort_index()
xau['close'] = pd.to_numeric(xau['close'], errors='coerce')

# 选几个关键日期验证
test_dates = ['2024-01-15', '2024-06-03', '2024-12-10']

print("\n【AU2412 vs XAU 价差验证】")
for d in test_dates:
    try:
        d = pd.Timestamp(d)
        au_price = float(au.loc[d, 'close'])
        xau_price = float(xau.loc[d, 'close'])
        xau_cny = (xau_price * RATE) / OZ_TO_GRAM
        spread = ((au_price - xau_cny) / xau_cny) * 100
        
        print(f"\n日期: {d.strftime('%Y-%m-%d')}")
        print(f"  AU2412: {au_price:.2f} 元/克")
        print(f"  XAU: ${xau_price:.2f}/oz -> {xau_cny:.2f} 元/克 (汇率{RATE})")
        print(f"  价差: {spread:.2f}%")
    except Exception as e:
        print(f"\n{d}: 数据缺失 - {e}")

# 验证白银
print("\n" + "="*60)
print("数据验证: AG2412 价差核对")
print("="*60)

ag = ak.futures_zh_daily_sina(symbol='AG2412')
ag['date'] = pd.to_datetime(ag['date'])
ag = ag.set_index('date').sort_index()
ag['close'] = pd.to_numeric(ag['close'], errors='coerce')

xag = ak.futures_foreign_hist(symbol='XAG')
xag['date'] = pd.to_datetime(xag['date'])
xag = xag.set_index('date').sort_index()
xag['close'] = pd.to_numeric(xag['close'], errors='coerce')

# 白银单位: 国内=元/千克, 国际=美元/盎司
# 转换: 1千克 = 32.1507盎司
OZ_PER_KG = 32.1507

test_dates_ag = ['2024-06-03', '2024-12-10']

print("\n【AG2412 vs XAG 价差验证】")
for d in test_dates_ag:
    try:
        d = pd.Timestamp(d)
        ag_price = float(ag.loc[d, 'close'])  # 元/千克
        xag_price = float(xag.loc[d, 'close'])  # 美元/盎司
        xag_cny = xag_price * OZ_PER_KG * RATE  # 转换为 元/千克
        spread = ((ag_price - xag_cny) / xag_cny) * 100
        
        print(f"\n日期: {d.strftime('%Y-%m-%d')}")
        print(f"  AG2412: {ag_price:.2f} 元/千克")
        print(f"  XAG: ${xag_price:.2f}/oz -> {xag_cny:.2f} 元/千克 (汇率{RATE})")
        print(f"  价差: {spread:.2f}%")
    except Exception as e:
        print(f"\n{d}: 数据缺失 - {e}")
