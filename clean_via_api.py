#!/usr/bin/env python3
"""Clean Duplicate Records via Production API"""
import requests

BASE_URL = "https://broker-report-analysis.vercel.app"

print("="*80)
print("🧹 CLEAN DUPLICATE RECORDS VIA PRODUCTION API")
print("="*80)

# Step 1: Get all records from production
print("\n[Step 1] Fetching all records from production...")
try:
    response = requests.get(
        f"{BASE_URL}/broker_3quilm/api/results",
        timeout=15
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch records: HTTP {response.status_code}")
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
        # Keep the latest record (first one since API returns sorted by created_at.desc)
        records_to_keep = records[0]
        records_to_remove = records[1:]
        
        print(f"\n📄 {pdf_filename}:")
        print(f"   Total records: {len(records)}")
        print(f"   ✅ Keep (latest): ID={records_to_keep.get('id', 'N/A')}, Created={records_to_keep.get('created_at', 'N/A')}")
        
        for rec in records_to_remove:
            print(f"   ❌ Delete: ID={rec.get('id', 'N/A')}, Created={rec.get('created_at', 'N/A')}")
            records_to_delete.append(rec.get('id'))

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

# Step 4: Delete duplicates via direct Supabase API
print(f"\n[Step 3] Deleting {len(records_to_delete)} duplicate records...")
print("⚠️  Note: Direct deletion requires Supabase credentials.")
print("   Please run clean_duplicates.py with proper environment variables instead.")
print("\nAlternatively, you can manually delete duplicates in Supabase Dashboard:")
print("   1. Go to Supabase Dashboard → Table Editor")
print("   2. Select analysis_results table")
print("   3. Filter and delete duplicate records")

print("\n" + "="*80)
print("CLEANUP INSTRUCTIONS")
print("="*80)
print("\nSince we don't have direct Supabase access in this script,")
print("please use one of these methods:")
print("\nMethod 1: Use clean_duplicates.py with .env file")
print("   - Create a .env file with SUPABASE_URL and SUPABASE_KEY")
print("   - Run: python clean_duplicates.py")
print("\nMethod 2: Manual deletion in Supabase Dashboard")
print("   - Visit your Supabase project dashboard")
print("   - Go to Table Editor → analysis_results")
print("   - Sort by created_at (descending)")
print("   - For each PDF with multiple records, keep only the latest")
print("="*80 + "\n")
