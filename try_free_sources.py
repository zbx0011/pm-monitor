"""
从 Investing.com 获取 COMEX 特定月份合约历史数据
"""
import requests
import pandas as pd
from datetime import datetime
import json
import time

# Investing.com 的合约页面
# 例如 https://www.investing.com/commodities/gold-historical-data
# 需要找到特定合约的页面

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

def try_investing_com():
    """尝试从 Investing.com 获取数据"""
    print("尝试 Investing.com...")
    
    # 黄金期货历史数据页面
    url = "https://www.investing.com/commodities/gold-historical-data"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            # 检查是否包含数据
            if "historical-data" in resp.text.lower():
                print("  ✓ 页面可访问")
                return True
        return False
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        return False


def try_barchart():
    """尝试从 Barchart 获取 GCZ24 数据"""
    print("\n尝试 Barchart...")
    
    # Barchart API endpoint (需要登录才能下载完整数据)
    url = "https://www.barchart.com/proxies/core-api/v1/historical/get"
    params = {
        "symbol": "GCZ24",
        "type": "daily",
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "orderBy": "date",
        "order": "asc"
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  数据: {data}")
            return data
    except Exception as e:
        print(f"  ✗ 失败: {e}")
    
    return None


def try_cme_group():
    """尝试从 CME Group 官网获取数据"""
    print("\n尝试 CME Group...")
    
    # CME Group 有免费的结算价数据
    # https://www.cmegroup.com/markets/metals/precious/gold.settlements.html
    url = "https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/425/FUT"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            print("  ✓ 可访问")
            return resp.json()
    except Exception as e:
        print(f"  ✗ 失败: {e}")
    
    return None


def try_nasdaq_data_link():
    """尝试 Nasdaq Data Link (原 Quandl) 的免费数据"""
    print("\n尝试 Nasdaq Data Link (Quandl)...")
    
    # CHRIS/CME_GC1 是黄金近月连续, 但可能有特定合约
    url = "https://data.nasdaq.com/api/v3/datasets/CHRIS/CME_GC1.json"
    params = {
        "rows": 5,
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'dataset' in data:
                print(f"  ✓ 数据集: {data['dataset']['name']}")
                print(f"  列: {data['dataset']['column_names']}")
                return data
    except Exception as e:
        print(f"  ✗ 失败: {e}")
    
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("尝试各种免费数据源获取 COMEX 特定月份合约")
    print("=" * 60)
    
    try_investing_com()
    try_barchart()
    try_cme_group()
    try_nasdaq_data_link()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
