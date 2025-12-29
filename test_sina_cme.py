import requests
import json
import time

def check_sina_future(symbol):
    t = int(time.time() * 1000)
    # 新浪财经外盘期货接口
    # hf_PL 是铂金主连，我们需要找具体合约
    # 尝试一些可能的代码组合: hf_PLJ26, hf_PL2604
    
    url = f"http://hq.sinajs.cn/list={symbol}"
    try:
        r = requests.get(url, headers={'Referer': 'http://finance.sina.com.cn/'})
        print(f"{symbol}: {r.text}")
    except Exception as e:
        print(f"Error {symbol}: {e}")

# 常用代码猜测
codes = [
    'hf_PL',      # 主连
    'hf_PLJ2026',
    'hf_PLJ26',
    'hf_PL2604',
    'hf_NYMEXPL'  
]

print("Trying Sina Finance...")
for c in codes:
    check_sina_future(c)
