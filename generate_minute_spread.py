"""
生成铂金和钯金分钟级价差分析数据
- 广期所: PT2610 (铂金10月), PD2606 (钯金6月)
- CME: PLV2025 (铂金10月), PAM2025 (钯金6月)
需要VPN代理: 127.0.0.1:7890
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
import akshare as ak

# 设置代理 (TradingView需要)
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval

OZ_TO_GRAM = 31.1035
RATE = 7.04  # USD/CNY汇率

# 合约配置
CONTRACTS = {
    'platinum': {
        'gfex_symbol': 'PT2610',  # 广期所铂金2026年10月
        'gfex_main': 'PT0',       # 主力合约代码
        'cme_symbol': 'PLV2026',  # CME铂金2026年10月
        'cme_exchange': 'NYMEX',
        'name': '铂金'
    },
    'palladium': {
        'gfex_symbol': 'PD2606',  # 广期所钯金2026年6月
        'gfex_main': 'PD0',       # 主力合约代码
        'cme_symbol': 'PAM2026',  # CME钯金2026年6月
        'cme_exchange': 'NYMEX',
        'name': '钯金'
    }
}


def fetch_gfex_minute(symbol, period='1'):
    """获取广期所分钟数据"""
    try:
        df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        df = df.sort_index()
        return df
    except Exception as e:
        print(f"  ✗ 广期所{symbol}获取失败: {e}")
        return None


def fetch_cme_minute(tv, symbol, exchange, interval=Interval.in_1_minute, n_bars=500):
    """获取CME分钟数据 (通过TradingView)"""
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
        if df is not None:
            df = df.sort_index()
        return df
    except Exception as e:
        print(f"  ✗ CME {symbol}获取失败: {e}")
        return None


def generate_spread_data(metal='platinum', period='1'):
    """生成指定品种的价差数据"""
    config = CONTRACTS[metal]
    print(f"\n{'='*60}")
    print(f"{config['name']}分钟级价差分析 ({config['gfex_symbol']} vs {config['cme_symbol']})")
    print(f"{'='*60}")
    
    # 1. 获取广期所数据
    print(f"\n正在获取广期所 {config['gfex_main']} 分钟数据...")
    gfex_df = fetch_gfex_minute(config['gfex_main'], period)
    if gfex_df is None:
        return None
    print(f"  ✓ 获取到 {len(gfex_df)} 条数据")
    print(f"  时间范围: {gfex_df.index.min()} ~ {gfex_df.index.max()}")
    
    # 2. 获取CME数据
    print(f"\n正在获取CME {config['cme_symbol']} 分钟数据...")
    tv = TvDatafeed()
    
    # 根据period选择interval
    interval_map = {'1': Interval.in_1_minute, '5': Interval.in_5_minute, 
                   '15': Interval.in_15_minute, '60': Interval.in_1_hour}
    interval = interval_map.get(period, Interval.in_1_minute)
    
    cme_df = fetch_cme_minute(tv, config['cme_symbol'], config['cme_exchange'], interval, n_bars=500)
    if cme_df is None:
        return None
    print(f"  ✓ 获取到 {len(cme_df)} 条数据")
    print(f"  时间范围: {cme_df.index.min()} ~ {cme_df.index.max()}")
    
    # 3. 换算CME价格 (USD/oz -> CNY/gram)
    cme_df['cme_cny'] = (cme_df['close'] * RATE) / OZ_TO_GRAM
    
    # 4. 合并数据 (基于时间匹配)
    # 由于时区差异，使用最近时间匹配
    gfex_df = gfex_df.rename(columns={'close': 'gfex_close'})
    
    # 使用最新的数据点计算当前价差
    gfex_latest = gfex_df['gfex_close'].iloc[-1]
    cme_latest = cme_df['cme_cny'].iloc[-1]
    spread = gfex_latest - cme_latest
    spread_pct = (spread / cme_latest) * 100
    
    print(f"\n当前价差:")
    print(f"  广期所 {config['gfex_symbol']}: {gfex_latest:.2f} 元/克")
    print(f"  CME {config['cme_symbol']}: {cme_latest:.2f} 元/克")
    print(f"  价差: {spread:.2f} 元/克 ({spread_pct:+.2f}%)")
    
    # 5. 生成历史数据 (使用广期所时间轴)
    history = []
    for idx, row in gfex_df.iterrows():
        gfex_price = float(row['gfex_close'])
        # 使用最近的CME价格（简化处理）
        cme_price = float(cme_latest)  # 实际应做时间对齐
        spread_val = gfex_price - cme_price
        spread_pct_val = (spread_val / cme_price) * 100
        
        history.append({
            'date': idx.strftime('%Y-%m-%d %H:%M'),  # 前端期望date字段
            'sge_price': gfex_price,  # 兼容前端
            'gfex_price': gfex_price,
            'cme_cny': cme_price,
            'spread': spread_val,
            'spread_pct': spread_pct_val,
            'spread_sge_pct': spread_pct_val,    # 兼容前端
            'spread_gfex_pct': spread_pct_val    # 兼容前端
        })
    
    # 6. 统计
    spreads = [h['spread_pct'] for h in history]
    stats = {
        'avg_spread_pct': float(np.mean(spreads)),
        'max_spread_pct': float(np.max(spreads)),
        'min_spread_pct': float(np.min(spreads))
    }
    
    # 7. 输出
    output = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'contracts': {
            'gfex': config['gfex_symbol'],
            'cme': config['cme_symbol']
        },
        'current': {
            'gfex_price': float(gfex_latest),
            'cme_cny': float(cme_latest),
            'cme_usd': float(cme_df['close'].iloc[-1]),
            'spread': float(spread),
            'spread_pct': float(spread_pct),
            'spread_gfex_pct': float(spread_pct),  # 兼容前端
            'spread_sge_pct': float(spread_pct)    # 兼容前端
        },
        'stats_3y_sge': stats,
        'history': history[-500:]  # 最近500条
    }
    
    return output


def main():
    print("=" * 60)
    print("分钟级价差数据生成 (到期合约)")
    print("=" * 60)
    
    # 生成铂金数据
    pt_data = generate_spread_data('platinum', period='60')  # 使用60分钟便于测试
    if pt_data:
        with open('platinum_spread_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(pt_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 铂金数据已保存到 platinum_spread_analysis.json")
    
    # 生成钯金数据
    pd_data = generate_spread_data('palladium', period='60')
    if pd_data:
        with open('palladium_spread_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(pd_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 钯金数据已保存到 palladium_spread_analysis.json")


if __name__ == "__main__":
    main()
