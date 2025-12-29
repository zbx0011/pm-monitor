import json

try:
    with open('platinum_all_pairs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    pairs = data.get('pairs', {})
    found = False
    for key, pair in pairs.items():
        if pair.get('cme_contract') == 'PLJ2026':
            print(f"Pair: {key}")
            print(f"CME Contract: {pair.get('cme_contract')}")
            print(f"Current CME USD: {pair['current'].get('cme_usd')}")
            print(f"Data Update Time: {data.get('update_time')}")
            found = True
            break
            
    if not found:
        print("PLJ2026 not found in pairs.")
        
except Exception as e:
    print(f"Error: {e}")
