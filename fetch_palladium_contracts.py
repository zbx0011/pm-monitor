import akshare as ak
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import sqlite3
import time
from datetime import datetime, timedelta

# 数据库文件
DB_FILE = 'precious_metals.db'

# 目标合约列表 (2025-12基准)
# 广期所: 偶数月份
GFEX_CONTRACTS = ['PD2606', 'PD2608', 'PD2610', 'PD2612']

# CME: 3, 6, 9, 12月 (H, M, U, Z)
CME_CONTRACTS = {
    'PAH2026': {'name': '2603', 'month': '2026年3月'},
    'PAM2026': {'name': '2606', 'month': '2026年6月'},
    'PAU2026': {'name': '2609', 'month': '2026年9月'},
    'PAZ2026': {'name': '2612', 'month': '2026年12月'}
}

def save_gfex_data(contract, df):
    if df is None or df.empty:
        return 0
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    count = 0
    
    for _, row in df.iterrows():
        try:
            # 转换时间格式
            dt_str = str(row['datetime']) # 已经是YYYY-MM-DD HH:MM:SS
            
            cursor.execute('''
                INSERT OR REPLACE INTO gfex_palladium_contracts 
                (contract, datetime, open, high, low, close, volume, hold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contract, dt_str,
                float(row['open']), float(row['high']),
                float(row['low']), float(row['close']),
                int(row['volume']), int(row.get('hold', 0))
            ))
            count += 1
        except Exception as e:
            # print(f"Error saving {contract}: {e}")
            pass
            
    conn.commit()
    conn.close()
    return count

def save_cme_data(contract, df):
    if df is None or df.empty:
        return 0
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    count = 0
    
    for idx, row in df.iterrows():
        try:
            # 处理时间 (CME数据是UTC时间，需要+8转北京时间，且注意tvDatafeed特性)
            # tvDatafeed返回的index是datetime对象
            # 这里统一加8小时转为北京时间
            # 但之前的经验显示，TvDatafeed获取的特定合约可能需要特殊处理
            # 暂时假设直接+8小时
            
            dt = idx + timedelta(hours=8)
            dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT OR REPLACE INTO cme_palladium_contracts 
                (contract, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                contract, dt_str,
                float(row['open']), float(row['high']),
                float(row['low']), float(row['close']),
                int(row['volume'])
            ))
            count += 1
        except Exception as e:
            pass
            
    conn.commit()
    conn.close()
    return count

def main():
    print("="*50)
    print("开始获取钯金合约数据")
    print("="*50)
    
    # 1. 获取广期所数据
    print("\n[广期所] 获取中...")
    for contract in GFEX_CONTRACTS:
        try:
            print(f"  正在获取 {contract}...", end='', flush=True)
            df = ak.futures_zh_minute_sina(symbol=contract, period='60')
            if df is not None and not df.empty:
                count = save_gfex_data(contract, df)
                print(f" 成功: {count} 条")
            else:
                print(" 无数据")
            time.sleep(1)
        except Exception as e:
            print(f" 失败: {e}")

    # 2. 获取CME数据
    print("\n[CME] 获取中...")
    tv = TvDatafeed()
    
    for symbol in CME_CONTRACTS.keys():
        retry = 3
        while retry > 0:
            try:
                print(f"  正在获取 {symbol} (剩余重试: {retry-1})...", end='', flush=True)
                df = tv.get_hist(symbol=symbol, exchange='NYMEX', interval=Interval.in_1_hour, n_bars=500)
                
                if df is not None and not df.empty:
                    count = save_cme_data(symbol, df)
                    print(f" 成功: {count} 条")
                    break
                else:
                    print(f" 获取为空")
                    retry -= 1
                    time.sleep(2)
            except Exception as e:
                print(f" 错误: {e}")
                retry -= 1
                time.sleep(2)

    print("\n完成!")

if __name__ == "__main__":
    main()
