import json

data = json.load(open('platinum_spread_analysis.json', encoding='utf-8'))
print("检查12月24-26日的数据：")
for h in data['history']:
    if '12-24' in h['date'] or '12-25' in h['date'] or '12-26' in h['date']:
        print(f"广期所时间: {h['date']}, CME时间: {h['cme_time']}, CME价格: ${h['cme_usd']}")
