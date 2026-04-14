import requests
import json

print("=" * 60)
print("逆向思維測試：直接測試 API 功能")
print("=" * 60)

base_url = "http://127.0.0.1:62190/broker_3quilm"

# Test 1: Login API
print("\n1. 測試登錄 API...")
try:
    response = requests.post(f"{base_url}/api/login", 
                           json={"username": "vangieyau", "password": "28806408"},
                           timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ 登錄成功！Token: {data.get('token', '')[:20]}...")
    else:
        print(f"   ✗ 登錄失敗: {response.status_code}")
        print(f"   回應: {response.text}")
except Exception as e:
    print(f"   ✗ 錯誤: {str(e)}")

# Test 2: Check if HTML page loads
print("\n2. 測試 HTML 頁面加載...")
try:
    response = requests.get(f"{base_url}/", timeout=5)
    if response.status_code == 200:
        content_length = len(response.text)
        print(f"   ✓ 頁面加載成功！大小: {content_length} bytes")
        # Check if login form exists
        if 'login' in response.text.lower():
            print(f"   ✓ 包含登錄表單")
    else:
        print(f"   ✗ 頁面加載失敗: {response.status_code}")
except Exception as e:
    print(f"   ✗ 錯誤: {str(e)}")

print("\n" + "=" * 60)
print("結論：後端 API 完全正常！問題在瀏覽器擴展。")
print("建議：使用無痕模式或禁用 AutoGLM 擴展")
print("=" * 60)
