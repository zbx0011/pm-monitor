"""
获取国内外贵金属历史数据 - 计算跨市场价差
标的: 黄金(AU/GC)、白银(AG/SI)、铜(CU/HG)
数据源: 国内用akshare, 美国用akshare的外盘数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import akshare as ak

# 常量
OZ_TO_GRAM = 31.1035  # 盎司转克
LB_TO_TON = 2204.62   # 磅转吨
RATE = 7.04           # 汇率

def fetch_domestic_futures(symbol, name):
    """获取国内期货主力连续数据"""
    print(f"  正在获取国内 {name} ({symbol})...")
    try:
        df = ak.futures_main_sina(symbol=symbol)
        if '日期' in df.columns:
            df = df.rename(columns={'日期': 'date', '收盘价': 'close'})
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        print(f"    ✓ 获取到 {len(df)} 条数据 ({df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')})")
        return df[['close']]
    except Exception as e:
        print(f"    ✗ 获取失败: {e}")
        return pd.DataFrame()

def fetch_foreign_futures(symbol, name):
    """获取外盘期货数据 (akshare)"""
    print(f"  正在获取外盘 {name} ({symbol})...")
    try:
        df = ak.futures_foreign_hist(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        print(f"    ✓ 获取到 {len(df)} 条数据 ({df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')})")
        return df[['close']]
    except Exception as e:
        print(f"    ✗ 获取失败: {e}")
        return pd.DataFrame()

def calculate_spread(domestic_df, foreign_df, conversion_factor, name):
    """计算价差"""
    if domestic_df.empty or foreign_df.empty:
        print(f"  ⚠ {name}: 数据不完整，跳过")
        return pd.DataFrame()
    
    # 对齐日期
    merged = pd.DataFrame()
    merged['domestic'] = domestic_df['close']
    merged['foreign_usd'] = foreign_df['close'].reindex(domestic_df.index, method='ffill')
    
    # 转换为同单位 (人民币/克 或 人民币/吨)
    merged['foreign_cny'] = (merged['foreign_usd'] * RATE) / conversion_factor
    
    # 计算价差
    merged['spread'] = merged['domestic'] - merged['foreign_cny']
    merged['spread_pct'] = (merged['spread'] / merged['foreign_cny']) * 100
    
    merged = merged.dropna()
    
    print(f"  {name} 价差统计:")
    print(f"    当前: {merged['spread_pct'].iloc[-1]:.2f}%")
    print(f"    3年均值: {merged['spread_pct'].mean():.2f}%")
    print(f"    最大: {merged['spread_pct'].max():.2f}%, 最小: {merged['spread_pct'].min():.2f}%")
    
    return merged

def main():
    print("=" * 70)
    print("贵金属跨市场价差分析")
    print("国内 (上期所) vs 美国 (COMEX)")
    print("=" * 70)
    
    results = {}
    
    # 1. 黄金 AU vs XAU
    print("\n【黄金】")
    au_dom = fetch_domestic_futures('AU0', '黄金主力')
    au_for = fetch_foreign_futures('XAU', 'COMEX黄金')
    au_spread = calculate_spread(au_dom, au_for, OZ_TO_GRAM, '黄金')
    if not au_spread.empty:
        results['gold'] = au_spread
    
    # 2. 白银 AG vs XAG (注意: 国内白银是元/千克, 外盘是美元/盎司)
    print("\n【白银】")
    ag_dom = fetch_domestic_futures('AG0', '白银主力')
    ag_for = fetch_foreign_futures('XAG', 'COMEX白银')
    # 白银转换: 1千克 = 32.15盎司
    OZ_TO_KG = 32.1507
    ag_spread = calculate_spread(ag_dom, ag_for, 1/OZ_TO_KG, '白银')  # 外盘价格*32.15*汇率=元/千克
    if not ag_spread.empty:
        results['silver'] = ag_spread
    
    # 3. 铜 CU vs HG (铜比较特殊: 国内是元/吨, 美国是美分/磅)
    print("\n【铜】")
    cu_dom = fetch_domestic_futures('CU0', '铜主力')
    cu_for = fetch_foreign_futures('HG', 'COMEX铜')
    # 铜转换: 1吨 = 2204.62磅, 美国报价是美分/磅
    # 外盘价格(美分/磅) * 2204.62 / 100(美分转美元) * 汇率 = 人民币/吨
    if not cu_dom.empty and not cu_for.empty:
        cu_merged = pd.DataFrame()
        cu_merged['domestic'] = cu_dom['close']
        cu_merged['foreign_usd'] = cu_for['close'].reindex(cu_dom.index, method='ffill')
        cu_merged['foreign_cny'] = cu_merged['foreign_usd'] * LB_TO_TON / 100 * RATE
        cu_merged['spread'] = cu_merged['domestic'] - cu_merged['foreign_cny']
        cu_merged['spread_pct'] = (cu_merged['spread'] / cu_merged['foreign_cny']) * 100
        cu_merged = cu_merged.dropna()
        
        if not cu_merged.empty:
            print(f"  铜 价差统计:")
            print(f"    当前: {cu_merged['spread_pct'].iloc[-1]:.2f}%")
            print(f"    3年均值: {cu_merged['spread_pct'].mean():.2f}%")
            print(f"    最大: {cu_merged['spread_pct'].max():.2f}%, 最小: {cu_merged['spread_pct'].min():.2f}%")
            results['copper'] = cu_merged
    
    # 保存结果
    if results:
        output = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'exchange_rate': RATE,
            'commodities': {}
        }
        
        for name, df in results.items():
            # 只保留最近3年
            three_years_ago = datetime.now() - timedelta(days=365*3)
            df_recent = df[df.index >= three_years_ago]
            
            history = []
            for date, row in df_recent.iterrows():
                history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'domestic': float(row['domestic']),
                    'foreign_cny': float(row['foreign_cny']),
                    'spread_pct': float(row['spread_pct'])
                })
            
            output['commodities'][name] = {
                'current_spread_pct': float(df['spread_pct'].iloc[-1]),
                'avg_spread_pct': float(df_recent['spread_pct'].mean()),
                'max_spread_pct': float(df_recent['spread_pct'].max()),
                'min_spread_pct': float(df_recent['spread_pct'].min()),
                'history': history
            }
        
        with open('precious_metals_spread_history.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 数据已保存到 precious_metals_spread_history.json")
    else:
        print("\n✗ 未能获取任何数据")

if __name__ == "__main__":
    main()
