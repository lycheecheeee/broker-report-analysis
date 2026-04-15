#!/usr/bin/env python3
"""Dry Run Test for Broker Report Analysis Deployment"""
import requests
import json
import time

BASE_URL = "https://broker-report-analysis.vercel.app"

def test_endpoint(name, endpoint, method='GET', timeout=10):
    """Test a single API endpoint"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"URL: {url}")
        
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, timeout=timeout)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ PASSED")
            
            # Try to parse JSON
            try:
                data = response.json()
                print(f"Response Type: JSON")
                
                # Special handling for different endpoints
                if 'health' in endpoint:
                    print(f"Message: {data.get('message', 'N/A')}")
                    
                elif 'list-pdfs' in endpoint:
                    files = data.get('files', [])
                    print(f"Files Found: {len(files)}")
                    if files:
                        print(f"First File: {files[0]}")
                        
                elif 'results' in endpoint:
                    count = len(data) if isinstance(data, list) else 0
                    print(f"Records Count: {count}")
                    
                elif 'export-analysis' in endpoint:
                    content_type = response.headers.get('Content-Type', 'N/A')
                    content_length = response.headers.get('Content-Length', 'N/A')
                    print(f"Content-Type: {content_type}")
                    print(f"Content-Length: {content_length} bytes")
            except:
                print(f"Response Type: Non-JSON ({response.headers.get('Content-Type', 'Unknown')})")
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"❌ FAILED - Timeout after {timeout}s")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ FAILED - Connection Error: {str(e)[:100]}")
    except Exception as e:
        print(f"❌ FAILED - {type(e).__name__}: {str(e)[:100]}")

def main():
    print("\n" + "="*60)
    print("DRY RUN TEST: Broker Report Analysis Deployment")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test A: Health Check
    test_endpoint(
        "A: Health Check",
        "/broker_3quilm/api/health"
    )
    
    # Test B: List PDFs
    test_endpoint(
        "B: List PDFs (Folder Scan)",
        "/broker_3quilm/api/list-pdfs?path=reports"
    )
    
    # Test C: Get Results (Supabase Data)
    test_endpoint(
        "C: Get Results (Supabase Integration)",
        "/broker_3quilm/api/results"
    )
    
    # Test D: Export Excel
    test_endpoint(
        "D: Export Analysis (Excel Generation)",
        "/broker_3quilm/api/export-analysis",
        timeout=15
    )
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("Check the results above for each test.")
    print("If all tests show ✅ PASSED, deployment is working correctly.")
    print("If any test shows ❌ FAILED, investigate the specific error.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
