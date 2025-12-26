import json

d = json.load(open('contract_convergence_data.json', encoding='utf-8'))

print("=" * 60)
print("验证: 收敛分析数据样本")
print("=" * 60)

for c in d['contracts']:
    print(f"\n【{c['symbol']} ({c['name']})】")
    print(f"  数据范围: {c['start_date']} ~ {c['end_date']}")
    print(f"  上市价差: {c['start_spread']:.2f}%")
    print(f"  交割价差: {c['end_spread']:.2f}%")
    
    # 显示最后3条数据
    print("  最后3天数据:")
    for h in c['history'][-3:]:
        print(f"    {h['date']}: 国内={h['close']}, 国际折算={h['intl_cny']:.2f}, 价差={h['spread_pct']:.2f}%")
