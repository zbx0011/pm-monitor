"""
快速增量刷新 - 只获取最新数据点，不重复计算历史
用于手动刷新按钮，耗时约5-10秒
"""
import os
import platform

if platform.system() == 'Windows':
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import json
import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime

DB_FILE = 'precious_metals.db'
OZ_TO_GRAM = 31.1035
RATE = 7.04

def get_latest_gfex_price(symbol):
    """获取广期所合约的最新价格（只取最后一条）"""
    try:
        df = ak.futures_zh_minute_sina(symbol=symbol, period='1')
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            return {
                'price': float(latest['close']),
                'datetime': pd.to_datetime(latest['datetime']).strftime('%Y-%m-%d %H:%M')
            }
    except Exception as e:
        print(f"  [!] 获取 {symbol} 失败: {e}")
    return None

def get_latest_cme_price(symbol, use_scraper=True):
    """获取CME合约的最新价格，优先使用爬虫获取实时数据"""
    # 1. 尝试使用爬虫获取实时价格
    if use_scraper:
        try:
            from tv_scraper import TradingViewScraper
            scraper = TradingViewScraper()
            try:
                price, data_time = scraper.get_price_with_time(symbol, 'NYMEX')
                if price:
                    time_str = data_time.strftime('%Y-%m-%d %H:%M') if data_time else datetime.now().strftime('%Y-%m-%d %H:%M')
                    # 保存到数据库
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO cme_platinum_contracts 
                        (contract, datetime, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (symbol, time_str, price, price, price, price, 0))
                    conn.commit()
                    conn.close()
                    return {'price': price, 'datetime': time_str, 'realtime': True}
            finally:
                scraper.close()
        except Exception as e:
            print(f"  [!] 爬虫获取 {symbol} 失败: {e}，回退到数据库")
    
    # 2. 回退到数据库
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT close, datetime FROM cme_platinum_contracts 
            WHERE contract = ? ORDER BY datetime DESC LIMIT 1
        ''', (symbol,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'price': row[0], 'datetime': row[1], 'realtime': False}
    except Exception as e:
        print(f"  [!] 获取 {symbol} 失败: {e}")
    return None

def update_pair_latest(metal, pair_name, gfex_contract, cme_contract, gfex_data, cme_data):
    """更新配对的最新数据到数据库"""
    gfex_price = gfex_data['price']
    cme_usd = cme_data['price']
    cme_cny = cme_usd * RATE / OZ_TO_GRAM
    spread = gfex_price - cme_cny
    spread_pct = (spread / cme_cny) * 100
    datetime_str = gfex_data['datetime']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    table = 'platinum_pairs' if metal == 'platinum' else 'palladium_pairs'
    
    cursor.execute(f'''
        INSERT OR REPLACE INTO {table} 
        (pair_name, gfex_contract, cme_contract, datetime, gfex_price, cme_usd, cme_cny, spread, spread_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pair_name, gfex_contract, cme_contract, datetime_str, gfex_price, cme_usd, cme_cny, spread, spread_pct))
    
    conn.commit()
    conn.close()
    
    return {
        'gfex_price': gfex_price,
        'cme_usd': cme_usd,
        'cme_cny': cme_cny,
        'spread': spread,
        'spread_pct': spread_pct,
        'datetime': datetime_str
    }

def quick_refresh():
    """快速增量刷新"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始快速刷新...")
    
    # 铂金配对
    PT_GFEX = ['PT2606', 'PT2610']
    PT_CME = ['PLF2026', 'PLJ2026', 'PLN2026', 'PLV2026']
    
    # 钯金配对
    PD_GFEX = ['PD2606', 'PD2608', 'PD2610', 'PD2612']
    PD_CME = ['PAH2026', 'PAM2026']
    
    updated_count = 0
    
    # 获取广期所最新价格
    print("  获取广期所最新价格...")
    gfex_prices = {}
    for sym in PT_GFEX + PD_GFEX:
        data = get_latest_gfex_price(sym)
        if data:
            gfex_prices[sym] = data
            print(f"    {sym}: {data['price']} @ {data['datetime']}")
    
    # 获取CME最新价格（优先使用爬虫批量获取）
    print("  获取CME最新价格...")
    cme_prices = {}
    all_cme_symbols = PT_CME + PD_CME
    
    # 尝试使用爬虫批量获取
    try:
        from tv_scraper import TradingViewScraper
        scraper = TradingViewScraper()
        try:
            for sym in all_cme_symbols:
                price, data_time = scraper.get_price_with_time(sym, 'NYMEX')
                if price:
                    time_str = data_time.strftime('%Y-%m-%d %H:%M') if data_time else datetime.now().strftime('%Y-%m-%d %H:%M')
                    # 保存到数据库
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO cme_platinum_contracts 
                        (contract, datetime, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (sym, time_str, price, price, price, price, 0))
                    conn.commit()
                    conn.close()
                    cme_prices[sym] = {'price': price, 'datetime': time_str}
                    print(f"    {sym}: ${price} @ {time_str} (实时)")
        finally:
            scraper.close()
    except Exception as e:
        print(f"  [!] 爬虫批量获取失败: {e}，回退到数据库")
        for sym in all_cme_symbols:
            data = get_latest_cme_price(sym, use_scraper=False)
            if data:
                cme_prices[sym] = data
                print(f"    {sym}: ${data['price']} @ {data['datetime']} (缓存)")
    
    # 更新铂金配对
    print("  更新铂金配对...")
    for gfex_sym in PT_GFEX:
        if gfex_sym not in gfex_prices:
            continue
        gfex_name = gfex_sym.replace('PT', '')
        for cme_sym in PT_CME:
            if cme_sym not in cme_prices:
                continue
            cme_month_map = {'F': '01', 'G': '02', 'H': '03', 'J': '04', 'K': '05', 'M': '06',
                             'N': '07', 'Q': '08', 'U': '09', 'V': '10', 'X': '11', 'Z': '12'}
            month_code = cme_sym[2]  # PLJ2026 -> 'J'
            year_suffix = cme_sym[5:7]  # PLJ2026 -> '26'
            cme_name = year_suffix + cme_month_map.get(month_code, '00')  # '26' + '04' = '2604'
            pair_name = f"{gfex_name}-{cme_name}"
            result = update_pair_latest('platinum', pair_name, gfex_sym, cme_sym, 
                                        gfex_prices[gfex_sym], cme_prices[cme_sym])
            print(f"    {pair_name}: 价差 {result['spread_pct']:+.2f}%")
            updated_count += 1
    
    # 更新钯金配对
    print("  更新钯金配对...")
    for gfex_sym in PD_GFEX:
        if gfex_sym not in gfex_prices:
            continue
        gfex_name = gfex_sym.replace('PD', '')
        for cme_sym in PD_CME:
            if cme_sym not in cme_prices:
                continue
            cme_month_map = {'F': '01', 'G': '02', 'H': '03', 'J': '04', 'K': '05', 'M': '06',
                             'N': '07', 'Q': '08', 'U': '09', 'V': '10', 'X': '11', 'Z': '12'}
            month_code = cme_sym[2]  # PAH2026 -> 'H'
            year_suffix = cme_sym[5:7]  # PAH2026 -> '26'
            cme_name = year_suffix + cme_month_map.get(month_code, '00')  # '26' + '03' = '2603'
            pair_name = f"{gfex_name}-{cme_name}"
            result = update_pair_latest('palladium', pair_name, gfex_sym, cme_sym,
                                        gfex_prices[gfex_sym], cme_prices[cme_sym])
            print(f"    {pair_name}: 价差 {result['spread_pct']:+.2f}%")
            updated_count += 1
    
    # 更新JSON文件（从数据库读取最新数据）
    print("  更新JSON文件...")
    update_json_files()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 快速刷新完成! 更新了 {updated_count} 个配对")
    return updated_count

def update_json_files():
    """从数据库读取最新数据并更新JSON文件"""
    conn = sqlite3.connect(DB_FILE)
    
    for metal, table, json_file in [
        ('platinum', 'platinum_pairs', 'platinum_all_pairs.json'),
        ('palladium', 'palladium_pairs', 'palladium_all_pairs.json')
    ]:
        cursor = conn.cursor()
        
        # 获取每个配对的最新数据
        cursor.execute(f'''
            SELECT pair_name, gfex_contract, cme_contract, datetime, gfex_price, cme_usd, cme_cny, spread, spread_pct
            FROM {table}
            WHERE (pair_name, datetime) IN (
                SELECT pair_name, MAX(datetime) FROM {table} GROUP BY pair_name
            )
        ''')
        
        pairs = {}
        for row in cursor.fetchall():
            pair_name = row[0]
            
            # 获取该配对的历史数据
            cursor.execute(f'''
                SELECT datetime, gfex_price, cme_usd, cme_cny, spread, spread_pct
                FROM {table}
                WHERE pair_name = ?
                ORDER BY datetime DESC
                LIMIT 5000
            ''', (pair_name,))
            
            history = [{'date': r[0], 'gfex_price': r[1], 'cme_usd': r[2], 
                       'cme_cny': r[3], 'spread': r[4], 'spread_pct': r[5]} 
                      for r in reversed(cursor.fetchall())]
            
            # 计算统计数据
            spreads = [h['spread_pct'] for h in history] if history else []
            stats = None
            if spreads:
                import numpy as np
                stats = {
                    'avg_spread_pct': float(np.mean(spreads)),
                    'max_spread_pct': float(np.max(spreads)),
                    'min_spread_pct': float(np.min(spreads))
                }
            
            pairs[pair_name] = {
                'gfex_contract': row[1],
                'cme_contract': row[2],
                'pair_name': pair_name,
                'current': {
                    'datetime': row[3],
                    'gfex_price': row[4],
                    'cme_usd': row[5],
                    'cme_cny': row[6],
                    'spread': row[7],
                    'spread_pct': row[8]
                },
                'stats': stats,
                'history': history
            }
        
        output = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pairs': pairs
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"    {json_file}: {len(pairs)} 个配对")
    
    conn.close()

if __name__ == '__main__':
    quick_refresh()
