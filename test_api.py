import requests
import json

try:
    resp = requests.get("http://localhost:8080/api/pair-history?metal=platinum&pair=2610-2610", timeout=10)
    data = resp.json()
    history = data.get('history', [])
    print(f"Total records: {len(history)}")
    if history:
        print(f"First record date: {history[0]['date']}")
        print(f"Last record date: {history[-1]['date']}")
except Exception as e:
    print(f"Error: {e}")
