
from tv_scraper import TradingViewScraper
import datetime

def test_scraper():
    scraper = TradingViewScraper(use_profile=True)
    symbol = "PLJ2026"
    exchange = "NYMEX"
    
    print(f"[{datetime.datetime.now()}] Fetching {exchange}:{symbol}...")
    try:
        price, time_fetched = scraper.get_price_with_time(symbol, exchange)
        print(f"Result: Price={price}, Time={time_fetched}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_scraper()
