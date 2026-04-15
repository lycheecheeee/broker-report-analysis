#!/usr/bin/env python3
"""Test Folder Scan Functionality - Simulate scanning one PDF"""
import requests
import json
import time

BASE_URL = "https://broker-report-analysis.vercel.app"

def test_scan_single_pdf():
    """Test scanning a single PDF file"""
    print("\n" + "="*60)
    print("TEST: Folder Scan - Single PDF Analysis")
    print("="*60)
    
    # Step 1: List PDFs
    print("\n[Step 1] Listing PDF files...")
    try:
        response = requests.get(
            f"{BASE_URL}/broker_3quilm/api/list-pdfs?path=reports",
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED to list PDFs: HTTP {response.status_code}")
            return
        
        data = response.json()
        files = data.get('files', [])
        
        if not files:
            print("❌ No PDF files found in reports/ folder")
            return
        
        print(f"✅ Found {len(files)} PDF files")
        print(f"   First file: {files[0]}")
        
        # Use first file for testing
        test_file = files[0]
        
    except Exception as e:
        print(f"❌ Error listing PDFs: {e}")
        return
    
    # Step 2: Analyze the PDF
    print(f"\n[Step 2] Analyzing PDF: {test_file}...")
    try:
        form_data = {
            'filename': test_file,
            'folder_path': 'reports'
        }
        
        response = requests.post(
            f"{BASE_URL}/broker_3quilm/api/analyze-existing-pdf",
            data=form_data,
            timeout=30  # Longer timeout for PDF analysis
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED to analyze PDF: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return
        
        result = response.json()
        
        # Check if analysis was successful
        if result.get('skipped'):
            print(f"⚠️  Skipped (already analyzed): {test_file}")
            return
        
        print(f"✅ Analysis completed successfully!")
        print(f"   Broker: {result.get('broker_name', 'N/A')}")
        print(f"   Rating: {result.get('rating', 'N/A')}")
        print(f"   Target Price: HK${result.get('target_price', 'N/A')}")
        print(f"   Analysis ID: {result.get('analysis_id', 'N/A')}")
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout during PDF analysis (30s limit)")
        return
    except Exception as e:
        print(f"❌ Error analyzing PDF: {type(e).__name__}: {str(e)[:100]}")
        return
    
    # Step 3: Verify data was saved to Supabase
    print("\n[Step 3] Verifying data persistence in Supabase...")
    time.sleep(2)  # Wait for data to be indexed
    
    try:
        response = requests.get(
            f"{BASE_URL}/broker_3quilm/api/results",
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED to get results: HTTP {response.status_code}")
            return
        
        results = response.json()
        count = len(results) if isinstance(results, list) else 0
        
        print(f"✅ Total records in Supabase: {count}")
        
        if count > 0:
            latest = results[0]
            print(f"   Latest record:")
            print(f"     - File: {latest.get('pdf_filename', 'N/A')}")
            print(f"     - Broker: {latest.get('broker_name', 'N/A')}")
            print(f"     - Rating: {latest.get('rating', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return
    
    # Step 4: Test Excel export
    print("\n[Step 4] Testing Excel export...")
    try:
        response = requests.get(
            f"{BASE_URL}/broker_3quilm/api/export-analysis",
            timeout=15
        )
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'N/A')
            content_length = response.headers.get('Content-Length', 'N/A')
            print(f"✅ Excel export successful!")
            print(f"   Content-Type: {content_type}")
            print(f"   File Size: {content_length} bytes")
        elif response.status_code == 404:
            error_data = response.json()
            print(f"⚠️  Export returned 404: {error_data.get('error', 'Unknown error')}")
            print(f"   This is expected if no data exists in Supabase")
        else:
            print(f"❌ Export failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error exporting Excel: {e}")
        return
    
    print("\n" + "="*60)
    print("SCAN TEST COMPLETE")
    print("="*60)
    print("If all steps show ✅, folder scan functionality is working!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_scan_single_pdf()
