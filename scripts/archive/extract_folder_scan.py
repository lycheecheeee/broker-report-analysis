# Read the test_system.html to see how folder scan works
with open('web/test_system.html', 'r', encoding='utf-8') as f:
    test_content = f.read()
    
# Extract the folder scan function
import re
match = re.search(r'async function testScanFolder\(\) \{[^}]+\}', test_content, re.DOTALL)
if match:
    print("Found folder scan function:")
    print(match.group(0)[:500])
else:
    print("Function not found")
