import requests

# Test dashboard access
url = "http://127.0.0.1:62190/broker_3quilm/dashboard"
try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        print(f"✓ Dashboard page accessible: {len(response.text)} bytes")
    else:
        print(f"✗ Dashboard error: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {str(e)}")
