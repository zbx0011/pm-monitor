import json

with open('contract_convergence_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== 数据核验样本 ===\n')

for contract in data['contracts']:
    symbol = contract['symbol']
    print(f'【{symbol}】')
    
    history = contract['history']
    
    # 取5个样本点：开头、1/4、中间、3/4、结尾
    indices = [0, len(history)//4, len(history)//2, len(history)*3//4, -1]
    
    print(f'{"日期":<12} | {"国内收盘":>10} | {"CME折算CNY":>12} | {"溢价率":>8}')
    print('-' * 55)
    
    for i in indices:
        h = history[i]
        date = h['date']
        close = h['close']
        intl = h['intl_cny']
        spread = h['spread_pct']
        print(f'{date:<12} | {close:>10.2f} | {intl:>12.2f} | {spread:>+7.2f}%')
    
    print()
