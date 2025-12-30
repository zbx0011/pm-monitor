
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

def login_tradingview():
    print("Opening Chrome for TradingView Login...")
    
    chrome_options = Options()
    
    # Use the same profile as the scraper
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    # NO HEADLESS MODE - So user can see and login
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("https://www.tradingview.com/accounts/signin/")
        print("\n" + "="*50)
        print("Please log in to TradingView in the opened browser window.")
        print("Once logged in, you can verify real-time data access.")
        print("Close the browser window when done.")
        print("="*50 + "\n")
        
        input("Press Enter here after you have closed the browser...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    login_tradingview()
