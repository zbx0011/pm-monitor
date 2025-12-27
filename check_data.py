import json

d = json.load(open('prices_data.json', encoding='utf-8'))
print('prices_data 当前价差:', d['spread']['pt_spread_pct'])

d2 = json.load(open('platinum_spread_analysis.json', encoding='utf-8'))
print('history 最后一条:')
print(d2['history'][-1])
print()
print('current:')
print(d2['current'])
