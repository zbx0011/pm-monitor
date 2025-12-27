"""
自动数据刷新服务
每10分钟获取分钟级数据并更新JSON文件和数据库
"""

import os
import time
import schedule
import pandas as pd
import numpy as np
from datetime import datetime
import json
import akshare as ak

# 设置代理 (TradingView需要)
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval
from database import save_spread_data, save_price_snapshot

OZ_TO_GRAM = 31.1035
RATE = 7.04  # USD/CNY汇率

# 合约配置
CONTRACTS = {
    'platinum': {
        'gfex_symbol': 'PT2610',
        'gfex_main': 'PT0',
        'cme_symbol': 'PLV2026',
        'cme_exchange': 'NYMEX',
        'name': '铂金'
    },
    'palladium': {
        'gfex_symbol': 'PD2606',
        'gfex_main': 'PD0',
        'cme_symbol': 'PAM2026',
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
    """获取CME分钟数据"""
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
        if df is not None:
            df = df.sort_index()
        return df
    except Exception as e:
        print(f"  ✗ CME {symbol}获取失败: {e}")
        return None


def generate_spread_data(tv, metal='platinum'):
    """生成指定品种的价差数据 - 使用小时级数据，确保两边同一时间匹配"""
    config = CONTRACTS[metal]
    
    # 1. 获取广期所具体合约小时数据 (使用PT2610/PD2606)
    try:
        gfex_df = ak.futures_zh_minute_sina(symbol=config['gfex_symbol'], period='60')
        gfex_df['datetime'] = pd.to_datetime(gfex_df['datetime'])
        gfex_df = gfex_df.set_index('datetime').sort_index()
        gfex_df = gfex_df.rename(columns={'close': 'gfex_close'})
    except Exception as e:
        print(f"  ✗ 广期所{config['gfex_symbol']}获取失败: {e}")
        return None
    
    # 2. 获取CME小时数据 (TvDatafeed返回北京时间)
    try:
        cme_df = tv.get_hist(symbol=config['cme_symbol'], exchange=config['cme_exchange'], 
                            interval=Interval.in_1_hour, n_bars=500)
        if cme_df is None or len(cme_df) == 0:
            print(f"  ✗ CME {config['cme_symbol']}数据为空")
            return None
        cme_df = cme_df.sort_index()
        cme_df['cme_cny'] = (cme_df['close'] * RATE) / OZ_TO_GRAM
        cme_df = cme_df.rename(columns={'close': 'cme_usd'})
    except Exception as e:
        print(f"  ✗ CME {config['cme_symbol']}获取失败: {e}")
        return None
    
    # 3. 按北京时间小时匹配：生成历史数据
    history = []
    for idx, row in gfex_df.iterrows():
        gfex_price = float(row['gfex_close'])
        
        # 查找CME同一小时的数据 (允许±30分钟匹配)
        time_diff = abs((cme_df.index - idx).total_seconds())
        matches = cme_df[time_diff <= 1800]
        
        if len(matches) == 0:
            continue
        
        cme_row = matches.iloc[0]
        cme_cny = float(cme_row['cme_cny'])
        cme_usd = float(cme_row['cme_usd'])
        spread_val = gfex_price - cme_cny
        spread_pct_val = (spread_val / cme_cny) * 100
        
        history.append({
            'date': idx.strftime('%Y-%m-%d %H:%M'),
            'sge_price': gfex_price,
            'gfex_price': gfex_price,
            'cme_usd': cme_usd,
            'cme_cny': cme_cny,
            'spread': spread_val,
            'spread_pct': spread_pct_val,
            'spread_sge_pct': spread_pct_val,
            'spread_gfex_pct': spread_pct_val
        })
    
    if len(history) == 0:
        print(f"  ✗ 没有匹配的数据")
        return None
    
    # 4. 统计和当前数据
    spreads = [h['spread_pct'] for h in history]
    stats = {
        'avg_spread_pct': float(np.mean(spreads)),
        'max_spread_pct': float(np.max(spreads)),
        'min_spread_pct': float(np.min(spreads))
    }
    
    latest = history[-1]
    
    output = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'contracts': {
            'gfex': config['gfex_symbol'],
            'cme': config['cme_symbol']
        },
        'current': {
            'gfex_price': latest['gfex_price'],
            'cme_cny': latest['cme_cny'],
            'cme_usd': latest['cme_usd'],
            'spread': latest['spread'],
            'spread_pct': latest['spread_pct'],
            'spread_gfex_pct': latest['spread_pct'],
            'spread_sge_pct': latest['spread_pct']
        },
        'stats_3y_sge': stats,
        'history': history
    }
    
    return output


def update_all_data():
    """更新所有数据"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 自动更新数据...")
    print(f"{'='*60}")
    
    try:
        tv = TvDatafeed()
        
        # 更新铂金
        print("\n正在更新铂金数据...")
        pt_data = generate_spread_data(tv, 'platinum')
        if pt_data:
            with open('platinum_spread_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(pt_data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 铂金: {pt_data['current']['gfex_price']:.2f} vs {pt_data['current']['cme_cny']:.2f} = {pt_data['current']['spread_pct']:+.2f}%")
        
        # 更新钯金
        print("\n正在更新钯金数据...")
        pd_data = generate_spread_data(tv, 'palladium')
        if pd_data:
            with open('palladium_spread_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(pd_data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 钯金: {pd_data['current']['gfex_price']:.2f} vs {pd_data['current']['cme_cny']:.2f} = {pd_data['current']['spread_pct']:+.2f}%")
        
        # 更新价格卡片数据 (for API)
        prices_data = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'exchange_rate': RATE,
            'gfex': {
                'pt_price': pt_data['current']['gfex_price'] if pt_data else 0,
                'pd_price': pd_data['current']['gfex_price'] if pd_data else 0,
                'pt_time': datetime.now().strftime('%H:%M'),
                'pd_time': datetime.now().strftime('%H:%M')
            },
            'cme': {
                'pt_price': pt_data['current']['cme_usd'] if pt_data else 0,
                'pd_price': pd_data['current']['cme_usd'] if pd_data else 0,
                'pt_time': datetime.now().strftime('%H:%M'),
                'pd_time': datetime.now().strftime('%H:%M')
            },
            'spread': {
                'pt_spread': pt_data['current']['spread'] if pt_data else 0,
                'pt_spread_pct': pt_data['current']['spread_pct'] if pt_data else 0,
                'pd_spread': pd_data['current']['spread'] if pd_data else 0,
                'pd_spread_pct': pd_data['current']['spread_pct'] if pd_data else 0
            }
        }
        
        with open('prices_data.json', 'w', encoding='utf-8') as f:
            json.dump(prices_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ prices_data.json 已更新")
        
        # 保存到数据库
        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            if pt_data:
                save_spread_data('platinum', now_str, 
                               pt_data['current']['gfex_price'],
                               pt_data['current']['cme_usd'],
                               pt_data['current']['cme_cny'],
                               pt_data['current']['spread'],
                               pt_data['current']['spread_pct'])
            if pd_data:
                save_spread_data('palladium', now_str,
                               pd_data['current']['gfex_price'],
                               pd_data['current']['cme_usd'],
                               pd_data['current']['cme_cny'],
                               pd_data['current']['spread'],
                               pd_data['current']['spread_pct'])
            if pt_data and pd_data:
                save_price_snapshot(pt_data['current'], pd_data['current'], RATE)
            print(f"✓ 数据已保存到数据库")
        except Exception as db_err:
            print(f"  数据库保存警告: {db_err}")
        
        print(f"\n✓ 数据更新完成!")
        
    except Exception as e:
        print(f"\n✗ 更新失败: {e}")


def main():
    print("=" * 60)
    print("自动数据刷新服务")
    print("每10分钟更新一次分钟级数据")
    print("=" * 60)
    
    # 立即执行一次
    update_all_data()
    
    # 设置定时任务
    schedule.every(10).minutes.do(update_all_data)
    
    print("\n服务已启动，每10分钟自动更新...")
    print("按 Ctrl+C 停止服务")
    
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
