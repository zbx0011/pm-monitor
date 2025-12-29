import requests
try:
    r = requests.get('http://localhost:8080/api/alert-config', timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
