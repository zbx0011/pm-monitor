import requests
import re
import os

# 必须使用代理访问 TradingView
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

def get_tv_price(symbol, exchange='NYMEX'):
    # 构造 URL: https://www.tradingview.com/symbols/NYMEX-PLJ2026/
    url = f"https://www.tradingview.com/symbols/{exchange}-{symbol}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"Scraping {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed: {response.status_code}")
            return None
            
        html = response.text
        
        # 使用正则提取价格
        # 价格通常在 class="last-JWoJqCpY" 或类似结构中，或者 title 中
        # <title>Platinum Futures (Apr 2026) Price - 2325.1 USD ...</title>
        
        # 方法1: 从 Title 提取 (最快)
        title_match = re.search(r'<title>.*?Price\s*-\s*([\d,]+\.?\d*)\s*USD', html)
        if title_match:
            price_str = title_match.group(1).replace(',', '')
            print(f"Method 1 (Title): {price_str}")
            return float(price_str)
            
        # 方法2: 查找特定的 class (可能变动)
        # last-JWoJqCpY js-symbol-last
        # 寻找包含 js-symbol-last 的元素内容
        price_match = re.search(r'class="[^"]*js-symbol-last[^"]*">([\d,]+\.?\d*)', html)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            print(f"Method 2 (Class): {price_str}")
            return float(price_str)

        print("Price not found in HTML.")
        # print first 500 chars of HTML for debug
        # print(html[:500]) 
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# 测试 PLJ2026
price = get_tv_price('PLJ2026', 'NYMEX')
print(f"Final Price: {price}")
