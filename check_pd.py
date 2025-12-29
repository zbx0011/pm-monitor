import json

d = json.load(open('palladium_all_pairs.json', encoding='utf-8'))
print('更新时间:', d['update_time'])
print('\n各配对 current 数据:')
for k,v in d['pairs'].items():
    c = v.get('current', {})
    # current里没有datetime，用history最后一条
    last = v['history'][-1] if v['history'] else {}
    print(f"  {k}: 广期所={c.get('gfex_price')}, CME=${c.get('cme_usd')}, 时间={last.get('date')}")
