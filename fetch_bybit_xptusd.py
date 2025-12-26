"""
获取Bybit XPTUSD历史K线数据
用于计算CME-Bybit基差
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time

def fetch_bybit_kline(symbol="XPTUSD", interval="D", limit=1000):
    """
    使用Bybit REST API获取历史K线数据
    interval: D=日线, 60=小时线
    limit: 最多1000条
    """
    url = "https://api.bybit.com/v5/market/kline"
    
    all_data = []
    end_time = int(datetime.now().timestamp() * 1000)
    
    # 获取3年数据需要多次请求
    for _ in range(4):  # 4次 x 1000天 = 约3年
        params = {
            "category": "linear",  # USDT永续
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "end": end_time
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get("retCode") != 0:
                print(f"API错误: {data.get('retMsg')}")
                break
                
            klines = data.get("result", {}).get("list", [])
            if not klines:
                break
                
            all_data.extend(klines)
            
            # 下一批从最早时间往前
            earliest = int(klines[-1][0])
            end_time = earliest - 1
            
            print(f"  已获取 {len(all_data)} 条数据...")
            time.sleep(0.5)  # 避免限流
            
        except Exception as e:
            print(f"请求失败: {e}")
            break
    
    if not all_data:
        return pd.DataFrame()
    
    # 转换为DataFrame
    # Bybit K线格式: [startTime, open, high, low, close, volume, turnover]
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
    df['timestamp'] = pd.to_numeric(df['timestamp'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = pd.to_numeric(df['close'])
    df = df.set_index('date').sort_index()
    
    return df[['close']]


def main():
    print("=" * 60)
    print("获取Bybit XPTUSD历史数据")
    print("=" * 60)
    
    print("\n正在从Bybit获取XPTUSD日线数据...")
    df = fetch_bybit_kline(symbol="XPTUSD", interval="D", limit=1000)
    
    if df.empty:
        print("✗ 未能获取到数据")
        return
    
    print(f"✓ 获取到 {len(df)} 条数据")
    print(f"  范围: {df.index.min()} ~ {df.index.max()}")
    print(f"  最新价: ${df['close'].iloc[-1]:.2f}")
    
    # 保存为JSON
    history = []
    for date, row in df.iterrows():
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "bybit_xptusd": float(row['close'])
        })
    
    output = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": "XPTUSD",
        "source": "Bybit",
        "count": len(history),
        "history": history
    }
    
    with open("bybit_xptusd_history.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 数据已保存到 bybit_xptusd_history.json")


if __name__ == "__main__":
    main()
