"""
TradingView 价格爬虫
使用 Selenium 从 TradingView 网页获取准确的 CME 期货价格
"""
import os
# 先不设置代理，让 webdriver-manager 能正常下载
# 浏览器内部会通过系统代理访问

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

class TradingViewScraper:
    def __init__(self, proxy="127.0.0.1:7890"):
        self.proxy = proxy
        self.driver = None
        
    def _init_driver(self):
        """初始化 Chrome 驱动"""
        if self.driver is not None:
            return
        
        # 临时清除环境代理，避免 webdriver-manager 下载失败
        saved_http_proxy = os.environ.pop('HTTP_PROXY', None)
        saved_https_proxy = os.environ.pop('HTTPS_PROXY', None)
        saved_http_proxy_lower = os.environ.pop('http_proxy', None)
        saved_https_proxy_lower = os.environ.pop('https_proxy', None)
            
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # 使用代理访问 TradingView
        if self.proxy:
            chrome_options.add_argument(f'--proxy-server={self.proxy}')
        
        # 禁用图片加载
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(30)
        
        # 恢复代理设置
        if saved_http_proxy:
            os.environ['HTTP_PROXY'] = saved_http_proxy
        if saved_https_proxy:
            os.environ['HTTPS_PROXY'] = saved_https_proxy
        if saved_http_proxy_lower:
            os.environ['http_proxy'] = saved_http_proxy_lower
        if saved_https_proxy_lower:
            os.environ['https_proxy'] = saved_https_proxy_lower
        
    def get_price_with_time(self, symbol, exchange='NYMEX'):
        """获取指定合约的价格和实际时间戳"""
        self._init_driver()
        
        url = f"https://www.tradingview.com/symbols/{exchange}-{symbol}/"
        print(f"  爬取 {url}...")
        
        price = None
        data_time = None
        
        try:
            self.driver.get(url)
            time.sleep(4)  # 等待 JS 执行
            
            # 获取价格
            # 方法1: 从 title 获取
            for _ in range(10):
                title = self.driver.title
                match = re.search(r'([0-9,]+\.?\d*)\s*[▲▼]', title)
                if match:
                    price = float(match.group(1).replace(',', ''))
                    print(f"    ✓ 价格: ${price}")
                    break
                time.sleep(0.5)
            
            # 方法2: 从 DOM 获取价格
            if price is None:
                try:
                    selectors = [
                        'span[class*="last-"]',
                        '[data-test-id="qc-price"]',
                        '.tv-symbol-price-quote__value'
                    ]
                    for selector in selectors:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for el in elements:
                            text = el.text.strip().replace(',', '')
                            if text and re.match(r'^\d+\.?\d*$', text):
                                p = float(text)
                                if p > 100:
                                    price = p
                                    print(f"    ✓ 价格: ${price}")
                                    break
                        if price:
                            break
                except Exception as e:
                    print(f"    DOM 查找失败: {e}")
            
            # 获取时间戳 - TradingView 免费版数据延迟约 10-15 分钟
            # 直接使用当前时间减去 15 分钟作为估算的数据时间
            from datetime import datetime, timedelta
            data_time = datetime.now() - timedelta(minutes=15)
            print(f"    ✓ 估算数据时间: {data_time.strftime('%Y-%m-%d %H:%M')} (当前时间 -15分钟)")
            
            if price is None:
                print(f"    ✗ 未能获取价格")
                
            return price, data_time
            
        except Exception as e:
            print(f"    ✗ 错误: {e}")
            return None, None
    
    def get_price(self, symbol, exchange='NYMEX'):
        """获取指定合约的价格（兼容旧接口）"""
        price, _ = self.get_price_with_time(symbol, exchange)
        return price
            
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None


def get_cme_prices():
    """获取所有 CME 铂金合约价格"""
    scraper = TradingViewScraper()
    
    contracts = {
        'PLF2026': '2026年1月',
        'PLJ2026': '2026年4月',
        'PLN2026': '2026年7月',
        'PLV2026': '2026年10月',
    }
    
    prices = {}
    
    try:
        print("=" * 50)
        print("TradingView 价格爬取")
        print("=" * 50)
        
        for symbol, name in contracts.items():
            print(f"\n获取 {symbol} ({name})...")
            price = scraper.get_price(symbol, 'NYMEX')
            if price:
                prices[symbol] = price
                
    finally:
        scraper.close()
        
    return prices


if __name__ == "__main__":
    prices = get_cme_prices()
    
    print("\n" + "=" * 50)
    print("结果汇总")
    print("=" * 50)
    for sym, price in prices.items():
        print(f"  {sym}: ${price}")
