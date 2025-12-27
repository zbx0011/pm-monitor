import json

RATE = 7.04
OZ_TO_GRAM = 31.1035

# 铂金历史数据
with open('platinum_spread_analysis.json', 'r', encoding='utf-8') as f:
    pt_data = json.load(f)

pt_history = pt_data['history']
pt_daily = {}
for h in pt_history:
    date = h['date'].split(' ')[0]
    if '15:00' in h['date']:
        pt_daily[date] = h

pt_dates = sorted(pt_daily.keys())[-5:]
pt_samples = [pt_daily[d] for d in pt_dates]

print("=" * 90)
print("【铂金 Platinum】- PT2610 vs PLV2026 (2026年10月)")
print("=" * 90)
print(f"{'日期':<12} | {'广期所(元/克)':>14} | {'CME(USD/oz)':>14} | {'价差(元/克)':>12} | {'溢价%':>8}")
print("-" * 90)
for h in pt_samples:
    cme_usd = h['cme_cny'] * OZ_TO_GRAM / RATE  # 反推CME USD价格
    print(f"{h['date'].split(' ')[0]:<12} | {h['gfex_price']:>14.2f} | {cme_usd:>14.2f} | {h['spread']:>+12.2f} | {h['spread_pct']:>+8.2f}%")

# 钯金历史数据
with open('palladium_spread_analysis.json', 'r', encoding='utf-8') as f:
    pd_data = json.load(f)

pd_history = pd_data['history']
pd_daily = {}
for h in pd_history:
    date = h['date'].split(' ')[0]
    if '15:00' in h['date']:
        pd_daily[date] = h

pd_dates = sorted(pd_daily.keys())[-5:]
pd_samples = [pd_daily[d] for d in pd_dates]

print("\n" + "=" * 90)
print("【钯金 Palladium】- PD2606 vs PAM2026 (2026年6月)")
print("=" * 90)
print(f"{'日期':<12} | {'广期所(元/克)':>14} | {'CME(USD/oz)':>14} | {'价差(元/克)':>12} | {'溢价%':>8}")
print("-" * 90)
for h in pd_samples:
    cme_usd = h['cme_cny'] * OZ_TO_GRAM / RATE
    print(f"{h['date'].split(' ')[0]:<12} | {h['gfex_price']:>14.2f} | {cme_usd:>14.2f} | {h['spread']:>+12.2f} | {h['spread_pct']:>+8.2f}%")

print("\n" + "=" * 90)
print("汇率: 7.04 | 1盎司 = 31.1035克")
print("=" * 90)
