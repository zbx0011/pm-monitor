import akshare as ak
import pandas as pd

print("=" * 70)
print("数据来源验证 - 请与外部行情软件对比")
print("=" * 70)

# AU2412 (上期所2024年12月黄金合约)
print("\n【上期所 AU2412】")
au = ak.futures_zh_daily_sina(symbol='AU2412')
au.columns = [c.strip() for c in au.columns]
print(f"数据来源: 新浪期货 via akshare")
print(f"样本数据 (最后5天):")
print(au.tail(5).to_string(index=False))

# XAU (COMEX黄金)
print("\n【COMEX XAU】")
xau = ak.futures_foreign_hist(symbol='XAU')
xau.columns = [c.strip() for c in xau.columns]
print(f"数据来源: 新浪期货 via akshare")
print(f"样本数据 (最后5天):")
print(xau.tail(5).to_string(index=False))

# AG2412 (上期所2024年12月白银合约)
print("\n【上期所 AG2412】")
ag = ak.futures_zh_daily_sina(symbol='AG2412')
ag.columns = [c.strip() for c in ag.columns]
print(f"数据来源: 新浪期货 via akshare")
print(f"样本数据 (最后5天):")
print(ag.tail(5).to_string(index=False))

# XAG (COMEX白银)
print("\n【COMEX XAG】")
xag = ak.futures_foreign_hist(symbol='XAG')
xag.columns = [c.strip() for c in xag.columns]
print(f"数据来源: 新浪期货 via akshare")
print(f"样本数据 (最后5天):")
print(xag.tail(5).to_string(index=False))

print("\n" + "=" * 70)
print("请对比上述数据与东方财富/同花顺/文华财经等软件是否一致")
print("=" * 70)
