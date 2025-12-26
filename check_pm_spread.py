"""
铂金钯金跨市场价差检查脚本
获取广期所和国际市场的实时价格，计算价差
"""

import requests
from datetime import datetime
import json

# ============ 数据获取函数 ============

def fetch_gfex_price():
    """
    从广期所官网获取铂金钯金延迟行情
    数据来源: http://www.gfex.com.cn/gfex/rihq/hqsj_tjsj.shtml
    """
    print("📡 正在获取广期所数据...")
    
    try:
        # 尝试从新浪期货获取数据（更可靠）
        # PT2606 铂金2026年6月合约, PD2606 钯金2026年6月合约
        symbols = {
            'PT2606': 'https://hq.sinajs.cn/list=nf_PT2606',
            'PD2606': 'https://hq.sinajs.cn/list=nf_PD2606'
        }
        
        results = {}
        for symbol, url in symbols.items():
            headers = {
                'Referer': 'https://finance.sina.com.cn',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=10)
            
            # 解析新浪行情数据
            # 格式: var hq_str_nf_PT2606="铂金2606,568.45,531.30,568.45,568.45,531.30,568.45,568.45,..."
            if resp.status_code == 200:
                text = resp.text
                if '=' in text and '\"' in text:
                    data_str = text.split('\"')[1]
                    if data_str:
                        parts = data_str.split(',')
                        if len(parts) > 3:
                            results[symbol] = {
                                'name': parts[0],
                                'price': float(parts[3]) if parts[3] else None,  # 最新价
                                'open': float(parts[1]) if parts[1] else None,   # 今开
                                'prev_close': float(parts[2]) if parts[2] else None,  # 昨收
                            }
                            print(f"  ✓ {symbol}: {results[symbol]['price']} 元/克")
                    else:
                        print(f"  ✗ {symbol}: 无数据（可能非交易时间）")
                else:
                    print(f"  ✗ {symbol}: 数据格式异常")
            else:
                print(f"  ✗ {symbol}: 请求失败")
                
        return results
        
    except Exception as e:
        print(f"  ✗ 获取失败: {e}")
        return {}


def fetch_international_price():
    """
    获取国际铂金钯金现货价格
    使用免费API: metals-api (每月100次免费) 或爬取公开网站
    """
    print("\n📡 正在获取国际市场数据...")
    
    results = {}
    
    try:
        # 方案1: 从 kitco.com 爬取 (无需API key)
        url = "https://www.kitco.com/charts/liveplatinum.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 尝试从Google Finance获取
        # 注意: 这可能需要翻墙
        
        # 备选方案: 使用预设的市场价格（基于最新公开数据）
        # 你可以手动更新这些值，或者后续接入实时API
        print("  ⚠️ 使用预设国际价格（需接入API获取实时数据）")
        
        # 国际现货价格（美元/盎司）- 基于12月23日市场数据
        results['XPT'] = {
            'price_usd': 944.0,  # 铂金 USD/oz
            'source': '预设值(需更新)',
            'time': '2024-12-23'
        }
        results['XPD'] = {
            'price_usd': 988.0,  # 钯金 USD/oz
            'source': '预设值(需更新)',
            'time': '2024-12-23'
        }
        
        print(f"  ✓ XPT (铂金): ${results['XPT']['price_usd']}/盎司")
        print(f"  ✓ XPD (钯金): ${results['XPD']['price_usd']}/盎司")
        
        return results
        
    except Exception as e:
        print(f"  ✗ 获取失败: {e}")
        return {}


def fetch_exchange_rate():
    """
    获取美元兑人民币汇率
    """
    print("\n📡 正在获取汇率数据...")
    
    try:
        # 使用免费汇率API
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            rate = data['rates'].get('CNY', 7.30)
            print(f"  ✓ USD/CNY: {rate}")
            return rate
        else:
            print(f"  ⚠️ 使用预设汇率: 7.30")
            return 7.30
            
    except Exception as e:
        print(f"  ⚠️ 获取失败，使用预设汇率: 7.30")
        return 7.30


def calculate_spread(gfex_data, intl_data, exchange_rate):
    """
    计算套利价差
    """
    print("\n" + "="*60)
    print("📊 价差计算结果")
    print("="*60)
    
    # 单位换算常数
    OZ_TO_GRAM = 31.1035  # 1盎司 = 31.1035克
    
    results = []
    
    # 铂金计算
    if 'PT2606' in gfex_data and 'XPT' in intl_data:
        gfex_price = gfex_data['PT2606']['price']
        intl_price_usd = intl_data['XPT']['price_usd']
        
        # 国际价格换算为 元/克
        intl_price_cny_gram = intl_price_usd * exchange_rate / OZ_TO_GRAM
        
        spread = gfex_price - intl_price_cny_gram
        spread_pct = (spread / intl_price_cny_gram) * 100
        
        print(f"\n【铂金 Platinum】")
        print(f"  广期所 PT2606:    {gfex_price:.2f} 元/克")
        print(f"  国际现货换算:      {intl_price_cny_gram:.2f} 元/克")
        print(f"  (${intl_price_usd}/oz × {exchange_rate} ÷ 31.1)")
        print(f"  ────────────────────────────")
        print(f"  价差:              {spread:+.2f} 元/克")
        print(f"  溢价率:            {spread_pct:+.2f}%")
        
        if spread_pct > 0:
            print(f"  💡 套利方向: 做空广期所 + 做多国际市场")
        else:
            print(f"  💡 套利方向: 做多广期所 + 做空国际市场")
            
        results.append({
            'metal': '铂金',
            'gfex_price': gfex_price,
            'intl_price': intl_price_cny_gram,
            'spread': spread,
            'spread_pct': spread_pct
        })
    
    # 钯金计算
    if 'PD2606' in gfex_data and 'XPD' in intl_data:
        gfex_price = gfex_data['PD2606']['price']
        intl_price_usd = intl_data['XPD']['price_usd']
        
        intl_price_cny_gram = intl_price_usd * exchange_rate / OZ_TO_GRAM
        
        spread = gfex_price - intl_price_cny_gram
        spread_pct = (spread / intl_price_cny_gram) * 100
        
        print(f"\n【钯金 Palladium】")
        print(f"  广期所 PD2606:    {gfex_price:.2f} 元/克")
        print(f"  国际现货换算:      {intl_price_cny_gram:.2f} 元/克")
        print(f"  (${intl_price_usd}/oz × {exchange_rate} ÷ 31.1)")
        print(f"  ────────────────────────────")
        print(f"  价差:              {spread:+.2f} 元/克")
        print(f"  溢价率:            {spread_pct:+.2f}%")
        
        if spread_pct > 0:
            print(f"  💡 套利方向: 做空广期所 + 做多国际市场")
        else:
            print(f"  💡 套利方向: 做多广期所 + 做空国际市场")
            
        results.append({
            'metal': '钯金',
            'gfex_price': gfex_price,
            'intl_price': intl_price_cny_gram,
            'spread': spread,
            'spread_pct': spread_pct
        })
    
    return results


def main():
    print("="*60)
    print("🔍 铂金钯金跨市场套利价差检查")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 1. 获取广期所数据
    gfex_data = fetch_gfex_price()
    
    # 2. 获取国际市场数据
    intl_data = fetch_international_price()
    
    # 3. 获取汇率
    exchange_rate = fetch_exchange_rate()
    
    # 4. 计算价差
    if gfex_data and intl_data:
        results = calculate_spread(gfex_data, intl_data, exchange_rate)
        
        print("\n" + "="*60)
        print("⚠️  重要说明")
        print("="*60)
        print("1. 广期所数据来自新浪期货，有15-20分钟延迟")
        print("2. 国际价格目前使用预设值，需接入实时API")
        print("3. 如此大的价差可能反映市场定价差异而非套利机会")
        print("4. 实际套利需考虑: 交易成本、汇率风险、流动性、交割差异")
    else:
        print("\n❌ 数据获取不完整，无法计算价差")
        print("   可能原因: 非交易时间 或 网络问题")


if __name__ == "__main__":
    main()
