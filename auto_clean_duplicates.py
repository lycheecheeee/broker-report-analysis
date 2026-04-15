#!/usr/bin/env python3
"""Auto Clean Duplicates - Direct Supabase API Access"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY")
    print("\nPlease create a .env file with:")
    print("SUPABASE_URL=https://your-project.supabase.co")
    print("SUPABASE_KEY=eyJ... (service_role key)")
    exit(1)

print("="*80)
print("🧹 AUTO CLEAN DUPLICATES - DIRECT SUPABASE ACCESS")
print("="*80)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

# Step 1: Fetch all records
print("\n[Step 1] Fetching all records...")
try:
    url = f"{SUPABASE_URL}/rest/v1/analysis_results?select=*&order=created_at.desc"
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        print(f"❌ Failed: HTTP {response.status_code}")
        print(f"Response: {response.text[:200]}")
        exit(1)
    
    all_records = response.json()
    total_records = len(all_records)
    print(f"✅ Total records: {total_records}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 2: Identify duplicates
print("\n[Step 2] Identifying duplicates...")
pdf_groups = {}
for record in all_records:
    pdf_filename = record.get('pdf_filename', '')
    if pdf_filename not in pdf_groups:
        pdf_groups[pdf_filename] = []
    pdf_groups[pdf_filename].append(record)

records_to_delete = []
unique_pdfs = len(pdf_groups)

for pdf_filename, records in pdf_groups.items():
    if len(records) > 1:
        # Keep latest (first), delete rest
        for rec in records[1:]:
            records_to_delete.append(rec['id'])

print(f"\n📊 Summary:")
print(f"   Unique PDFs: {unique_pdfs}")
print(f"   Total Records: {total_records}")
print(f"   To Delete: {len(records_to_delete)}")

if not records_to_delete:
    print("\n✅ No duplicates found!")
    exit(0)

# Step 3: Auto-delete (no confirmation needed for automation)
print(f"\n[Step 3] Deleting {len(records_to_delete)} duplicate records...")
deleted = 0
failed = 0

for i, record_id in enumerate(records_to_delete, 1):
    try:
        delete_url = f"{SUPABASE_URL}/rest/v1/analysis_results?id=eq.{record_id}"
        resp = requests.delete(delete_url, headers=headers, timeout=10)
        
        if resp.status_code in [200, 204]:
            deleted += 1
            if i % 10 == 0 or i == len(records_to_delete):
                print(f"   Progress: {i}/{len(records_to_delete)} ({deleted} deleted, {failed} failed)")
        else:
            failed += 1
            print(f"   ❌ Failed to delete ID {record_id}: HTTP {resp.status_code}")
            
    except Exception as e:
        failed += 1
        print(f"   ❌ Error deleting ID {record_id}: {str(e)[:50]}")

# Step 4: Verify
print(f"\n[Step 4] Verifying cleanup...")
try:
    verify_url = f"{SUPABASE_URL}/rest/v1/analysis_results?select=*"
    verify_resp = requests.get(verify_url, headers=headers, timeout=15)
    
    if verify_resp.status_code == 200:
        remaining = len(verify_resp.json())
        print(f"✅ Remaining records: {remaining}")
        print(f"✅ Unique PDFs: {unique_pdfs}")
        
        if remaining == unique_pdfs:
            print(f"\n🎉 SUCCESS! Database cleaned.")
            print(f"   Before: {total_records} records")
            print(f"   After: {remaining} records")
            print(f"   Deleted: {deleted} duplicates")
        else:
            print(f"\n⚠️  Warning: {remaining} != {unique_pdfs}")
    else:
        print(f"❌ Verification failed: HTTP {verify_resp.status_code}")
        
except Exception as e:
    print(f"❌ Verification error: {e}")

print("\n" + "="*80)
print("CLEANUP COMPLETE")
print("="*80 + "\n")

