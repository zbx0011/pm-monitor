"""
铂钯价差数据库管理
使用SQLite存储历史价差数据
"""

import sqlite3
import json
import os
from datetime import datetime

DB_FILE = 'precious_metals.db'


def init_database():
    """初始化数据库表结构"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 创建铂金价差历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platinum_spread (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            gfex_price REAL,
            cme_usd REAL,
            cme_cny REAL,
            spread REAL,
            spread_pct REAL,
            gfex_contract TEXT DEFAULT 'PT2610',
            cme_contract TEXT DEFAULT 'PLV2026',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(datetime)
        )
    ''')
    
    # 创建钯金价差历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS palladium_spread (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            gfex_price REAL,
            cme_usd REAL,
            cme_cny REAL,
            spread REAL,
            spread_pct REAL,
            gfex_contract TEXT DEFAULT 'PD2606',
            cme_contract TEXT DEFAULT 'PAM2026',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(datetime)
        )
    ''')
    
    # 创建价格快照表（用于实时价格记录）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            pt_gfex REAL,
            pt_cme_usd REAL,
            pt_cme_cny REAL,
            pt_spread REAL,
            pt_spread_pct REAL,
            pd_gfex REAL,
            pd_cme_usd REAL,
            pd_cme_cny REAL,
            pd_spread REAL,
            pd_spread_pct REAL,
            exchange_rate REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pt_datetime ON platinum_spread(datetime)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pd_datetime ON palladium_spread(datetime)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshot_datetime ON price_snapshots(datetime)')
    
    conn.commit()
    conn.close()
    print(f"✓ 数据库初始化完成: {DB_FILE}")


def import_json_data():
    """导入现有JSON数据到数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 导入铂金数据
    if os.path.exists('platinum_spread_analysis.json'):
        with open('platinum_spread_analysis.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for item in data.get('history', []):
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO platinum_spread 
                    (datetime, gfex_price, cme_cny, spread, spread_pct)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    item.get('date', item.get('datetime')),
                    item.get('gfex_price', item.get('sge_price')),
                    item.get('cme_cny'),
                    item.get('spread', item.get('spread_sge')),
                    item.get('spread_pct', item.get('spread_gfex_pct', item.get('spread_sge_pct')))
                ))
                count += 1
            except Exception as e:
                pass
        
        conn.commit()
        print(f"✓ 铂金数据导入: {count} 条记录")
    
    # 导入钯金数据
    if os.path.exists('palladium_spread_analysis.json'):
        with open('palladium_spread_analysis.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for item in data.get('history', []):
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO palladium_spread 
                    (datetime, gfex_price, cme_cny, spread, spread_pct)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    item.get('date', item.get('datetime')),
                    item.get('gfex_price', item.get('sge_price')),
                    item.get('cme_cny'),
                    item.get('spread', item.get('spread_sge')),
                    item.get('spread_pct', item.get('spread_gfex_pct', item.get('spread_sge_pct')))
                ))
                count += 1
            except Exception as e:
                pass
        
        conn.commit()
        print(f"✓ 钯金数据导入: {count} 条记录")
    
    conn.close()


def save_spread_data(metal, datetime_str, gfex_price, cme_usd, cme_cny, spread, spread_pct):
    """保存单条价差数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    table = 'platinum_spread' if metal == 'platinum' else 'palladium_spread'
    
    cursor.execute(f'''
        INSERT OR REPLACE INTO {table} 
        (datetime, gfex_price, cme_usd, cme_cny, spread, spread_pct)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime_str, gfex_price, cme_usd, cme_cny, spread, spread_pct))
    
    conn.commit()
    conn.close()


def save_price_snapshot(pt_data, pd_data, exchange_rate):
    """保存价格快照"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO price_snapshots 
        (datetime, pt_gfex, pt_cme_usd, pt_cme_cny, pt_spread, pt_spread_pct,
         pd_gfex, pd_cme_usd, pd_cme_cny, pd_spread, pd_spread_pct, exchange_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        pt_data.get('gfex_price'), pt_data.get('cme_usd'), pt_data.get('cme_cny'),
        pt_data.get('spread'), pt_data.get('spread_pct'),
        pd_data.get('gfex_price'), pd_data.get('cme_usd'), pd_data.get('cme_cny'),
        pd_data.get('spread'), pd_data.get('spread_pct'),
        exchange_rate
    ))
    
    conn.commit()
    conn.close()


def get_spread_history(metal, days=30):
    """获取历史价差数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    table = 'platinum_spread' if metal == 'platinum' else 'palladium_spread'
    
    cursor.execute(f'''
        SELECT datetime, gfex_price, cme_cny, spread, spread_pct
        FROM {table}
        ORDER BY datetime DESC
        LIMIT ?
    ''', (days * 24,))  # 假设每小时一条
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{'datetime': r[0], 'gfex_price': r[1], 'cme_cny': r[2], 
             'spread': r[3], 'spread_pct': r[4]} for r in rows]


def get_statistics(metal):
    """获取统计数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    table = 'platinum_spread' if metal == 'platinum' else 'palladium_spread'
    
    cursor.execute(f'''
        SELECT 
            COUNT(*) as total,
            AVG(spread_pct) as avg,
            MAX(spread_pct) as max,
            MIN(spread_pct) as min,
            (SELECT spread_pct FROM {table} ORDER BY datetime DESC LIMIT 1) as current
        FROM {table}
    ''')
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        'total_records': row[0],
        'avg_spread_pct': row[1],
        'max_spread_pct': row[2],
        'min_spread_pct': row[3],
        'current_spread_pct': row[4]
    }


def main():
    """主函数：初始化数据库并导入现有数据"""
    print("=" * 60)
    print("铂钯价差数据库初始化")
    print("=" * 60)
    
    # 初始化数据库
    init_database()
    
    # 导入现有JSON数据
    import_json_data()
    
    # 显示统计
    print("\n数据库统计:")
    for metal in ['platinum', 'palladium']:
        stats = get_statistics(metal)
        name = '铂金' if metal == 'platinum' else '钯金'
        print(f"\n{name}:")
        print(f"  总记录数: {stats['total_records']}")
        if stats['avg_spread_pct']:
            print(f"  平均价差: {stats['avg_spread_pct']:.2f}%")
            print(f"  最高价差: {stats['max_spread_pct']:.2f}%")
            print(f"  最低价差: {stats['min_spread_pct']:.2f}%")
            print(f"  当前价差: {stats['current_spread_pct']:.2f}%")


if __name__ == "__main__":
    main()
