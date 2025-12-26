"""
生成铂金和钯金价差分析数据 - 改进版
使用日频数据获取更长历史，正确匹配时间
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import akshare as ak

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval

OZ_TO_GRAM = 31.1035
RATE = 7.04

# 合约配置
CONTRACTS = {
    'platinum': {
        'gfex_symbol': 'PT2610',
        'gfex_main': 'PT0',
        'cme_symbol': 'PLV2026',
        'cme_month': '2026年10月',
        'cme_exchange': 'NYMEX',
        'name': '铂金'
    },
    'palladium': {
        'gfex_symbol': 'PD2606',
        'gfex_main': 'PD0',
        'cme_symbol': 'PAM2026',
        'cme_month': '2026年6月',
        'cme_exchange': 'NYMEX',
        'name': '钯金'
    }
}


def generate_spread_data(metal='platinum'):
    """生成价差数据"""
    config = CONTRACTS[metal]
    print(f"\n{'='*60}")
    print(f"{config['name']}价差分析 ({config['gfex_symbol']} vs {config['cme_symbol']})")
    print(f"{'='*60}")
    
    # 1. 获取广期所日频数据
    print(f"\n正在获取广期所 {config['gfex_main']} 日频数据...")
    try:
        gfex_df = ak.futures_main_sina(symbol=config['gfex_main'])
        gfex_df['日期'] = pd.to_datetime(gfex_df['日期'])
        gfex_df = gfex_df.set_index('日期').sort_index()
        gfex_df = gfex_df.rename(columns={'收盘价': 'gfex_close'})
        print(f"  ✓ 获取到 {len(gfex_df)} 条日频数据")
        print(f"  范围: {gfex_df.index.min().strftime('%Y-%m-%d')} ~ {gfex_df.index.max().strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"  ✗ 广期所数据获取失败: {e}")
        return None
    
    # 2. 获取CME日频数据
    print(f"\n正在获取CME {config['cme_symbol']} 日频数据...")
    try:
        tv = TvDatafeed()
        cme_df = tv.get_hist(symbol=config['cme_symbol'], exchange=config['cme_exchange'], 
                            interval=Interval.in_daily, n_bars=100)
        if cme_df is None or len(cme_df) == 0:
            print(f"  ✗ CME数据为空")
            return None
        cme_df = cme_df.sort_index()
        cme_df['cme_cny'] = (cme_df['close'] * RATE) / OZ_TO_GRAM
        print(f"  ✓ 获取到 {len(cme_df)} 条日频数据")
        print(f"  范围: {cme_df.index.min().strftime('%Y-%m-%d')} ~ {cme_df.index.max().strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"  ✗ CME数据获取失败: {e}")
        return None
    
    # 3. 按日期合并 (只保留两边都有数据的日期)
    # 标准化日期为只有日期部分
    gfex_daily = gfex_df[['gfex_close']].copy()
    gfex_daily.index = gfex_daily.index.normalize()
    
    cme_daily = cme_df[['close', 'cme_cny']].copy()
    cme_daily = cme_daily.rename(columns={'close': 'cme_usd'})
    cme_daily.index = cme_daily.index.normalize()
    
    # 合并
    merged = pd.merge(gfex_daily, cme_daily, left_index=True, right_index=True, how='inner')
    print(f"\n合并后: {len(merged)} 个交易日 (两边都有数据)")
    
    if len(merged) == 0:
        print("  ✗ 没有匹配的交易日")
        return None
    
    # 4. 计算价差
    merged['spread'] = merged['gfex_close'] - merged['cme_cny']
    merged['spread_pct'] = (merged['spread'] / merged['cme_cny']) * 100
    
    # 5. 生成历史数据
    history = []
    for idx, row in merged.iterrows():
        # 标记是否只有一边有数据
        has_both = True  # 因为是inner join，都有
        
        history.append({
            'date': idx.strftime('%Y-%m-%d'),
            'sge_price': float(row['gfex_close']),
            'gfex_price': float(row['gfex_close']),
            'cme_usd': float(row['cme_usd']),
            'cme_cny': float(row['cme_cny']),
            'spread': float(row['spread']),
            'spread_pct': float(row['spread_pct']),
            'spread_sge_pct': float(row['spread_pct']),
            'spread_gfex_pct': float(row['spread_pct']),
            'has_both': has_both
        })
    
    # 6. 统计
    spreads = merged['spread_pct'].values
    latest = history[-1] if history else {}
    
    stats = {
        'avg_spread_pct': float(np.mean(spreads)),
        'max_spread_pct': float(np.max(spreads)),
        'min_spread_pct': float(np.min(spreads))
    }
    
    # 7. 获取最新实时数据（分钟级）
    print("\n正在获取最新实时数据...")
    try:
        gfex_min = ak.futures_zh_minute_sina(symbol=config['gfex_main'], period='1')
        latest_gfex = float(gfex_min['close'].iloc[-1])
        latest_gfex_time = pd.to_datetime(gfex_min['datetime'].iloc[-1]).strftime('%H:%M')
    except:
        latest_gfex = float(merged['gfex_close'].iloc[-1])
        latest_gfex_time = "收盘"
    
    try:
        cme_min = tv.get_hist(symbol=config['cme_symbol'], exchange=config['cme_exchange'],
                             interval=Interval.in_1_minute, n_bars=10)
        if cme_min is not None and len(cme_min) > 0:
            latest_cme_usd = float(cme_min['close'].iloc[-1])
            latest_cme_time = cme_min.index[-1].strftime('%H:%M')
        else:
            latest_cme_usd = float(merged['cme_usd'].iloc[-1])
            latest_cme_time = "收盘"
    except:
        latest_cme_usd = float(merged['cme_usd'].iloc[-1])
        latest_cme_time = "收盘"
    
    latest_cme_cny = (latest_cme_usd * RATE) / OZ_TO_GRAM
    latest_spread = latest_gfex - latest_cme_cny
    latest_spread_pct = (latest_spread / latest_cme_cny) * 100
    
    print(f"  广期所 {config['gfex_symbol']}: {latest_gfex:.2f} 元/克 @{latest_gfex_time}")
    print(f"  CME {config['cme_symbol']}: ${latest_cme_usd:.2f}/oz = {latest_cme_cny:.2f} 元/克 @{latest_cme_time}")
    print(f"  价差: {latest_spread:.2f} 元/克 ({latest_spread_pct:+.2f}%)")
    
    # 8. 输出
    output = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'contracts': {
            'gfex': config['gfex_symbol'],
            'cme': config['cme_symbol'],
            'cme_month': config['cme_month']
        },
        'current': {
            'gfex_price': latest_gfex,
            'gfex_time': latest_gfex_time,
            'cme_usd': latest_cme_usd,
            'cme_cny': latest_cme_cny,
            'cme_time': latest_cme_time,
            'spread': latest_spread,
            'spread_pct': latest_spread_pct,
            'spread_gfex_pct': latest_spread_pct,
            'spread_sge_pct': latest_spread_pct
        },
        'stats_3y_sge': stats,
        'history': history
    }
    
    return output


def main():
    print("=" * 60)
    print("铂钯价差数据生成 (日频)")
    print("=" * 60)
    
    # 铂金
    pt_data = generate_spread_data('platinum')
    if pt_data:
        with open('platinum_spread_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(pt_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ platinum_spread_analysis.json ({len(pt_data['history'])} 条)")
    
    # 钯金
    pd_data = generate_spread_data('palladium')
    if pd_data:
        with open('palladium_spread_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(pd_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ palladium_spread_analysis.json ({len(pd_data['history'])} 条)")
    
    # 价格数据
    if pt_data and pd_data:
        prices_data = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'exchange_rate': RATE,
            'gfex': {
                'pt_price': pt_data['current']['gfex_price'],
                'pt_time': pt_data['current']['gfex_time'],
                'pd_price': pd_data['current']['gfex_price'],
                'pd_time': pd_data['current']['gfex_time']
            },
            'cme': {
                'pt_usd': pt_data['current']['cme_usd'],
                'pt_cny': pt_data['current']['cme_cny'],
                'pt_time': pt_data['current']['cme_time'],
                'pt_contract': pt_data['contracts']['cme'],
                'pt_month': pt_data['contracts']['cme_month'],
                'pd_usd': pd_data['current']['cme_usd'],
                'pd_cny': pd_data['current']['cme_cny'],
                'pd_time': pd_data['current']['cme_time'],
                'pd_contract': pd_data['contracts']['cme'],
                'pd_month': pd_data['contracts']['cme_month']
            },
            'spread': {
                'pt_spread': pt_data['current']['spread'],
                'pt_spread_pct': pt_data['current']['spread_pct'],
                'pd_spread': pd_data['current']['spread'],
                'pd_spread_pct': pd_data['current']['spread_pct']
            }
        }
        with open('prices_data.json', 'w', encoding='utf-8') as f:
            json.dump(prices_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ prices_data.json 已更新")


if __name__ == "__main__":
    main()
