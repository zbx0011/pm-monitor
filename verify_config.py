"""验证当前使用的合约配置和数据同步情况"""
import json

# 铂金
print("=" * 70)
print("铂金配置验证")
print("=" * 70)
with open('platinum_spread_analysis.json', 'r', encoding='utf-8') as f:
    pt = json.load(f)

print(f"广期所合约: {pt['contracts']['gfex']}")
print(f"CME合约: {pt['contracts']['cme']}")
print(f"\n最后3条数据 (验证同一时间匹配):")
print(f"{'时间':<20} | {'PT2610(元/克)':>14} | {'PLV2026(USD)':>14}")
print("-" * 55)
for h in pt['history'][-3:]:
    print(f"{h['date']:<20} | {h['gfex_price']:>14.2f} | {h['cme_usd']:>14.2f}")

# 钯金
print("\n" + "=" * 70)
print("钯金配置验证")
print("=" * 70)
with open('palladium_spread_analysis.json', 'r', encoding='utf-8') as f:
    pd_data = json.load(f)

print(f"广期所合约: {pd_data['contracts']['gfex']}")
print(f"CME合约: {pd_data['contracts']['cme']}")
print(f"\n最后3条数据 (验证同一时间匹配):")
print(f"{'时间':<20} | {'PD2606(元/克)':>14} | {'PAM2026(USD)':>14}")
print("-" * 55)
for h in pd_data['history'][-3:]:
    print(f"{h['date']:<20} | {h['gfex_price']:>14.2f} | {h['cme_usd']:>14.2f}")

print("\n" + "=" * 70)
