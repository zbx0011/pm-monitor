import requests
try:
    print("Testing refresh-data endpoint...")
    resp = requests.post("http://localhost:8080/api/refresh-data", timeout=120)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
