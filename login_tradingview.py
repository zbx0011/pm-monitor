"""
TradingView 登录脚本
打开浏览器让用户手动登录 TradingView，保存登录状态到 chrome_profile 目录
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def main():
    print("=" * 60)
    print("TradingView 登录助手")
    print("=" * 60)
    print()
    print("即将打开 Chrome 浏览器，请手动登录您的 TradingView 付费账号")
    print("登录成功后，关闭浏览器窗口即可")
    print()
    
    # Chrome 配置
    chrome_options = Options()
    profile_dir = os.path.join(os.path.dirname(__file__), 'chrome_profile')
    
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        print(f"创建配置目录: {profile_dir}")
    
    chrome_options.add_argument(f'--user-data-dir={profile_dir}')
    chrome_options.add_argument("--start-maximized")
    
    # 启动浏览器
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 打开 TradingView 登录页面
    print("\n正在打开 TradingView...")
    driver.get("https://www.tradingview.com/")
    
    print()
    print("=" * 60)
    print("请在浏览器中登录您的 TradingView 账号")
    print("登录完成后，直接关闭浏览器窗口即可")
    print("=" * 60)
    
    # 等待用户关闭浏览器
    try:
        while True:
            try:
                _ = driver.title
            except:
                break
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    print("\n✓ 登录状态已保存！")
    print("现在爬虫将自动使用您的付费账号获取实时数据")

if __name__ == "__main__":
    main()
