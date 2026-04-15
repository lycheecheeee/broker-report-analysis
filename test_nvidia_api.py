import os
import requests
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY', '')

print("=" * 70)
print("測試 NVIDIA NIM API 連接")
print("=" * 70)
print()

if not NVIDIA_API_KEY:
    print("❌ NVIDIA_API_KEY 未設置")
    exit(1)

print(f"✅ API Key 已設置 (長度: {len(NVIDIA_API_KEY)})")
print()

# 測試 API 調用
url = 'https://integrate.api.nvidia.com/v1/chat/completions'
headers = {
    'Authorization': f'Bearer {NVIDIA_API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

payload = {
    'model': 'meta/llama-3.1-405b-instruct',
    'messages': [
        {'role': 'user', 'content': '請用一句話回答：你好嗎？'}
    ],
    'max_tokens': 100,
    'temperature': 0.3,
    'top_p': 0.7,
    'stream': False
}

print("正在調用 NVIDIA NIM API...")
print(f"模型: meta/llama-3.1-405b-instruct")
print()

try:
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    print(f"狀態碼: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print("✅ NVIDIA API 調用成功！")
        print(f"回應內容: {content}")
        print()
        print("=" * 70)
        print("🎉 NVIDIA NIM API 配置正確，可以開始使用！")
        print("=" * 70)
    else:
        print(f"❌ NVIDIA API 調用失敗")
        print(f"錯誤訊息: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ 請求異常: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
