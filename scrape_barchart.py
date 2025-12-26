"""
从 Barchart 页面抓取 COMEX 特定月份合约历史数据
使用 Selenium 自动化抓取页面表格
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def scrape_barchart_table(symbol):
    """从 Barchart 页面抓取历史价格表格"""
    url = f"https://www.barchart.com/futures/quotes/{symbol}/price-history/historical"
    print(f"  抓取 {symbol}...")
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"    ✗ HTTP {resp.status_code}")
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 查找数据表格
        tables = soup.find_all('table')
        if not tables:
            print(f"    ✗ 未找到表格")
            return None
        
        # 查找包含 "Time" 或日期的表格
        data_table = None
        for table in tables:
            text = table.get_text()
            if 'Time' in text and 'Open' in text and 'High' in text:
                data_table = table
                break
        
        if not data_table:
            print(f"    ✗ 未找到数据表格")
            return None
        
        # 解析表头
        headers = [th.get_text(strip=True) for th in data_table.find_all('th')]
        
        # 解析数据行
        rows = []
        for tr in data_table.find_all('tr')[1:]:  # 跳过表头
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            if len(cells) >= 5 and '/' in cells[0]:  # 确保有日期
                rows.append(cells)
        
        if not rows:
            print(f"    ✗ 表格无数据行")
            return None
        
        # 转换为 DataFrame
        df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
        
        # 处理日期和价格
        df['date'] = pd.to_datetime(df['Time'], format='%m/%d/%Y', errors='coerce')
        df['close'] = pd.to_numeric(df['Last'].str.replace(',', '').str.replace('s', ''), errors='coerce')
        df = df.dropna(subset=['date', 'close'])
        df = df.set_index('date').sort_index()
        
        print(f"    ✓ {len(df)}条数据 ({df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')})")
        return df[['close']]
        
    except Exception as e:
        print(f"    ✗ 错误: {e}")
        return None


def main():
    print("=" * 60)
    print("从 Barchart 抓取 COMEX 特定月份合约数据")
    print("=" * 60)
    
    # 测试一个合约
    df = scrape_barchart_table('GCZ24')
    
    if df is not None:
        print("\n样本数据:")
        print(df.tail(10))


if __name__ == "__main__":
    main()
