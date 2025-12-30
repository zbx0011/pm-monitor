"""
分析 CME 数据的时间偏移问题
"""
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = 'precious_metals.db'

def analyze_time_offset():
    conn = sqlite3.connect(DB_FILE)
    
    # 读取最近的数据
    query = """
    SELECT datetime, gfex_price, cme_usd, pair_name, created_at
    FROM platinum_pairs 
    WHERE pair_name = '2610-2604'
    ORDER BY datetime DESC 
    LIMIT 30
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("最近30条 2610-2604 配对数据:")
    print("=" * 80)
    print(f"{'数据时间':<20} | {'GFEX价格':>10} | {'CME价格':>10} | {'创建时间':<20}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        print(f"{row['datetime']:<20} | {row['gfex_price']:>10.2f} | {row['cme_usd']:>10.2f} | {str(row['created_at']):<20}")
    
    # 分析：检查是否存在重复的 CME 价格（可能表示数据没更新）
    print("\n" + "=" * 80)
    print("CME 价格变化分析:")
    cme_changes = df['cme_usd'].diff().abs()
    unchanged_count = (cme_changes == 0).sum()
    print(f"  连续相同价格的次数: {unchanged_count} / {len(df)}")
    
    # 检查唯一的 CME 价格数量
    unique_cme = df['cme_usd'].nunique()
    print(f"  唯一 CME 价格数量: {unique_cme}")
    
    # 显示 CME 价格的分布
    print("\n  CME 价格分布:")
    print(df['cme_usd'].value_counts().head(10))

if __name__ == "__main__":
    analyze_time_offset()
