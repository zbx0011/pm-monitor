"""
富途CME期货数据获取脚本
获取铂金(PL)和钯金(PA)期货的合约列表和实时价格
"""

import json
from datetime import datetime

try:
    from futu import *
except ImportError:
    print("请安装 futu-api: pip install futu-api")
    exit(1)

# CME铂金和钯金期货代码
# 富途的期货代码格式: US.PLmain (主连), US.PL2601 (具体月份)
PLATINUM_CODES = [
    "US.PLmain",  # 铂金主连
    "US.PL2512",  # 2025年12月
    "US.PL2601",  # 2026年1月
    "US.PL2602",  # 2026年2月
    "US.PL2603",  # 2026年3月
    "US.PL2604",  # 2026年4月
    "US.PL2606",  # 2026年6月 (可能不存在)
    "US.PL2607",  # 2026年7月
    "US.PL2609",  # 2026年9月
    "US.PL2610",  # 2026年10月
    "US.PL2612",  # 2026年12月
]

PALLADIUM_CODES = [
    "US.PAmain",  # 钯金主连
    "US.PA2512",  # 2025年12月
    "US.PA2601",  # 2026年1月
    "US.PA2602",  # 2026年2月
    "US.PA2603",  # 2026年3月
    "US.PA2604",  # 2026年4月
    "US.PA2606",  # 2026年6月
    "US.PA2607",  # 2026年7月
    "US.PA2609",  # 2026年9月
    "US.PA2610",  # 2026年10月
    "US.PA2612",  # 2026年12月
]

def get_futures_quotes(quote_ctx, codes):
    """获取期货报价"""
    results = []
    
    for code in codes:
        try:
            ret, data = quote_ctx.get_market_snapshot([code])
            if ret == RET_OK and not data.empty:
                row = data.iloc[0]
                results.append({
                    "code": code,
                    "name": row.get("name", code),
                    "last_price": float(row.get("last_price", 0)),
                    "open_price": float(row.get("open_price", 0)),
                    "high_price": float(row.get("high_price", 0)),
                    "low_price": float(row.get("low_price", 0)),
                    "prev_close": float(row.get("prev_close_price", 0)),
                    "volume": int(row.get("volume", 0)),
                    "update_time": row.get("update_time", ""),
                    "available": True
                })
            else:
                results.append({
                    "code": code,
                    "available": False,
                    "error": "数据不可用"
                })
        except Exception as e:
            results.append({
                "code": code,
                "available": False,
                "error": str(e)
            })
    
    return results

def main():
    print("正在连接富途OpenD...")
    print("注意: 需要先启动富途的OpenD网关程序")
    print("下载地址: https://openapi.futunn.com/futu-api-doc/opend/opend-cmd.html")
    print()
    
    try:
        # 连接到OpenD (默认本地 127.0.0.1:11111)
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        
        print("连接成功! 正在获取期货数据...")
        print()
        
        # 获取铂金期货数据
        print("=" * 50)
        print("CME 铂金期货 (PL)")
        print("=" * 50)
        platinum_data = get_futures_quotes(quote_ctx, PLATINUM_CODES)
        
        available_pt = []
        for item in platinum_data:
            if item.get("available"):
                print(f"  ✓ {item['code']}: ${item['last_price']:.2f}")
                available_pt.append(item)
            else:
                print(f"  ✗ {item['code']}: 不可用")
        
        print()
        
        # 获取钯金期货数据
        print("=" * 50)
        print("CME 钯金期货 (PA)")
        print("=" * 50)
        palladium_data = get_futures_quotes(quote_ctx, PALLADIUM_CODES)
        
        available_pd = []
        for item in palladium_data:
            if item.get("available"):
                print(f"  ✓ {item['code']}: ${item['last_price']:.2f}")
                available_pd.append(item)
            else:
                print(f"  ✗ {item['code']}: 不可用")
        
        # 保存数据到JSON文件
        output_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platinum": platinum_data,
            "palladium": palladium_data,
            "available_platinum_contracts": [x["code"] for x in available_pt],
            "available_palladium_contracts": [x["code"] for x in available_pd],
        }
        
        with open("futu_cme_futures.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"数据已保存到 futu_cme_futures.json")
        print()
        print("可用铂金合约:", [x["code"].split(".")[-1] for x in available_pt])
        print("可用钯金合约:", [x["code"].split(".")[-1] for x in available_pd])
        
        # 关闭连接
        quote_ctx.close()
        
    except Exception as e:
        print(f"连接失败: {e}")
        print()
        print("请确保:")
        print("1. 已下载并安装 OpenD 网关")
        print("2. OpenD 已启动并登录富途账户")
        print("3. 防火墙允许 11111 端口")
        print()
        print("下载OpenD: https://openapi.futunn.com/futu-api-doc/opend/opend-cmd.html")

if __name__ == "__main__":
    main()
