"""
获取2026年所有铂金合约小时数据并存入数据库
广期所: PT2606, PT2610
CME: PLF2026, PLJ2026, PLN2026, PLV2026
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

DB_FILE = 'precious_metals.db'
OZ_TO_GRAM = 31.1035
RATE = 7.04

def init_contracts_table():
    """创建各月份合约数据表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 广期所铂金各月份合约表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gfex_platinum_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract TEXT NOT NULL,
            datetime TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            hold INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(contract, datetime)
        )
    ''')
    
    # CME铂金各月份合约表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cme_platinum_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract TEXT NOT NULL,
            datetime TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(contract, datetime)
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gfex_pt_contract ON gfex_platinum_contracts(contract, datetime)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cme_pt_contract ON cme_platinum_contracts(contract, datetime)')
    
    conn.commit()
    conn.close()
    print("[OK] 合约数据表初始化完成")

def fetch_and_save_gfex(contracts):
    """获取并保存广期所铂金合约数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for symbol in contracts:
        print(f"\n正在获取广期所 {symbol}...")
        try:
            df = ak.futures_zh_minute_sina(symbol=symbol, period='60')
            if df is None or len(df) == 0:
                print(f"  [X] {symbol} 无数据")
                continue
            
            df['datetime'] = pd.to_datetime(df['datetime'])
            count = 0
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO gfex_platinum_contracts 
                    (contract, datetime, open, high, low, close, volume, hold)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    row['datetime'].strftime('%Y-%m-%d %H:%M'),
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    int(row['volume']) if pd.notna(row['volume']) else 0,
                    int(row['hold']) if pd.notna(row['hold']) else 0
                ))
                count += 1
            
            conn.commit()
            print(f"  [OK] {symbol}: 保存 {count} 条小时数据")
        except Exception as e:
            print(f"  [X] {symbol} 获取失败: {e}")
    
    conn.close()

def fetch_and_save_cme(tv, contracts):
    """获取并保存CME铂金合约分钟数据 (使用 tvDatafeed 历史数据)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for symbol, desc in contracts:
        print(f"\n正在获取CME {symbol} ({desc}) 分钟数据...")
        try:
            # 获取分钟级数据，最多 5000 条
            df = tv.get_hist(symbol=symbol, exchange='NYMEX', 
                            interval=Interval.in_1_minute, n_bars=5000)
            if df is None or len(df) == 0:
                print(f"  [X] {symbol} 无数据")
                continue
            
            df = df.sort_index()
            count = 0
            for idx, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO cme_platinum_contracts 
                    (contract, datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    idx.strftime('%Y-%m-%d %H:%M'),
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    int(row['volume']) if pd.notna(row.get('volume', 0)) else 0
                ))
                count += 1
            
            conn.commit()
            print(f"  [OK] {symbol}: 保存 {count} 条分钟数据")
        except Exception as e:
            print(f"  [X] {symbol} 获取失败: {e}")
    
    conn.close()


def fetch_realtime_with_scraper(contracts):
    """使用 TradingView 爬虫获取实时价格和实际时间戳"""
    try:
        from tv_scraper import TradingViewScraper
    except ImportError:
        print("  [!] tv_scraper 模块未找到，跳过实时爬取")
        return {}
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    scraper = TradingViewScraper()
    results = {}
    
    try:
        for symbol, desc in contracts:
            print(f"\n[爬虫] 获取 {symbol} 实时价格...")
            price, data_time = scraper.get_price_with_time(symbol, 'NYMEX')
            
            if price:
                results[symbol] = {'price': price, 'time': data_time}
                # 使用实际数据时间，如果获取失败则使用当前时间
                if data_time:
                    time_str = data_time.strftime('%Y-%m-%d %H:%M')
                else:
                    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"    [!] 未获取到数据时间，使用当前时间: {time_str}")
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cme_platinum_contracts 
                    (contract, datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, time_str, price, price, price, price, 0))
                print(f"    [OK] {symbol}: ${price} @ {time_str} (已保存)")
            else:
                print(f"    [X] {symbol}: 获取失败")
        
        conn.commit()
    finally:
        scraper.close()
        conn.close()
    
    return results


def show_summary():
    """显示数据库中的合约数据统计"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("数据库统计")
    print("=" * 70)
    
    # 广期所
    print("\n【广期所铂金合约】")
    cursor.execute('''
        SELECT contract, COUNT(*) as cnt, MIN(datetime), MAX(datetime)
        FROM gfex_platinum_contracts
        GROUP BY contract
        ORDER BY contract
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:>5} 条 | {row[2]} ~ {row[3]}")
    
    # CME
    print("\n【CME铂金合约】")
    cursor.execute('''
        SELECT contract, COUNT(*) as cnt, MIN(datetime), MAX(datetime)
        FROM cme_platinum_contracts
        GROUP BY contract
        ORDER BY contract
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:>5} 条 | {row[2]} ~ {row[3]}")
    
    conn.close()

def main():
    print("=" * 70)
    print("获取2026年铂金各月份合约数据")
    print("=" * 70)
    
    # 初始化表
    init_contracts_table()
    
    # 广期所2026年合约
    gfex_contracts = ['PT2606', 'PT2610']
    fetch_and_save_gfex(gfex_contracts)
    
    # CME 2026年合约
    tv = TvDatafeed()
    cme_contracts = [
        ('PLF2026', '2026年1月'),
        ('PLJ2026', '2026年4月'),
        ('PLN2026', '2026年7月'),
        ('PLV2026', '2026年10月'),
    ]
    fetch_and_save_cme(tv, cme_contracts)
    
    # 使用爬虫获取实时价格（更准确）
    print("\n" + "=" * 70)
    print("使用 TradingView 爬虫获取实时价格...")
    print("=" * 70)
    fetch_realtime_with_scraper(cme_contracts)
    
    # 显示统计
    show_summary()
    
    print("\n[OK] 数据获取完成!")

if __name__ == "__main__":
    main()
