"""
铂金历史价差走势图 (近3年)
SGE铂金 vs CME铂金(XPT)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

try:
    import akshare as ak
except ImportError:
    print("请安装akshare: pip install akshare")
    exit(1)

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    print("请安装matplotlib: pip install matplotlib")
    exit(1)


def main():
    print("=" * 70)
    print("铂金历史价差走势图 (近3年)")
    print("SGE Pt99.95 vs CME XPT")
    print("=" * 70)
    print()
    
    OZ_TO_GRAM = 31.1035
    RATE = 7.04  # 平均汇率
    
    # 1. 获取SGE铂金数据
    print("正在获取SGE铂金(Pt99.95)数据...")
    try:
        sge_df = ak.spot_hist_sge(symbol="Pt99.95")
        print(f"  ✓ 获取到 {len(sge_df)} 条SGE铂金数据")
    except Exception as e:
        print(f"  ✗ SGE铂金获取失败: {e}")
        return
    
    # 处理SGE数据
    sge_df['date'] = pd.to_datetime(sge_df['date'])
    sge_df = sge_df.set_index('date')
    sge_df = sge_df.sort_index()
    sge_df['close'] = pd.to_numeric(sge_df['close'], errors='coerce')
    sge_df = sge_df[sge_df['close'] > 0]
    
    # 2. 获取CME铂金数据 (使用XPT代码)
    print("\n正在获取CME铂金(XPT)数据...")
    try:
        cme_df = ak.futures_foreign_hist(symbol="XPT")
        print(f"  ✓ 获取到 {len(cme_df)} 条CME铂金数据")
    except Exception as e:
        print(f"  ✗ CME铂金获取失败: {e}")
        return
    
    # 处理CME数据
    cme_df['date'] = pd.to_datetime(cme_df['date'])
    cme_df = cme_df.set_index('date')
    cme_df = cme_df.sort_index()
    cme_df['close'] = pd.to_numeric(cme_df['close'], errors='coerce')
    cme_df['cny_per_gram'] = (cme_df['close'] * RATE) / OZ_TO_GRAM
    
    # 只保留最近3年
    three_years_ago = datetime.now() - timedelta(days=365*3)
    sge_df = sge_df[sge_df.index >= three_years_ago]
    cme_df = cme_df[cme_df.index >= three_years_ago]
    
    print(f"\n数据范围:")
    print(f"  SGE: {sge_df.index.min().strftime('%Y-%m-%d')} ~ {sge_df.index.max().strftime('%Y-%m-%d')} ({len(sge_df)}条)")
    print(f"  CME: {cme_df.index.min().strftime('%Y-%m-%d')} ~ {cme_df.index.max().strftime('%Y-%m-%d')} ({len(cme_df)}条)")
    
    # 2.5 获取广期所铂金数据 (PT0)
    print("\n正在获取广期所铂金(PT0)数据...")
    try:
        gfex_df = ak.futures_main_sina(symbol='PT0')
        # 处理可能的列名差异
        if '日期' in gfex_df.columns:
            gfex_df = gfex_df.rename(columns={'日期': 'date', '收盘价': 'close'})
        gfex_df['date'] = pd.to_datetime(gfex_df['date'])
        gfex_df = gfex_df.set_index('date')
        gfex_df = gfex_df.sort_index()
        gfex_df['close'] = pd.to_numeric(gfex_df['close'], errors='coerce')
        print(f"  ✓ 获取到 {len(gfex_df)} 条广期所铂金数据 ({gfex_df.index.min().strftime('%Y-%m-%d')} ~ {gfex_df.index.max().strftime('%Y-%m-%d')})")
    except Exception as e:
        print(f"  ✗ 广期所铂金获取失败: {e}")
        gfex_df = pd.DataFrame()

    # 3. 合并数据计算价差
    merged = pd.DataFrame()
    merged['sge'] = sge_df['close']
    merged['cme_cny'] = cme_df['cny_per_gram'].reindex(sge_df.index, method='ffill')
    merged['cme_usd'] = cme_df['close'].reindex(sge_df.index, method='ffill')
    
    # 合并广期所数据
    if not gfex_df.empty:
        merged['gfex'] = gfex_df['close'].reindex(sge_df.index)
    else:
        merged['gfex'] = np.nan
        
    merged = merged.dropna(subset=['sge', 'cme_cny'])  # 只要SGE和CME有的都保留
    
    # 优先计算广期所价差(如果有)，否则计算SGE价差
    # 这里我们保留两个价差
    merged['spread_sge'] = merged['sge'] - merged['cme_cny']
    merged['spread_sge_pct'] = (merged['spread_sge'] / merged['cme_cny']) * 100
    
    merged['spread_gfex'] = merged['gfex'] - merged['cme_cny']
    merged['spread_gfex_pct'] = (merged['spread_gfex'] / merged['cme_cny']) * 100
    
    # 默认spread字段优先使用GFEX，如果没有则用SGE (为了兼容旧逻辑，但最好前端区分)
    # 实际上由于GFEX数据太短，我们主要还是看SGE的历史，但重点展示GFEX的近期
    
    print(f"\n最新数据 ({merged.index[-1].strftime('%Y-%m-%d')}):")
    print(f"  SGE: {merged['sge'].iloc[-1]:.2f}, 溢价: {merged['spread_sge_pct'].iloc[-1]:.2f}%")
    if pd.notna(merged['gfex'].iloc[-1]):
        print(f"  GFEX: {merged['gfex'].iloc[-1]:.2f}, 溢价: {merged['spread_gfex_pct'].iloc[-1]:.2f}%")
    
    # ... (原有绘图代码略，重点是JSON输出) ...

    # 输出JSON
    history_list = []
    for date, row in merged.iterrows():
        item = {
            'date': date.strftime('%Y-%m-%d'),
            'sge': float(f"{row['sge']:.2f}"),
            'cme_cny': float(f"{row['cme_cny']:.2f}"),
            # SGE溢价
            'spread_sge': float(f"{row['spread_sge']:.2f}"),
            'spread_sge_pct': float(f"{row['spread_sge_pct']:.2f}")
        }
        # 如果有广期所数据
        if pd.notna(row['gfex']):
            item['gfex'] = float(f"{row['gfex']:.2f}")
            item['spread_gfex'] = float(f"{row['spread_gfex']:.2f}")
            item['spread_gfex_pct'] = float(f"{row['spread_gfex_pct']:.2f}")
        else:
            item['gfex'] = None
            item['spread_gfex'] = None
            item['spread_gfex_pct'] = None
            
        history_list.append(item)

    # 统计数据：主要基于SGE (因为GFEX太短)
    summary = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'current': {
            'sge': float(merged['sge'].iloc[-1]),
            'gfex': float(merged['gfex'].iloc[-1]) if pd.notna(merged['gfex'].iloc[-1]) else None,
            'cme_cny': float(merged['cme_cny'].iloc[-1]),
            'cme_usd': float(merged['cme_usd'].iloc[-1]),
            'spread_sge': float(merged['spread_sge'].iloc[-1]),
            'spread_sge_pct': float(merged['spread_sge_pct'].iloc[-1]),
            'spread_gfex_pct': float(merged['spread_gfex_pct'].iloc[-1]) if pd.notna(merged['spread_gfex_pct'].iloc[-1]) else None
        },
        'stats_3y_sge': {
            'avg_spread_pct': float(merged['spread_sge_pct'].mean()),
            'max_spread_pct': float(merged['spread_sge_pct'].max()),
            'min_spread_pct': float(merged['spread_sge_pct'].min())
        },
        'history': history_list
    }
    
    with open('platinum_spread_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✓ 分析结果已保存到 platinum_spread_analysis.json (包含 {len(history_list)} 条历史记录)")
    
    # 年度统计
    print("\n" + "=" * 70)
    print("年度价差统计 (SGE)")
    print("=" * 70)
    
    # 按年份统计
    merged['year'] = merged.index.year
    years = merged['year'].unique()
    
    for year in years:
        year_data = merged[merged['year'] == year]
        print(f"{year}: 均价差 {year_data['spread_sge'].mean():+.2f} ({year_data['spread_sge_pct'].mean():+.2f}%), "
              f"最大 {year_data['spread_sge'].max():+.2f} ({year_data['spread_sge_pct'].max():+.2f}%), "
              f"最小 {year_data['spread_sge'].min():+.2f} ({year_data['spread_sge_pct'].min():+.2f}%)")
    
    plt.close()  # 关闭图表窗口避免阻塞


if __name__ == "__main__":
    main()
