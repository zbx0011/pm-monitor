"""
使用yfinance获取CME铂金钯金期货数据 (优化版)
使用history方法避免限流
"""

import json
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    print("请安装yfinance: pip install yfinance")
    exit(1)

def get_futures_data():
    """获取CME铂金钯金期货数据"""
    
    result = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "platinum": {},
        "palladium": {},
        "exchange_rate": 7.04
    }
    
    OZ_TO_GRAM = 31.1035
    
    # 铂金期货 - 使用history方法
    print("正在获取铂金期货数据...")
    try:
        pl = yf.download("PL=F", period="5d", progress=False)
        if len(pl) > 0:
            last_price = float(pl['Close'].iloc[-1])
            prev_close = float(pl['Close'].iloc[-2]) if len(pl) > 1 else last_price
            result["platinum"] = {
                "symbol": "PL=F",
                "name": "CME铂金期货",
                "price_usd": round(last_price, 2),
                "prev_close": round(prev_close, 2),
                "day_high": round(float(pl['High'].iloc[-1]), 2),
                "day_low": round(float(pl['Low'].iloc[-1]), 2),
                "available": True
            }
            print(f"  ✓ 铂金: ${last_price:.2f}/oz")
        else:
            result["platinum"] = {"available": False, "error": "无数据"}
    except Exception as e:
        result["platinum"] = {"available": False, "error": str(e)}
        print(f"  ✗ 铂金获取失败: {e}")
    
    # 钯金期货
    print("正在获取钯金期货数据...")
    try:
        pa = yf.download("PA=F", period="5d", progress=False)
        if len(pa) > 0:
            last_price = float(pa['Close'].iloc[-1])
            prev_close = float(pa['Close'].iloc[-2]) if len(pa) > 1 else last_price
            result["palladium"] = {
                "symbol": "PA=F",
                "name": "CME钯金期货",
                "price_usd": round(last_price, 2),
                "prev_close": round(prev_close, 2),
                "day_high": round(float(pa['High'].iloc[-1]), 2),
                "day_low": round(float(pa['Low'].iloc[-1]), 2),
                "available": True
            }
            print(f"  ✓ 钯金: ${last_price:.2f}/oz")
        else:
            result["palladium"] = {"available": False, "error": "无数据"}
    except Exception as e:
        result["palladium"] = {"available": False, "error": str(e)}
        print(f"  ✗ 钯金获取失败: {e}")
    
    # 获取美元兑人民币汇率
    print("正在获取汇率...")
    try:
        fx = yf.download("USDCNY=X", period="5d", progress=False)
        if len(fx) > 0:
            result["exchange_rate"] = round(float(fx['Close'].iloc[-1]), 4)
            print(f"  ✓ 汇率: {result['exchange_rate']}")
    except Exception as e:
        print(f"  ⚠ 汇率获取失败，使用默认值7.04")
    
    return result

def main():
    print("=" * 50)
    print("CME 铂金钯金期货数据获取")
    print("=" * 50)
    print()
    
    data = get_futures_data()
    
    # 保存到JSON文件
    with open("cme_futures_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 50)
    print("数据汇总 (换算为人民币/克)")
    print("=" * 50)
    
    OZ_TO_GRAM = 31.1035
    rate = data["exchange_rate"]
    
    if data["platinum"].get("available"):
        pt_usd = data["platinum"]["price_usd"]
        pt_cny_gram = (pt_usd * rate) / OZ_TO_GRAM
        print(f"铂金: ${pt_usd}/oz = ¥{pt_cny_gram:.2f}/克")
    
    if data["palladium"].get("available"):
        pd_usd = data["palladium"]["price_usd"]
        pd_cny_gram = (pd_usd * rate) / OZ_TO_GRAM
        print(f"钯金: ${pd_usd}/oz = ¥{pd_cny_gram:.2f}/克")
    
    print()
    print(f"数据已保存到 cme_futures_data.json")
    print(f"更新时间: {data['update_time']}")

if __name__ == "__main__":
    main()
