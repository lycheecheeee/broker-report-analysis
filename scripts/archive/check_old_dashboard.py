with open('web/broker_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Check for path/folder features
has_path_feature = 'path' in content.lower() or 'folder' in content.lower() or '目錄' in content or '路徑' in content
print(f"Has path/folder feature: {has_path_feature}")

# Show key features
if 'upload' in content.lower():
    print("✓ Has upload functionality")
if 'pdf' in content.lower():
    print("✓ Handles PDF files")
if 'analyze' in content.lower() or '分析' in content:
    print("✓ Has analysis feature")
    
# Check file size
print(f"\nFile size: {len(content)} bytes")
print(f"First 500 chars:\n{content[:500]}")
