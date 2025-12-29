from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# 代理设置
PROXY = "127.0.0.1:7890"

def get_real_tv_price(symbol, exchange='NYMEX'):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式，不显示窗口
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f'--proxy-server=http://{PROXY}')
    
    # 伪装 User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    url = f"https://www.tradingview.com/symbols/{exchange}-{symbol}/"
    print(f"Browsing {url}...")
    
    try:
        driver.get(url)
        
        # 等待价格元素加载
        # data-symbol-last 属性通常存有最后价格，或者寻找具体的 class
        # 我们尝试找 class 包含 "last-" 且是数字的元素
        
        # TradingView 的价格通常在这个 class 里: "last-JWoJqCpY" (后缀随机)
        # 或者 data-test-id="instrument-price-last" (这个比较稳)
        
        # 方法1: 从 Title 提取 (最快且通常最稳)
        # Title 格式通常为: "Platinum Futures (Apr 2026) Price - 2325.1 USD - TradingView"
        page_title = driver.title
        print(f"Page Title: {page_title}")
        
        import re
        # 匹配 Price - 1234.5 USD
        # 或者 2325.1 USD
        match = re.search(r'Price\s*[-|:]\s*([\d,]+\.?\d*)', page_title)
        if not match:
            # 尝试直接找数字+USD
            match = re.search(r'([\d,]+\.?\d*)\s*USD', page_title)
            
        if match:
             price = float(match.group(1).replace(',', ''))
             print(f"Found Price from Title: {price}")
             return price

        # 如果 Title 还没更新（有时候Title是静态的），再尝试找元素
        wait = WebDriverWait(driver, 20)
        # 尝试更通用的选择器：找大号字体
        # 这里的 class 可能会变，但通常它是 role="img" 的兄弟或者特定的 data-test-id
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        driver.quit()

# Test
price = get_real_tv_price('PLJ2026', 'NYMEX')
print(f"Final Captured Price: {price}")
