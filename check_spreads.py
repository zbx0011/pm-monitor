import json
d = json.load(open('platinum_all_pairs.json', encoding='utf-8'))
h = d.get('pairs', {}).get('2610-2610', {}).get('history', [])
dates = [x['date'] for x in h]
spreads = [x.get('spread_pct') for x in h]
print('=== Checking for null/None values in spreads ===')
null_count = sum(1 for s in spreads if s is None)
print(f'Null spread values: {null_count}')
# Check if any dates have weird format
print('=== Sample of date/spread pairs ===')
for i in [0, len(h)//4, len(h)//2, 3*len(h)//4, -1]:
    print(f'  [{i}]: date={h[i]["date"]}, spread={h[i].get("spread_pct", "MISSING")}')
