"""
获取CME钯金历史数据并计算与广期所的价差
由于SGE没有钯金数据，使用CME作为国际价格参考
"""

import pandas as pd
from datetime import datetime

try:
    import akshare as ak
except ImportError:
    print("请安装akshare: pip install akshare")
    exit(1)


def main():
    print("=" * 60)
    print("CME钯金历史价格分析")
    print("=" * 60)
    print()
    
    # 1. 获取CME钯金期货数据
    print("正在获取CME钯金期货数据...")
    try:
        cme_df = ak.futures_foreign_hist(symbol="PA")
        print(f"  ✓ 获取到 {len(cme_df)} 条CME钯金数据")
        print(f"  列名: {cme_df.columns.tolist()}")
    except Exception as e:
        print(f"  ✗ CME钯金获取失败: {e}")
        cme_df = None
        return
    
    # 2. 处理数据
    cme_df['date'] = pd.to_datetime(cme_df['date'])
    cme_df = cme_df.set_index('date')
    cme_df = cme_df.sort_index()
    
    # 只保留最近3年数据
    cme_df = cme_df[cme_df.index >= '2022-01-01']
    
    print(f"\n日期范围: {cme_df.index.min().strftime('%Y-%m-%d')} ~ {cme_df.index.max().strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(cme_df)}")
    
    # 3. 换算成人民币/克
    rate = 7.2  # 平均汇率
    oz_to_gram = 31.1035
    
    cme_df['close'] = pd.to_numeric(cme_df['close'], errors='coerce')
    cme_df['cny_per_gram'] = (cme_df['close'] * rate) / oz_to_gram
    
    print(f"\n价格统计 (人民币/克):")
    print(f"  最新: {cme_df['cny_per_gram'].iloc[-1]:.2f}")
    print(f"  过去1年均值: {cme_df['cny_per_gram'].tail(252).mean():.2f}")
    print(f"  过去1年最高: {cme_df['cny_per_gram'].tail(252).max():.2f}")
    print(f"  过去1年最低: {cme_df['cny_per_gram'].tail(252).min():.2f}")
    
    # 4. 与广期所价格对比
    gfex_price = 578.25  # 广期所当前价格 (元/克)
    intl_price = cme_df['cny_per_gram'].iloc[-1]
    spread = gfex_price - intl_price
    spread_pct = (spread / intl_price) * 100
    
    print(f"\n当前价差分析:")
    print(f"  广期所PD2606: {gfex_price:.2f} 元/克")
    print(f"  CME换算价格: {intl_price:.2f} 元/克")
    print(f"  价差: {spread:.2f} 元/克 ({spread_pct:+.2f}%)")
    
    # 5. 历史价差分析（假设广期所跟踪国际价格+溢价）
    print(f"\n历史价格区间分析 (美元/盎司):")
    
    years = [2022, 2023, 2024, 2025]
    for year in years:
        year_data = cme_df[cme_df.index.year == year]
        if len(year_data) > 0:
            avg_usd = year_data['close'].mean()
            max_usd = year_data['close'].max()
            min_usd = year_data['close'].min()
            print(f"  {year}: 均值 ${avg_usd:.0f}, 最高 ${max_usd:.0f}, 最低 ${min_usd:.0f}")
    
    # 6. 如果广期所溢价比例保持不变，历史收益分析
    print(f"\n假设价差收敛分析:")
    print(f"  当前溢价: {spread_pct:.2f}%")
    print(f"  如果溢价完全收敛，1000克收益: ¥{spread * 1000:,.0f}")
    print(f"  如果溢价收敛一半，1000克收益: ¥{spread * 0.5 * 1000:,.0f}")
    
    # 7. 保存数据
    output_df = cme_df[['close', 'cny_per_gram']].copy()
    output_df.columns = ['cme_usd_oz', 'cme_cny_gram']
    output_df.to_csv('cme_palladium_history.csv')
    print(f"\n✓ 数据已保存到 cme_palladium_history.csv")
    
    # 8. 输出JSON供前端使用
    import json
    recent_data = output_df.tail(30).reset_index()
    recent_data['date'] = recent_data['date'].dt.strftime('%Y-%m-%d')
    with open('cme_palladium_recent.json', 'w') as f:
        json.dump({
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price_usd': float(cme_df['close'].iloc[-1]),
            'current_price_cny_gram': float(cme_df['cny_per_gram'].iloc[-1]),
            'gfex_price': gfex_price,
            'spread': float(spread),
            'spread_pct': float(spread_pct),
            'history': recent_data.to_dict('records')
        }, f, ensure_ascii=False, indent=2)
    print(f"✓ 最近30天数据已保存到 cme_palladium_recent.json")


if __name__ == "__main__":
    main()
