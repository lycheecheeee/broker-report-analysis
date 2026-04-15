#!/usr/bin/env python3
"""Diagnose Supabase Connection Issues"""
import requests
import os
from dotenv import load_dotenv

# Load local .env file for testing
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print("="*60)
print("SUPABASE CONNECTION DIAGNOSIS")
print("="*60)

print(f"\n1. Environment Variables:")
print(f"   SUPABASE_URL: {SUPABASE_URL or 'NOT SET'}")
print(f"   SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")
print(f"   Key Length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ FAILED: Missing environment variables")
    print("   Please set SUPABASE_URL and SUPABASE_KEY in Vercel Dashboard")
    exit(1)

print(f"\n2. Testing Supabase REST API...")

# Test 1: Check if table exists
print(f"\n   [Test A] Checking if analysis_results table exists...")
try:
    url = f"{SUPABASE_URL}/rest/v1/analysis_results?select=id&limit=1"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   ✅ Table exists and accessible")
        data = response.json()
        print(f"   Sample records: {len(data)}")
    elif response.status_code == 404:
        print(f"   ❌ Table does not exist (404)")
        print(f"   Response: {response.text[:200]}")
    elif response.status_code == 401:
        print(f"   ❌ Authentication failed (401)")
        print(f"   Response: {response.text[:200]}")
    elif response.status_code == 403:
        print(f"   ❌ Permission denied (403) - RLS policy blocking access")
        print(f"   Response: {response.text[:200]}")
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {str(e)[:100]}")

# Test 2: Try to insert a test record
print(f"\n   [Test B] Testing INSERT operation...")
try:
    url = f"{SUPABASE_URL}/rest/v1/analysis_results"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    test_data = {
        'user_id': 1,
        'pdf_filename': 'test_diagnosis.pdf',
        'broker_name': 'Test Broker',
        'rating': '買入',
        'target_price': 500.0,
        'current_price': 400.0,
        'upside_potential': 25.0,
        'ai_summary': 'Test record for diagnosis',
        'prompt_used': '',
        'created_at': '2026-04-15T12:00:00'
    }
    
    response = requests.post(url, headers=headers, json=test_data, timeout=10)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code in [200, 201]:
        print(f"   ✅ INSERT successful")
        result = response.json()
        print(f"   Inserted ID: {result[0]['id'] if result else 'N/A'}")
        
        # Clean up: delete the test record
        if result and len(result) > 0:
            test_id = result[0]['id']
            print(f"\n   [Test C] Cleaning up test record (ID: {test_id})...")
            delete_url = f"{SUPABASE_URL}/rest/v1/analysis_results?id=eq.{test_id}"
            delete_response = requests.delete(delete_url, headers=headers, timeout=10)
            print(f"   Delete Status: {delete_response.status_code}")
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Cleanup successful")
            else:
                print(f"   ⚠️  Cleanup failed: {delete_response.status_code}")
    elif response.status_code == 400:
        print(f"   ❌ Bad Request (400) - Schema mismatch or missing required fields")
        print(f"   Response: {response.text[:300]}")
    elif response.status_code == 401:
        print(f"   ❌ Authentication failed (401)")
        print(f"   Response: {response.text[:200]}")
    elif response.status_code == 403:
        print(f"   ❌ Permission denied (403) - RLS policy blocking INSERT")
        print(f"   Response: {response.text[:200]}")
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text[:300]}")
        
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "="*60)
print("DIAGNOSIS COMPLETE")
print("="*60)
print("\nNext Steps:")
print("1. If table doesn't exist: Create it in Supabase Dashboard")
print("2. If 401 error: Check SUPABASE_KEY is correct (service_role key)")
print("3. If 403 error: Disable RLS or add policy for anonymous access")
print("4. If 400 error: Check table schema matches the data structure")
print("="*60 + "\n")
