#!/usr/bin/env python3
"""Clean Duplicate Records in Supabase - Keep Only Latest Record Per PDF"""
import requests
import os
from dotenv import load_dotenv

# Load local .env file for testing
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    exit(1)

print("="*80)
print("🧹 SUPABASE DUPLICATE RECORDS CLEANUP")
print("="*80)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

# Step 1: Get all records
print("\n[Step 1] Fetching all records from Supabase...")
try:
    url = f"{SUPABASE_URL}/rest/v1/analysis_results?select=*&order=created_at.desc"
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch records: HTTP {response.status_code}")
        print(f"Response: {response.text[:200]}")
        exit(1)
    
    all_records = response.json()
    total_records = len(all_records)
    print(f"✅ Total records found: {total_records}")
    
except Exception as e:
    print(f"❌ Error fetching records: {e}")
    exit(1)

# Step 2: Identify duplicates
print("\n[Step 2] Identifying duplicate records...")
pdf_groups = {}
for record in all_records:
    pdf_filename = record.get('pdf_filename', '')
    if pdf_filename not in pdf_groups:
        pdf_groups[pdf_filename] = []
    pdf_groups[pdf_filename].append(record)

duplicates_found = 0
records_to_delete = []
unique_pdfs = len(pdf_groups)

for pdf_filename, records in pdf_groups.items():
    if len(records) > 1:
        duplicates_found += len(records) - 1
        # Keep the latest record (first one since sorted by created_at.desc)
        records_to_keep = records[0]
        records_to_remove = records[1:]
        
        print(f"\n📄 {pdf_filename}:")
        print(f"   Total records: {len(records)}")
        print(f"   ✅ Keep (latest): ID={records_to_keep['id']}, Created={records_to_keep['created_at']}")
        
        for rec in records_to_remove:
            print(f"   ❌ Delete: ID={rec['id']}, Created={rec['created_at']}")
            records_to_delete.append(rec['id'])

print(f"\n{'='*80}")
print(f"📊 SUMMARY:")
print(f"   Unique PDFs: {unique_pdfs}")
print(f"   Total Records: {total_records}")
print(f"   Duplicates Found: {duplicates_found}")
print(f"   Records to Delete: {len(records_to_delete)}")
print(f"{'='*80}")

if not records_to_delete:
    print("\n✅ No duplicates found. Database is clean!")
    exit(0)

# Step 3: Confirm deletion
print(f"\n⚠️  WARNING: This will permanently delete {len(records_to_delete)} records!")
confirm = input("Continue? (yes/no): ").strip().lower()

if confirm != 'yes':
    print("\n❌ Operation cancelled by user.")
    exit(0)

# Step 4: Delete duplicates
print(f"\n[Step 3] Deleting {len(records_to_delete)} duplicate records...")
deleted_count = 0
failed_count = 0

for record_id in records_to_delete:
    try:
        delete_url = f"{SUPABASE_URL}/rest/v1/analysis_results?id=eq.{record_id}"
        delete_response = requests.delete(delete_url, headers=headers, timeout=10)
        
        if delete_response.status_code in [200, 204]:
            deleted_count += 1
            print(f"   ✅ Deleted record ID: {record_id}")
        else:
            failed_count += 1
            print(f"   ❌ Failed to delete record ID: {record_id} (HTTP {delete_response.status_code})")
            
    except Exception as e:
        failed_count += 1
        print(f"   ❌ Error deleting record ID: {record_id} - {str(e)[:50]}")

print(f"\n{'='*80}")
print(f"🎯 DELETION RESULTS:")
print(f"   Successfully Deleted: {deleted_count}")
print(f"   Failed: {failed_count}")
print(f"{'='*80}")

# Step 5: Verify cleanup
print("\n[Step 4] Verifying cleanup...")
try:
    verify_url = f"{SUPABASE_URL}/rest/v1/analysis_results?select=*&order=created_at.desc"
    verify_response = requests.get(verify_url, headers=headers, timeout=15)
    
    if verify_response.status_code == 200:
        remaining_records = verify_response.json()
        remaining_count = len(remaining_records)
        
        print(f"✅ Remaining records: {remaining_count}")
        print(f"✅ Unique PDFs: {unique_pdfs}")
        
        if remaining_count == unique_pdfs:
            print("\n🎉 SUCCESS! All duplicates removed. Each PDF now has exactly 1 record.")
        else:
            print(f"\n⚠️  Warning: Remaining records ({remaining_count}) != Unique PDFs ({unique_pdfs})")
            print("   There may still be some issues to investigate.")
    else:
        print(f"❌ Failed to verify: HTTP {verify_response.status_code}")
        
except Exception as e:
    print(f"❌ Error during verification: {e}")

print("\n" + "="*80)
print("CLEANUP COMPLETE")
print("="*80 + "\n")

