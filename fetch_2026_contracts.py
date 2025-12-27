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
    print("✓ 合约数据表初始化完成")

def fetch_and_save_gfex(contracts):
    """获取并保存广期所铂金合约数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for symbol in contracts:
        print(f"\n正在获取广期所 {symbol}...")
        try:
            df = ak.futures_zh_minute_sina(symbol=symbol, period='60')
            if df is None or len(df) == 0:
                print(f"  ✗ {symbol} 无数据")
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
            print(f"  ✓ {symbol}: 保存 {count} 条小时数据")
        except Exception as e:
            print(f"  ✗ {symbol} 获取失败: {e}")
    
    conn.close()

def fetch_and_save_cme(tv, contracts):
    """获取并保存CME铂金合约数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for symbol, desc in contracts:
        print(f"\n正在获取CME {symbol} ({desc})...")
        try:
            df = tv.get_hist(symbol=symbol, exchange='NYMEX', 
                            interval=Interval.in_1_hour, n_bars=500)
            if df is None or len(df) == 0:
                print(f"  ✗ {symbol} 无数据")
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
            print(f"  ✓ {symbol}: 保存 {count} 条小时数据")
        except Exception as e:
            print(f"  ✗ {symbol} 获取失败: {e}")
    
    conn.close()

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
    
    # 显示统计
    show_summary()
    
    print("\n✓ 数据获取完成!")

if __name__ == "__main__":
    main()
