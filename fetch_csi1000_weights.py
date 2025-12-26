"""
获取中证1000成分股权重数据
使用akshare的index_stock_cons_weight_csindex接口
"""

import akshare as ak
import pandas as pd
from datetime import datetime

print("正在获取中证1000成分股权重数据...")
print("指数代码: 000852 (中证1000)")

try:
    # 获取中证1000成分股权重
    df = ak.index_stock_cons_weight_csindex(symbol="000852")
    
    print(f"\n成功获取数据!")
    print(f"成分股数量: {len(df)}")
    print(f"\n数据列: {df.columns.tolist()}")
    print(f"\n前20条数据:")
    print(df.head(20).to_string(index=False))
    
    # 统计权重
    print(f"\n权重统计:")
    print(f"  权重总和: {df['权重'].sum():.4f}%")
    print(f"  最大权重: {df['权重'].max():.4f}%")
    print(f"  最小权重: {df['权重'].min():.4f}%")
    print(f"  平均权重: {df['权重'].mean():.4f}%")
    
    # 保存到CSV
    output_file = f'csi1000_weights_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n数据已保存到: {output_file}")
    
except Exception as e:
    print(f"获取数据失败: {e}")
    print("\n尝试查看akshare版本和可用接口...")
    print(f"akshare版本: {ak.__version__}")
