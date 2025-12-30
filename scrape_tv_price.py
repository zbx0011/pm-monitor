"""
使用 Selenium 从 TradingView 网页抓取真实价格
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def get_tv_price(symbol, exchange='NYMEX'):
    """从 TradingView 获取真实价格"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 新版无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:7890')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # 禁用图片加载以加快速度
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    
    url = f"https://www.tradingview.com/symbols/{exchange}-{symbol}/"
    print(f"正在访问: {url}")
    
    try:
        driver.get(url)
        
        # 等待页面加载 - 尝试等待价格元素出现
        time.sleep(5)  # 给 JS 时间执行
        
        # 方法1: 从页面 title 获取（title 会动态更新）
        # 等待 title 包含数字
        for _ in range(10):
            title = driver.title
            print(f"  Title: {title}")
            # 尝试匹配 "PLJ2026 2345.6" 这样的格式
            match = re.search(r'([0-9,]+\.?\d*)\s*[▲▼]', title)
            if match:
                price = float(match.group(1).replace(',', ''))
                print(f"  从 Title 提取价格: {price}")
                return price
            time.sleep(1)
        
        # 方法2: 直接执行 JS 获取特定元素
        try:
            # TradingView 的价格通常在 data-test-id="price-last" 或类似属性中
            js_code = """
            // 尝试多种选择器
            const selectors = [
                '[data-test-id="price-last"]',
                '.js-symbol-last',
                '.tv-symbol-price-quote__value',
                'span[class*="last-"]'
            ];
            for (let sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.textContent) {
                    return el.textContent.trim();
                }
            }
            return null;
            """
            result = driver.execute_script(js_code)
            if result:
                price = float(result.replace(',', ''))
                print(f"  从 DOM 提取价格: {price}")
                return price
        except Exception as e:
            print(f"  JS 执行失败: {e}")
        
        # 方法3: 等待页面完全加载后再查找
        time.sleep(3)
        page_source = driver.page_source
        
        # 保存 HTML 用于调试
        with open('tv_debug.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("  已保存 HTML 到 tv_debug.html")
        
        return None
        
    except Exception as e:
        print(f"  错误: {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    # 测试获取 PLJ2026 价格
    symbols = ['PLJ2026', 'PLF2026', 'PLN2026']
    
    for sym in symbols:
        print(f"\n{'='*50}")
        print(f"获取 {sym} 价格...")
        price = get_tv_price(sym)
        if price:
            print(f"✅ {sym}: ${price}")
        else:
            print(f"❌ {sym}: 获取失败")
