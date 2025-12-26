"""
获取中证1000成分股K线数据 - 使用baostock
这是备选方案，baostock接口更稳定
"""

import baostock as bs
import pandas as pd
import time
from datetime import datetime

# 登录baostock
lg = bs.login()
print(f"登录状态: {lg.error_code} - {lg.error_msg}")

# 读取成分股列表
components_file = 'csi1000_components_20251206_194449.csv'
components = pd.read_csv(components_file, encoding='utf-8-sig')
print(f"成分股总数: {len(components)}")

# 输出文件
output_file = f'stock_data/kline/csi1000_kline_{datetime.now().strftime("%Y%m%d")}.csv'

# 存储所有数据
all_data = []
failed_codes = []

# 日期范围
start_date = '2024-02-01'
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"数据范围: {start_date} 至 {end_date}")
print("开始获取数据...")

for idx, row in components.iterrows():
    pure_code = str(row['品种代码']).zfill(6)
    name = row['品种名称']
    
    # baostock格式: sh.600000 或 sz.000001
    if pure_code.startswith('6'):
        bs_code = f'sh.{pure_code}'
    else:
        bs_code = f'sz.{pure_code}'
    
    try:
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="2"  # 前复权
        )
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if data_list:
            df = pd.DataFrame(data_list, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'amount'])
            df['股票代码'] = bs_code
            df['股票名称'] = name
            df = df[['date', '股票代码', 'open', 'high', 'low', 'close', 'volume', 'amount', '股票名称']]
            all_data.append(df)
            print(f"[{idx+1}/{len(components)}] ✓ {bs_code} {name}: {len(df)} 条")
        else:
            failed_codes.append((bs_code, name, rs.error_msg))
            print(f"[{idx+1}/{len(components)}] ✗ {bs_code} {name}: {rs.error_msg}")
            
    except Exception as e:
        failed_codes.append((bs_code, name, str(e)[:50]))
        print(f"[{idx+1}/{len(components)}] ✗ {bs_code} {name}: {e}")
    
    # 每200只保存一次
    if (idx + 1) % 200 == 0 and all_data:
        temp_result = pd.concat(all_data, ignore_index=True)
        temp_result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"--- 已保存 {len(all_data)} 只股票到 {output_file} ---")
    
    # 短暂延迟避免请求过快
    if (idx + 1) % 50 == 0:
        time.sleep(0.5)

# 登出
bs.logout()

# 最终保存
if all_data:
    result = pd.concat(all_data, ignore_index=True)
    result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ 数据保存到: {output_file}")
    print(f"✓ 成功获取: {len(all_data)} 只股票")
    print(f"✓ 总记录数: {len(result)}")
else:
    print("\n✗ 未获取到任何数据")

if failed_codes:
    print(f"\n✗ 失败: {len(failed_codes)} 只")
    with open('failed_codes.txt', 'w', encoding='utf-8') as f:
        for code, name, err in failed_codes:
            f.write(f"{code},{name},{err}\n")
    print("失败列表已保存到 failed_codes.txt")
