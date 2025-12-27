import akshare as ak
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
from datetime import datetime
import time

# 代理设置
proxies = {
    'http': 'http://127.0.0.1:4780',
    'https': 'http://127.0.0.1:4780'
}

def check_gfex_contracts():
    print("正在检查广期所钯金合约...")
    # 广期所合约通常是偶数月份
    contracts = ['PD2602', 'PD2604', 'PD2606', 'PD2608', 'PD2610', 'PD2612']
    available = []
    
    for contract in contracts:
        try:
            df = ak.futures_zh_minute_sina(symbol=contract, period='60')
            if df is not None and not df.empty:
                last_time = df.iloc[-1]['datetime']
                last_price = df.iloc[-1]['close']
                print(f"  ✓ {contract}: 可用 (最新: {last_time}, 价格: {last_price})")
                available.append(contract)
            else:
                print(f"  x {contract}: 无数据")
        except Exception as e:
            print(f"  x {contract}: 获取失败 ({e})")
            
    return available

def check_cme_contracts():
    print("\n正在检查CME钯金合约 (2026)...")
    tv = TvDatafeed()
    
    # CME 钯金合约代码 (PA)
    # 月份代码: F(1), G(2), H(3), J(4), K(5), M(6), N(7), Q(8), U(9), V(10), X(11), Z(12)
    # 活跃合约通常是 3(H), 6(M), 9(U), 12(Z)
    months = {
        'H': '03', 'M': '06', 'U': '09', 'Z': '12'
    }
    
    available = []
    
    for code, month_num in months.items():
        symbol = f"PA{code}2026"
        try:
            df = tv.get_hist(symbol=symbol, exchange='NYMEX', interval=Interval.in_1_hour, n_bars=10)
            if df is not None and not df.empty:
                last_price = df.iloc[-1]['close']
                print(f"  ✓ {symbol} (26{month_num}): 可用 (价格: {last_price})")
                available.append({'symbol': symbol, 'name': f"26{month_num}"})
            else:
                print(f"  x {symbol}: 无数据")
        except Exception as e:
            print(f"  x {symbol}: 获取失败")
            
    return available

if __name__ == "__main__":
    gfex_list = check_gfex_contracts()
    cme_list = check_cme_contracts()
    
    print("\n=== 探测结果汇总 ===")
    print(f"广期所可用: {', '.join(gfex_list)}")
    print(f"CME可用: {', '.join([c['symbol'] for c in cme_list])}")
