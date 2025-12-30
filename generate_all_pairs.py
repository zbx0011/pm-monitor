"""
生成所有铂金合约配对的价差数据
广期所: PT2606, PT2610
CME: PLF2026(1月), PLJ2026(4月), PLN2026(7月), PLV2026(10月)
"""
import os
import platform

# 仅在Windows本地开发环境使用代理，VPS(Linux)通常不需要或使用系统配置
if platform.system() == 'Windows':
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import json
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval
from database import init_database, save_pair_history, get_pair_history
from alert_manager import check_and_alert

OZ_TO_GRAM = 31.1035
RATE = 7.04

# 合约配置
GFEX_CONTRACTS = {
    'PT2606': {'name': '2606', 'month': '2026年6月'},
    'PT2610': {'name': '2610', 'month': '2026年10月'}
}

CME_CONTRACTS = {
    'PLF2026': {'name': '2601', 'month': '2026年1月'},
    'PLJ2026': {'name': '2604', 'month': '2026年4月'},
    'PLN2026': {'name': '2607', 'month': '2026年7月'},
    'PLV2026': {'name': '2610', 'month': '2026年10月'}
}


def fetch_gfex_data(symbol):
    """获取广期所分钟数据"""
    try:
        df = ak.futures_zh_minute_sina(symbol=symbol, period='1')
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()
        return df
    except Exception as e:
        print(f"  ✗ 广期所{symbol}获取失败: {e}")
        return None


import sqlite3
DB_FILE = 'precious_metals.db'

def fetch_cme_data(tv, symbol):
    """从数据库获取CME分钟数据"""
    try:
        conn = sqlite3.connect(DB_FILE)
        # 读取最近 5000 条数据
        query = f'''
            SELECT datetime, open, high, low, close, volume 
            FROM cme_platinum_contracts 
            WHERE contract = '{symbol}'
            ORDER BY datetime DESC
            LIMIT 5000
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df is None or len(df) == 0:
            print(f"  ✗ 数据库中无 {symbol} 数据")
            return None
            
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()
        return df
    except Exception as e:
        print(f"  ✗ 数据库读取 {symbol} 失败: {e}")
        return None


def calculate_spread(gfex_df, cme_df, gfex_symbol, cme_symbol):
    """计算两个合约的价差"""
    history = []
    
    for idx, row in gfex_df.iterrows():
        gfex_price = float(row['close'])
        
        # 查找CME同一小时的数据 (允许±30分钟匹配)
        # 精确匹配：找出时间差最小的一条
        # 使用 Series 计算以保留索引
        diffs = pd.Series(np.abs((cme_df.index - idx).total_seconds()), index=cme_df.index)
        
        # 只保留 30 分钟内的数据
        valid_matches = diffs[diffs <= 1800]
        
        if len(valid_matches) == 0:
            continue
            
        # 找到时间差最小的那个索引
        best_match_idx = valid_matches.idxmin()
        cme_row = cme_df.loc[best_match_idx]
        
        cme_usd = float(cme_row['close'])
        cme_cny = cme_usd * RATE / OZ_TO_GRAM
        spread = gfex_price - cme_cny
        spread_pct = (spread / cme_cny) * 100
        
        history.append({
            'date': idx.strftime('%Y-%m-%d %H:%M'),
            'gfex_price': gfex_price,
            'cme_usd': cme_usd,
            'cme_cny': cme_cny,
            'spread': spread,
            'spread_pct': spread_pct
        })
    
    return history


def main():
    print("=" * 80)
    print("生成所有铂金合约配对价差数据")
    print("=" * 80)
    
    # tv = TvDatafeed()  # 不再需要 tvDatafeed，直接从数据库读取
    tv = None
    
    # 获取所有广期所数据
    gfex_data = {}
    for symbol in GFEX_CONTRACTS:
        print(f"\n正在获取广期所 {symbol}...")
        df = fetch_gfex_data(symbol)
        if df is not None:
            gfex_data[symbol] = df
            print(f"  [OK] {symbol}: {len(df)} 条数据")
    
    # 获取所有CME数据
    cme_data = {}
    for symbol in CME_CONTRACTS:
        print(f"\n正在获取CME {symbol}...")
        df = fetch_cme_data(tv, symbol)
        if df is not None:
            cme_data[symbol] = df
            print(f"  [OK] {symbol}: {len(df)} 条数据")
    
    # 生成所有配对的价差
    all_pairs = {}
    
    for gfex_sym, gfex_info in GFEX_CONTRACTS.items():
        if gfex_sym not in gfex_data:
            continue
        
        for cme_sym, cme_info in CME_CONTRACTS.items():
            if cme_sym not in cme_data:
                continue
            
            pair_name = f"{gfex_info['name']}-{cme_info['name']}"
            print(f"\n正在计算配对 {pair_name} ({gfex_sym} vs {cme_sym})...")
            
            history = calculate_spread(gfex_data[gfex_sym], cme_data[cme_sym], gfex_sym, cme_sym)
            
            if len(history) > 0:
                spreads = [h['spread_pct'] for h in history]
                latest = history[-1]
                
                pair_data = {
                    'gfex_contract': gfex_sym,
                    'cme_contract': cme_sym,
                    'pair_name': pair_name,
                    'gfex_month': gfex_info['month'],
                    'cme_month': cme_info['month'],
                    'current': {
                        'gfex_price': latest['gfex_price'],
                        'cme_usd': latest['cme_usd'],
                        'cme_cny': latest['cme_cny'],
                        'spread': latest['spread'],
                        'spread_pct': latest['spread_pct']
                    },
                    'stats': {
                        'avg_spread_pct': float(np.mean(spreads)),
                        'max_spread_pct': float(np.max(spreads)),
                        'min_spread_pct': float(np.min(spreads))
                    },
                    'history': history
                }
                
                all_pairs[pair_name] = pair_data
                
                # 保存到数据库
                save_pair_history('platinum', pair_name, gfex_sym, cme_sym, history)
                
                # 从数据库读取完整历史（包括导入的小时级数据）
                db_history = get_pair_history('platinum', pair_name)
                if db_history:
                    pair_data['history'] = db_history
                    # 重新计算统计数据
                    all_spreads = [h['spread_pct'] for h in db_history]
                    pair_data['stats'] = {
                        'avg_spread_pct': float(np.mean(all_spreads)),
                        'max_spread_pct': float(np.max(all_spreads)),
                        'min_spread_pct': float(np.min(all_spreads))
                    }
                
                print(f"  [OK] {pair_name}: {len(pair_data['history'])} 条数据, 当前价差: {latest['spread_pct']:+.2f}%")
                
                # 检查报警
                check_and_alert(
                    metal='platinum',
                    pair_name=pair_name,
                    spread_pct=latest['spread_pct'],
                    current_gfex=latest['gfex_price'],
                    current_cme=latest['cme_cny']
                )
    
    # 保存所有配对数据到JSON
    output = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'pairs': all_pairs
    }
    
    with open('platinum_all_pairs.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("配对汇总")
    print("=" * 80)
    print(f"{'配对':<12} | {'广期所':>10} | {'CME(USD)':>10} | {'价差%':>10}")
    print("-" * 50)
    for name, data in all_pairs.items():
        c = data['current']
        print(f"{name:<12} | {c['gfex_price']:>10.2f} | {c['cme_usd']:>10.2f} | {c['spread_pct']:>+10.2f}%")
    
    print(f"\n[OK] 数据已保存到 platinum_all_pairs.json 和数据库")
    print("=" * 80)


if __name__ == "__main__":
    main()
