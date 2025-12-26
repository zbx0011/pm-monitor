"""
生成铂金和钯金价差分析数据 - v3 分钟级版本
使用分钟级数据获取丰富的数据点
时间格式：日期+时间
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
    """生成价差数据 - 使用分钟级数据"""
    config = CONTRACTS[metal]
    print(f"\n{'='*60}")
    print(f"{config['name']}价差分析 ({config['gfex_symbol']} vs {config['cme_symbol']})")
    print(f"{'='*60}")
    
    tv = TvDatafeed()
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # 1. 获取广期所分钟数据 (60分钟周期，获取更多数据)
    print(f"\n正在获取广期所 {config['gfex_main']} 分钟数据...")
    try:
        gfex_df = ak.futures_zh_minute_sina(symbol=config['gfex_main'], period='60')
        gfex_df['datetime'] = pd.to_datetime(gfex_df['datetime'])
        gfex_df = gfex_df.set_index('datetime').sort_index()
        gfex_df = gfex_df.rename(columns={'close': 'gfex_close'})
        print(f"  ✓ 获取到 {len(gfex_df)} 条60分钟数据")
        print(f"  范围: {gfex_df.index.min().strftime('%Y-%m-%d %H:%M')} ~ {gfex_df.index.max().strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        print(f"  ✗ 广期所数据获取失败: {e}")
        return None
    
    # 2. 获取CME分钟数据 (60分钟周期)
    print(f"\n正在获取CME {config['cme_symbol']} 分钟数据...")
    try:
        cme_df = tv.get_hist(symbol=config['cme_symbol'], exchange=config['cme_exchange'], 
                            interval=Interval.in_1_hour, n_bars=500)
        if cme_df is None or len(cme_df) == 0:
            print(f"  ✗ CME数据为空")
            return None
        cme_df = cme_df.sort_index()
        cme_df['cme_cny'] = (cme_df['close'] * RATE) / OZ_TO_GRAM
        cme_df = cme_df.rename(columns={'close': 'cme_usd'})
        print(f"  ✓ 获取到 {len(cme_df)} 条60分钟数据")
        print(f"  范围: {cme_df.index.min().strftime('%Y-%m-%d %H:%M')} ~ {cme_df.index.max().strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        print(f"  ✗ CME数据获取失败: {e}")
        return None
    
    # 3. 时间对齐：对每个广期所时间点，找最近的CME价格
    history = []
    latest_cme_row = cme_df.iloc[-1]  # 最新的CME价格作为当前参考
    
    for idx, row in gfex_df.iterrows():
        gfex_price = float(row['gfex_close'])
        
        # 找最近的CME价格
        cme_before = cme_df[cme_df.index <= idx]
        if len(cme_before) > 0:
            cme_row = cme_before.iloc[-1]
            cme_time = cme_before.index[-1]
            cme_cny = float(cme_row['cme_cny'])
            cme_usd = float(cme_row['cme_usd'])
            has_both = True
        else:
            # 没有对应的CME数据，用最早的
            cme_row = cme_df.iloc[0]
            cme_time = cme_df.index[0]
            cme_cny = float(cme_row['cme_cny'])
            cme_usd = float(cme_row['cme_usd'])
            has_both = False
        
        spread = gfex_price - cme_cny
        spread_pct = (spread / cme_cny) * 100
        
        history.append({
            'date': idx.strftime('%Y-%m-%d %H:%M'),  # 完整日期+时间
            'gfex_price': gfex_price,
            'gfex_time': idx.strftime('%Y-%m-%d %H:%M'),
            'cme_usd': cme_usd,
            'cme_cny': cme_cny,
            'cme_time': cme_time.strftime('%Y-%m-%d %H:%M'),
            'spread': spread,
            'spread_pct': spread_pct,
            'spread_sge_pct': spread_pct,
            'spread_gfex_pct': spread_pct,
            'has_both': has_both
        })
    
    print(f"\n生成 {len(history)} 条价差数据")
    
    # 4. 统计
    spreads = [h['spread_pct'] for h in history]
    stats = {
        'avg_spread_pct': float(np.mean(spreads)),
        'max_spread_pct': float(np.max(spreads)),
        'min_spread_pct': float(np.min(spreads))
    }
    
    # 5. 获取最新实时数据（1分钟级别，获取真实最新时间）
    print("\n正在获取最新实时数据 (1分钟级)...")
    
    # 获取广期所最新1分钟数据
    try:
        gfex_1m = ak.futures_zh_minute_sina(symbol=config['gfex_main'], period='1')
        gfex_1m['datetime'] = pd.to_datetime(gfex_1m['datetime'])
        latest_gfex = float(gfex_1m['close'].iloc[-1])
        latest_gfex_time = gfex_1m['datetime'].iloc[-1].strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        print(f"  广期所1分钟数据获取失败: {e}")
        latest_gfex = float(gfex_df['gfex_close'].iloc[-1])
        latest_gfex_time = gfex_df.index[-1].strftime('%Y-%m-%d %H:%M')
    
    # 获取CME最新1分钟数据
    try:
        cme_1m = tv.get_hist(symbol=config['cme_symbol'], exchange=config['cme_exchange'],
                            interval=Interval.in_1_minute, n_bars=10)
        if cme_1m is not None and len(cme_1m) > 0:
            latest_cme_usd = float(cme_1m['close'].iloc[-1])
            latest_cme_time = cme_1m.index[-1].strftime('%Y-%m-%d %H:%M')
        else:
            latest_cme_usd = float(latest_cme_row['cme_usd'])
            latest_cme_time = cme_df.index[-1].strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        print(f"  CME 1分钟数据获取失败: {e}")
        latest_cme_usd = float(latest_cme_row['cme_usd'])
        latest_cme_time = cme_df.index[-1].strftime('%Y-%m-%d %H:%M')
    
    latest_cme_cny = (latest_cme_usd * RATE) / OZ_TO_GRAM
    latest_spread = latest_gfex - latest_cme_cny
    latest_spread_pct = (latest_spread / latest_cme_cny) * 100
    
    print(f"\n当前价差:")
    print(f"  广期所 {config['gfex_symbol']}: {latest_gfex:.2f} 元/克 @{latest_gfex_time}")
    print(f"  CME {config['cme_symbol']}: ${latest_cme_usd:.2f}/oz = {latest_cme_cny:.2f} 元/克 @{latest_cme_time}")
    print(f"  价差: {latest_spread:.2f} 元/克 ({latest_spread_pct:+.2f}%)")
    
    # 6. 输出
    output = {
        'update_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'contracts': {
            'gfex': config['gfex_symbol'],
            'cme': config['cme_symbol'],
            'cme_month': config['cme_month']
        },
        'current': {
            'gfex_price': latest_gfex,
            'gfex_time': latest_gfex_time,  # 完整日期+时间
            'cme_usd': latest_cme_usd,
            'cme_cny': latest_cme_cny,
            'cme_time': latest_cme_time,    # 完整日期+时间
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
    print("铂钯价差数据生成 (分钟级)")
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
    
    # 价格数据 - 用于前端和套利计算器
    if pt_data and pd_data:
        prices_data = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'exchange_rate': RATE,
            'gfex': {
                'pt_price': pt_data['current']['gfex_price'],
                'pt_time': pt_data['current']['gfex_time'],  # 完整日期+时间
                'pd_price': pd_data['current']['gfex_price'],
                'pd_time': pd_data['current']['gfex_time']   # 完整日期+时间
            },
            'cme': {
                'pt_usd': pt_data['current']['cme_usd'],
                'pt_cny': pt_data['current']['cme_cny'],
                'pt_time': pt_data['current']['cme_time'],   # 完整日期+时间
                'pt_contract': pt_data['contracts']['cme'],
                'pt_month': pt_data['contracts']['cme_month'],
                'pd_usd': pd_data['current']['cme_usd'],
                'pd_cny': pd_data['current']['cme_cny'],
                'pd_time': pd_data['current']['cme_time'],   # 完整日期+时间
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
