"""
生成钯金历史价差分析数据 (广期所 vs CME)
使用CME钯金历史价格计算真实价差
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import akshare as ak

OZ_TO_GRAM = 31.1035
RATE = 7.04  # USD/CNY汇率


def main():
    print("=" * 60)
    print("钯金历史价差分析 (广期所 vs CME)")
    print("=" * 60)
    print()
    
    # 1. 获取广期所钯金主力数据
    print("正在获取广期所钯金(PD)主力数据...")
    try:
        gfex_df = ak.futures_main_sina(symbol='PD0')
        print(f"  ✓ 获取到 {len(gfex_df)} 条广期所钯金数据")
    except Exception as e:
        print(f"  ✗ 广期所钯金获取失败: {e}")
        return
    
    # 处理广期所数据
    gfex_df['日期'] = pd.to_datetime(gfex_df['日期'])
    gfex_df = gfex_df.set_index('日期')
    gfex_df = gfex_df.sort_index()
    gfex_df = gfex_df.rename(columns={'收盘价': 'gfex_close'})
    
    print(f"  广期所范围: {gfex_df.index.min().strftime('%Y-%m-%d')} ~ {gfex_df.index.max().strftime('%Y-%m-%d')}")
    
    # 2. 获取CME钯金历史数据
    print("\n正在获取CME钯金(XPD)历史数据...")
    try:
        cme_df = ak.futures_foreign_hist(symbol='XPD')
        print(f"  ✓ 获取到 {len(cme_df)} 条CME钯金数据")
    except Exception as e:
        print(f"  ✗ CME钯金获取失败: {e}")
        return
    
    # 处理CME数据
    cme_df['date'] = pd.to_datetime(cme_df['date'])
    cme_df = cme_df.set_index('date')
    cme_df = cme_df.sort_index()
    cme_df['close'] = pd.to_numeric(cme_df['close'], errors='coerce')
    cme_df['cme_cny'] = (cme_df['close'] * RATE) / OZ_TO_GRAM  # 换算成 元/克
    
    print(f"  CME范围: {cme_df.index.min().strftime('%Y-%m-%d')} ~ {cme_df.index.max().strftime('%Y-%m-%d')}")
    
    # 3. 合并数据 - 只保留两边市场同时有数据的日期
    merged = pd.merge(
        gfex_df[['gfex_close']],
        cme_df[['close', 'cme_cny']].rename(columns={'close': 'cme_usd'}),
        left_index=True, right_index=True, how='inner'  # 只保留同时有数据的日期
    )
    
    merged = merged.dropna()
    
    print(f"\n合并后数据: {len(merged)} 条 (同时交易日)")
    
    # 4. 计算价差
    merged['spread'] = merged['gfex_close'] - merged['cme_cny']
    merged['spread_pct'] = (merged['spread'] / merged['cme_cny']) * 100
    
    # 5. 生成历史数据
    history = []
    for idx, row in merged.iterrows():
        history.append({
            'date': idx.strftime('%Y-%m-%d'),
            'sge_price': float(row['gfex_close']),  # 使用gfex作为国内价格
            'cme_usd': float(row['cme_usd']),
            'cme_cny': float(row['cme_cny']),
            'spread_sge': float(row['spread']),
            'spread_sge_pct': float(row['spread_pct']),
            'spread_gfex_pct': float(row['spread_pct'])  # 兼容前端
        })
    
    # 6. 统计
    spreads = merged['spread_pct'].values
    stats = {
        'avg_spread_pct': float(np.mean(spreads)),
        'max_spread_pct': float(np.max(spreads)),
        'min_spread_pct': float(np.min(spreads))
    }
    
    latest = history[-1] if history else {}
    
    # 7. 输出JSON
    output = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'current': {
            'sge_price': latest.get('sge_price', 0),
            'cme_cny': latest.get('cme_cny', 0),
            'spread_sge': latest.get('spread_sge', 0),
            'spread_sge_pct': latest.get('spread_sge_pct', 0),
            'spread_gfex_pct': latest.get('spread_gfex_pct', 0)
        },
        'stats_3y_sge': stats,
        'history': history
    }
    
    with open('palladium_spread_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 已生成 palladium_spread_analysis.json ({len(history)} 条记录)")
    print(f"  当前价差: {latest.get('spread_gfex_pct', 0):.2f}%")
    print(f"  历史均值: {stats['avg_spread_pct']:.2f}%")
    print(f"  历史最高: {stats['max_spread_pct']:.2f}%")
    print(f"  历史最低: {stats['min_spread_pct']:.2f}%")


if __name__ == "__main__":
    main()
