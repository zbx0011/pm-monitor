"""
使用 Selenium 从 Barchart 自动抓取 COMEX 特定月份合约历史数据
"""
import time
import pandas as pd
from datetime import datetime
import json
import akshare as ak

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

OZ_TO_GRAM = 31.1035
RATE = 7.04
OZ_PER_KG = 32.1507

# COMEX 合约配置
CONTRACTS = [
    {'domestic': 'AU2412', 'comex': 'GCZ24', 'name': '黄金2024.12', 'type': 'gold'},
    {'domestic': 'AU2406', 'comex': 'GCM24', 'name': '黄金2024.06', 'type': 'gold'},
    {'domestic': 'AU2312', 'comex': 'GCZ23', 'name': '黄金2023.12', 'type': 'gold'},
    {'domestic': 'AU2306', 'comex': 'GCM23', 'name': '黄金2023.06', 'type': 'gold'},
    {'domestic': 'AG2412', 'comex': 'SIZ24', 'name': '白银2024.12', 'type': 'silver'},
    {'domestic': 'AG2406', 'comex': 'SIM24', 'name': '白银2024.06', 'type': 'silver'},
]


def create_driver():
    """创建 Chrome 浏览器实例"""
    options = Options()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def scrape_barchart(driver, symbol):
    """从 Barchart 抓取历史数据"""
    url = f"https://www.barchart.com/futures/quotes/{symbol}/price-history/historical"
    print(f"  抓取 {symbol}...")
    
    try:
        driver.get(url)
        time.sleep(3)  # 等待页面加载
        
        # 关闭可能的弹窗
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, '.bc-iam-close, .bz-close-btn')
            close_btn.click()
            time.sleep(0.5)
        except:
            pass
        
        # 等待表格加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table tbody tr'))
        )
        
        # 提取表格数据
        rows = driver.execute_script("""
            const table = document.querySelector('table');
            if (!table) return [];
            
            const data = [];
            const trs = table.querySelectorAll('tbody tr');
            trs.forEach(tr => {
                const cells = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                if (cells.length >= 5 && cells[0].includes('/')) {
                    data.push({
                        date: cells[0],
                        open: cells[1],
                        high: cells[2],
                        low: cells[3],
                        close: cells[4]
                    });
                }
            });
            return data;
        """)
        
        if not rows:
            print(f"    ✗ 未找到数据")
            return None
        
        # 转换为 DataFrame
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
        df['close'] = pd.to_numeric(df['close'].str.replace(',', '').str.replace('s', ''), errors='coerce')
        df = df.dropna(subset=['date', 'close'])
        df = df.set_index('date').sort_index()
        
        print(f"    ✓ {len(df)}条数据 ({df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')})")
        return df[['close']]
        
    except Exception as e:
        print(f"    ✗ 错误: {e}")
        return None


def process_contract(driver, config):
    """处理单个合约对"""
    print(f"\n处理 {config['domestic']} vs {config['comex']}...")
    
    # 获取国内数据
    try:
        dom = ak.futures_zh_daily_sina(symbol=config['domestic'])
        dom['date'] = pd.to_datetime(dom['date'])
        dom = dom.set_index('date').sort_index()
        dom['close'] = pd.to_numeric(dom['close'], errors='coerce')
        print(f"  国内: {len(dom)}条")
    except Exception as e:
        print(f"  ✗ 国内数据失败: {e}")
        return None
    
    # 获取 COMEX 数据
    intl = scrape_barchart(driver, config['comex'])
    if intl is None:
        return None
    
    # 对齐日期
    common_dates = dom.index.intersection(intl.index)
    if len(common_dates) < 10:
        print(f"  ✗ 共同日期不足 ({len(common_dates)}天)")
        return None
    
    dom = dom.loc[common_dates]
    intl = intl.loc[common_dates]
    
    # 单位转换
    if config['type'] == 'gold':
        intl_cny = (intl['close'] * RATE) / OZ_TO_GRAM
    else:
        intl_cny = intl['close'] * OZ_PER_KG * RATE
    
    spread_pct = ((dom['close'] - intl_cny) / intl_cny) * 100
    
    # 构建结果
    history = []
    for date in common_dates:
        history.append({
            'date': date.strftime('%Y-%m-%d'),
            'domestic': float(dom.loc[date, 'close']),
            'comex': float(intl.loc[date, 'close']),
            'comex_cny': float(intl_cny.loc[date]),
            'spread_pct': float(spread_pct.loc[date])
        })
    
    return {
        'symbol': config['domestic'],
        'comex_symbol': config['comex'],
        'name': config['name'],
        'start_date': common_dates.min().strftime('%Y-%m-%d'),
        'end_date': common_dates.max().strftime('%Y-%m-%d'),
        'days': len(common_dates),
        'start_spread': float(spread_pct.iloc[0]),
        'end_spread': float(spread_pct.iloc[-1]),
        'convergence': float(spread_pct.iloc[0] - spread_pct.iloc[-1]),
        'history': history
    }


def main():
    print("=" * 60)
    print("COMEX 特定月份合约收敛分析 (Selenium)")
    print("=" * 60)
    
    driver = None
    results = []
    
    try:
        driver = create_driver()
        
        for config in CONTRACTS:
            data = process_contract(driver, config)
            if data:
                results.append(data)
                print(f"  ✓ 价差 {data['start_spread']:.1f}% -> {data['end_spread']:.1f}%")
            time.sleep(2)  # 防止被封
        
    finally:
        if driver:
            driver.quit()
    
    if results:
        output = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': {
                'domestic': '新浪期货 (上期所特定月份合约)',
                'international': 'Barchart (COMEX特定月份合约)'
            },
            'contracts': results,
        }
        
        with open('contract_convergence_data.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print("✓ 数据已保存到 contract_convergence_data.json")
        print(f"{'='*60}")
    else:
        print("\n✗ 未能获取任何数据")


if __name__ == "__main__":
    main()
