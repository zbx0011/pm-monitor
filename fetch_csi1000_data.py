"""
获取中证1000成分股K线数据 - 改进版
使用akshare库，增加重试机制和断点续传
"""

import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime
import requests

# 设置更大的连接超时
requests.adapters.DEFAULT_RETRIES = 3

# 读取成分股列表
components_file = 'csi1000_components_20251206_194449.csv'
components = pd.read_csv(components_file, encoding='utf-8-sig')
print(f"成分股总数: {len(components)}")

# 输出文件
output_file = f'stock_data/kline/csi1000_kline_{datetime.now().strftime("%Y%m%d")}.csv'
progress_file = 'fetch_progress.txt'

# 检查是否有之前的进度
completed_codes = set()
if os.path.exists(progress_file):
    with open(progress_file, 'r') as f:
        completed_codes = set(f.read().strip().split('\n'))
    print(f"发现已完成 {len(completed_codes)} 只股票，继续获取...")

# 存储所有数据
all_data = []
failed_codes = []

# 开始日期
start_date = '20240201'
end_date = datetime.now().strftime('%Y%m%d')

print(f"数据范围: {start_date} 至 {end_date}")
print("开始获取数据...")

def fetch_with_retry(pure_code, max_retries=3):
    """带重试机制的数据获取"""
    for attempt in range(max_retries):
        try:
            df = ak.stock_zh_a_hist(
                symbol=pure_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise e
    return None

for idx, row in components.iterrows():
    pure_code = str(row['品种代码']).zfill(6)
    name = row['品种名称']
    
    # 判断市场
    if pure_code.startswith('6'):
        full_code = f'sh.{pure_code}'
    else:
        full_code = f'sz.{pure_code}'
    
    # 跳过已完成的
    if full_code in completed_codes:
        continue
    
    try:
        df = fetch_with_retry(pure_code)
        
        if df is not None and len(df) > 0:
            df = df.rename(columns={
                '日期': 'date', '开盘': 'open', '最高': 'high',
                '最低': 'low', '收盘': 'close', '成交量': 'volume', '成交额': 'amount'
            })
            df['股票代码'] = full_code
            df['股票名称'] = name
            df = df[['date', '股票代码', 'open', 'high', 'low', 'close', 'volume', 'amount', '股票名称']]
            all_data.append(df)
            
            # 记录进度
            with open(progress_file, 'a') as f:
                f.write(full_code + '\n')
            
            print(f"[{idx+1}/{len(components)}] ✓ {full_code} {name}: {len(df)} 条")
        else:
            failed_codes.append((full_code, name, "无数据"))
            print(f"[{idx+1}/{len(components)}] ✗ {full_code} {name}: 无数据")
            
    except Exception as e:
        failed_codes.append((full_code, name, str(e)[:50]))
        print(f"[{idx+1}/{len(components)}] ✗ {full_code} {name}: {str(e)[:50]}")
    
    # 请求间隔
    time.sleep(0.5)
    
    # 每100只保存一次
    if (idx + 1) % 100 == 0 and all_data:
        temp_result = pd.concat(all_data, ignore_index=True)
        temp_result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"--- 已保存 {len(all_data)} 只股票到 {output_file} ---")

# 最终保存
if all_data:
    result = pd.concat(all_data, ignore_index=True)
    result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ 数据保存到: {output_file}")
    print(f"✓ 成功获取: {len(all_data)} 只股票")
    print(f"✓ 总记录数: {len(result)}")

if failed_codes:
    print(f"\n✗ 失败: {len(failed_codes)} 只")
    # 保存失败列表
    with open('failed_codes.txt', 'w') as f:
        for code, name, err in failed_codes:
            f.write(f"{code},{name},{err}\n")
    print("失败列表已保存到 failed_codes.txt")
