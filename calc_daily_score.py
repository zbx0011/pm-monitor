"""
计算中证1000每日加权平均压力支撑评分 - 优化版
使用向量化操作和预计算提高性能
整合真实成分股权重数据
"""

import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("中证1000每日加权平均压力支撑评分计算（带权重版）")
print("=" * 60)

# 获取中证1000成分股权重
print("\n正在获取中证1000成分股权重...")
try:
    weights_df = ak.index_stock_cons_weight_csindex(symbol="000852")
    # 构建权重映射：成分券代码 -> 权重
    weight_map = {}
    for _, row in weights_df.iterrows():
        code = str(row['成分券代码']).zfill(6)
        weight_map[code] = float(row['权重'])
    print(f"成功获取 {len(weight_map)} 只成分股权重")
    print(f"权重总和: {sum(weight_map.values()):.2f}%")
except Exception as e:
    print(f"获取权重数据失败: {e}")
    print("将使用等权重计算...")
    weight_map = {}

# 读取K线数据
kline_file = 'stock_data/kline/csi1000_kline_20251208.csv'
df = pd.read_csv(kline_file, encoding='utf-8-sig')
df['date'] = pd.to_datetime(df['date'])

# 确保数据类型正确
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"K线数据: {len(df)} 条记录")

# 获取所有股票代码
stocks = df['股票代码'].unique()
print(f"股票数量: {len(stocks)}")

# 筛选2025年数据
df_2025 = df[df['date'] >= '2025-01-01'].copy()
trade_dates = sorted(df_2025['date'].unique())
print(f"2025年交易日: {len(trade_dates)} 天")

# ============ 简化的评分算法 ============
def calc_score_fast(stock_df, lookback=180):
    """使用全部历史数据一次性计算每日评分"""
    results = []
    stock_df = stock_df.sort_values('date').reset_index(drop=True)
    
    for i in range(len(stock_df)):
        row = stock_df.iloc[i]
        if row['date'] < pd.Timestamp('2025-01-01'):
            continue
        
        # 需要至少20天历史数据
        if i < 20:
            results.append({'date': row['date'], 'score': 0, 'zone_type': 'insufficient'})
            continue
        
        # 使用最近180天数据计算VP分布
        start_idx = max(0, i - lookback)
        hist = stock_df.iloc[start_idx:i]
        
        if len(hist) < 20:
            results.append({'date': row['date'], 'score': 0, 'zone_type': 'insufficient'})
            continue
        
        # 当前K线
        current_high = row['high']
        current_low = row['low']
        current_close = row['close']
        
        # 3天前收盘价
        price_3d_ago = stock_df.iloc[max(0, i-3)]['close']
        
        # 简单的VP计算：统计不同价格区间的成交量
        price_min = hist['low'].min() * 0.98
        price_max = hist['high'].max() * 1.02
        bins = 50
        bin_size = (price_max - price_min) / bins
        
        # 计算每个价格区间的成交量
        vol_dist = np.zeros(bins)
        for _, h in hist.iterrows():
            if h['high'] <= h['low'] or h['volume'] <= 0:
                continue
            low_bin = int((h['low'] - price_min) / bin_size)
            high_bin = int((h['high'] - price_min) / bin_size)
            low_bin = max(0, min(bins-1, low_bin))
            high_bin = max(0, min(bins-1, high_bin))
            for b in range(low_bin, high_bin + 1):
                vol_dist[b] += h['volume'] / (high_bin - low_bin + 1)
        
        # 找低量区（低于平均的55%）
        avg_vol = vol_dist.mean()
        threshold = avg_vol * 0.55
        
        # 识别LVN区间
        in_lvn = False
        lvn_start = None
        zones = []
        
        for b in range(bins):
            if vol_dist[b] < threshold:
                if not in_lvn:
                    in_lvn = True
                    lvn_start = b
            else:
                if in_lvn:
                    zones.append({
                        'low': price_min + lvn_start * bin_size,
                        'high': price_min + b * bin_size,
                        'avg_vol': vol_dist[lvn_start:b].mean()
                    })
                    in_lvn = False
        
        if in_lvn:
            zones.append({
                'low': price_min + lvn_start * bin_size,
                'high': price_max,
                'avg_vol': vol_dist[lvn_start:].mean()
            })
        
        # 检查是否触及LVN
        touched_zone = None
        for z in zones:
            if current_high >= z['low'] and current_low <= z['high']:
                touched_zone = z
                break
        
        if touched_zone is None:
            results.append({'date': row['date'], 'score': 0, 'zone_type': 'no_touch'})
            continue
        
        # 判断压力/支撑
        if price_3d_ago < touched_zone['low']:
            zone_type = 'resistance'
        elif price_3d_ago > touched_zone['high']:
            zone_type = 'support'
        else:
            zone_type = 'resistance' if current_close < (touched_zone['low'] + touched_zone['high'])/2 else 'support'
        
        # 计算评分
        strength = 100 * (1 - touched_zone['avg_vol'] / avg_vol) if avg_vol > 0 else 50
        strength = max(10, min(100, strength))
        score = strength if zone_type == 'resistance' else -strength
        
        results.append({'date': row['date'], 'score': score, 'zone_type': zone_type})
    
    return pd.DataFrame(results)

# ============ 主计算 ============
print("\n开始计算...")

all_scores = []
for idx, stock in enumerate(stocks):
    if (idx + 1) % 50 == 0:
        print(f"进度: {idx+1}/{len(stocks)}")
    
    stock_df = df[df['股票代码'] == stock].copy()
    scores = calc_score_fast(stock_df)
    scores['stock'] = stock
    all_scores.append(scores)

print("合并结果...")
all_df = pd.concat(all_scores, ignore_index=True)

# 按日期汇总
print("汇总每日评分...")

# 为每只股票添加权重
def get_weight(stock_code):
    """从股票代码中提取纯数字代码并获取权重"""
    # stock_code格式: sh.600000 或 sz.000001
    pure_code = stock_code.split('.')[1] if '.' in stock_code else stock_code
    pure_code = str(pure_code).zfill(6)
    # 如果没有权重数据，使用等权重 (100/1000 = 0.1%)
    return weight_map.get(pure_code, 0.1)

daily_summary = []

for date in trade_dates:
    day_data = all_df[all_df['date'] == date].copy()
    if len(day_data) == 0:
        continue
    
    # 添加权重列
    day_data['weight'] = day_data['stock'].apply(get_weight)
    
    # 计算加权平均评分
    total_weight = day_data['weight'].sum()
    if total_weight > 0:
        weighted_score = (day_data['score'] * day_data['weight']).sum() / total_weight
    else:
        weighted_score = day_data['score'].mean()
    
    # 同时计算简单平均用于对比
    simple_avg = day_data['score'].mean()
    
    resistance_cnt = (day_data['zone_type'] == 'resistance').sum()
    support_cnt = (day_data['zone_type'] == 'support').sum()
    no_touch_cnt = (day_data['zone_type'] == 'no_touch').sum()
    
    daily_summary.append({
        'date': date.strftime('%Y-%m-%d'),
        'weighted_score': round(weighted_score, 2),
        'simple_score': round(simple_avg, 2),
        'resistance_count': resistance_cnt,
        'support_count': support_cnt,
        'no_touch_count': no_touch_cnt,
        'total_stocks': len(day_data),
        'total_weight': round(total_weight, 2)
    })

# 保存
result_df = pd.DataFrame(daily_summary)
output_file = f'daily_weighted_score_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
result_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print("\n" + "=" * 60)
print("计算完成！")
print(f"结果已保存到: {output_file}")
print(f"数据行数: {len(result_df)}")
print("\n最近10天数据预览:")
print(result_df.tail(10).to_string(index=False))
