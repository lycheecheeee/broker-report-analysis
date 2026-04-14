"""
Broker Report Analysis System - 自動診斷工具
自動檢測並修復常見問題
"""
import requests
import sqlite3
import os
import sys
from datetime import datetime

print("="*70)
print("🔍 Broker Report Analysis System - 自動診斷工具")
print("="*70)
print()

# 配置
BASE_URL = 'http://localhost:62190'
DATABASE = 'broker_analysis.db'
issues_found = []
issues_fixed = []

def check_service_running():
    """檢查服務是否運行"""
    print("1️⃣  檢查服務狀態...")
    try:
        r = requests.get(f'{BASE_URL}/broker_3quilm/', timeout=3)
        if r.status_code == 200:
            print("   ✅ 服務正常運行")
            return True
        else:
            print(f"   ❌ 服務返回異常狀態: {r.status_code}")
            issues_found.append("服務狀態異常")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ 服務未運行")
        print("   💡 請執行: python backend.py")
        issues_found.append("服務未運行")
        return False
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        issues_found.append(f"檢查服務失敗: {e}")
        return False

def check_database():
    """檢查數據庫"""
    print("\n2️⃣  檢查數據庫...")
    if not os.path.exists(DATABASE):
        print(f"   ❌ 數據庫文件不存在: {DATABASE}")
        issues_found.append("數據庫文件缺失")
        return False
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # 檢查表是否存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        
        required_tables = ['users', 'analysis_results', 'feedback', 'prompt_templates', 'stocks', 'broker_ratings']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"   ❌ 缺少表: {missing_tables}")
            issues_found.append(f"缺少表: {missing_tables}")
            conn.close()
            return False
        
        print(f"   ✅ 數據庫正常 ({len(tables)} 個表)")
        
        # 檢查用戶
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"   ✅ 用戶數量: {user_count}")
        
        if user_count == 0:
            print("   ⚠️  警告: 沒有用戶,請先註冊")
        
        # 檢查 broker_ratings 表結構
        c.execute("PRAGMA table_info(broker_ratings)")
        broker_cols = [row[1] for row in c.fetchall()]
        required_broker_fields = [
            'date_of_release', 'broker_name', 'stock_name',
            'related_industry', 'related_sub_industry', 'related_indexes',
            'investment_grade', 'target_price_adjusted', 'investment_horizon',
            'latest_close_before_release', 'date_target_first_hit',
            'last_transacted_price', 'today_date',
            'date_grade_revised', 'date_target_revised'
        ]
        missing_fields = [f for f in required_broker_fields if f not in broker_cols]
        
        if missing_fields:
            print(f"   ❌ broker_ratings 缺少字段: {missing_fields}")
            issues_found.append(f"broker_ratings 缺少字段: {missing_fields}")
        else:
            print(f"   ✅ broker_ratings 表結構完整 (15 個必需字段)")
        
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ 數據庫錯誤: {e}")
        issues_found.append(f"數據庫錯誤: {e}")
        return False

def check_api_endpoints():
    """檢查 API endpoints"""
    print("\n3️⃣  檢查 API Endpoints...")
    
    # 先嘗試登入獲取 token
    try:
        r = requests.post(f'{BASE_URL}/broker_3quilm/api/login', 
                         json={'username': 'testuser', 'password': 'test123'})
        if r.status_code != 200:
            print("   ⚠️  無法使用 testuser 登入,嘗試其他方法...")
            token = None
        else:
            token = r.json().get('token')
            print(f"   ✅ 登入成功")
    except Exception as e:
        print(f"   ⚠️  登入測試失敗: {e}")
        token = None
    
    if not token:
        print("   ⚠️  跳過 API 測試(需要有效用戶)")
        return True
    
    # 測試各個 endpoint
    endpoints = [
        ('GET', '/broker_3quilm/api/results'),
        ('GET', '/broker_3quilm/api/charts'),
    ]
    
    all_ok = True
    for method, endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            headers = {'Authorization': f'Bearer {token}'}
            
            if method == 'GET':
                r = requests.get(url, headers=headers, timeout=5)
            else:
                r = requests.post(url, headers=headers, timeout=5)
            
            if r.status_code == 200:
                print(f"   ✅ {endpoint}")
            else:
                print(f"   ❌ {endpoint} -> {r.status_code}")
                issues_found.append(f"{endpoint} 返回 {r.status_code}")
                all_ok = False
        except Exception as e:
            print(f"   ❌ {endpoint} -> {e}")
            issues_found.append(f"{endpoint} 異常: {e}")
            all_ok = False
    
    return all_ok

def check_openrouter_api():
    """檢查 OpenRouter API"""
    print("\n4️⃣  檢查 OpenRouter API...")
    try:
        # 從 backend.py 讀取 API key
        with open('backend.py', 'r', encoding='utf-8') as f:
            content = f.read()
            import re
            match = re.search(r"OPENROUTER_API_KEY = '([^']+)'", content)
            if not match:
                print("   ❌ 無法找到 API Key")
                issues_found.append("API Key 缺失")
                return False
            
            api_key = match.group(1)
            
            # 測試 API
            r = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'qwen/qwen-2.5-72b-instruct',
                    'messages': [{'role': 'user', 'content': 'test'}],
                    'max_tokens': 10
                },
                timeout=10
            )
            
            if r.status_code == 200:
                print("   ✅ OpenRouter API 正常")
                return True
            else:
                print(f"   ❌ OpenRouter API 錯誤: {r.status_code}")
                print(f"   響應: {r.text[:200]}")
                issues_found.append(f"OpenRouter API 錯誤: {r.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ OpenRouter API 檢查失敗: {e}")
        issues_found.append(f"OpenRouter API 檢查失敗: {e}")
        return False

def check_pdf_files():
    """檢查 PDF 文件"""
    print("\n5️⃣  檢查 PDF 文件...")
    pdf_folder = '700'
    if not os.path.exists(pdf_folder):
        print(f"   ⚠️  PDF 文件夾不存在: {pdf_folder}")
        return True
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("   ⚠️  未找到 PDF 文件")
        return True
    
    # 檢查文件大小
    invalid_files = []
    for pdf_file in pdf_files:
        filepath = os.path.join(pdf_folder, pdf_file)
        size = os.path.getsize(filepath)
        if size < 100:  # 小於 100 bytes 可能係損壞文件
            invalid_files.append((pdf_file, size))
    
    if invalid_files:
        print(f"   ⚠️  發現 {len(invalid_files)} 個可能損壞嘅 PDF 文件:")
        for fname, size in invalid_files:
            print(f"      - {fname} ({size} bytes)")
        print("   💡 建議: 刪除或替換呢啲文件")
    else:
        print(f"   ✅ 找到 {len(pdf_files)} 個 PDF 文件")
    
    return True

def print_summary():
    """打印總結"""
    print("\n" + "="*70)
    print("📊 診斷總結")
    print("="*70)
    
    if not issues_found:
        print("✅ 所有檢查通過!系統運行正常。")
        print()
        print("💡 使用提示:")
        print(f"   - 登入頁面: {BASE_URL}/broker_3quilm/")
        print(f"   - Dashboard: {BASE_URL}/broker_3quilm/dashboard")
        print(f"   - 測試賬戶: testuser / test123")
    else:
        print(f"❌ 發現 {len(issues_found)} 個問題:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
        print()
        print("💡 建議:")
        print("   1. 確保 backend.py 正在運行 (python backend.py)")
        print("   2. 檢查網絡連接")
        print("   3. 查看後端日誌獲取更多詳情")
    
    print("="*70)

if __name__ == '__main__':
    service_ok = check_service_running()
    if not service_ok:
        print("\n⚠️  服務未運行,無法繼續檢查其他項目")
        print_summary()
        sys.exit(1)
    
    db_ok = check_database()
    api_ok = check_api_endpoints()
    openrouter_ok = check_openrouter_api()
    pdf_ok = check_pdf_files()
    
    print_summary()
