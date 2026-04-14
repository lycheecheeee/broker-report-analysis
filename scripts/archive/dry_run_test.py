import requests
import time

url = "http://127.0.0.1:62190/broker_3quilm/"
print("Starting Dry Run Test (5 iterations)...")
print("=" * 60)

for i in range(1, 6):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✓ Test {i}/5: PASSED - Status: {response.status_code}, Time: {elapsed:.2f}s")
        else:
            print(f"✗ Test {i}/5: FAILED - Status: {response.status_code}")
    except Exception as e:
        print(f"✗ Test {i}/5: ERROR - {str(e)}")
    
    time.sleep(1)

print("=" * 60)
print("Dry Run Complete!")
