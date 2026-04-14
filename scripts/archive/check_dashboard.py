# Check if dashboard.html exists and has content
import os

dashboard_path = 'web/broker_dashboard_v2.html'
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'Dashboard file size: {len(content)} bytes')
    print(f'Contains HTML tags: {"<html" in content.lower()}')
    print(f'Contains body: {"<body" in content.lower()}')
else:
    print('Dashboard file NOT found!')
    
# Also check what route /dashboard returns
import requests
response = requests.get('http://127.0.0.1:62190/broker_3quilm/dashboard', timeout=5)
print(f'\nDashboard response status: {response.status_code}')
print(f'Dashboard response size: {len(response.text)} bytes')
print(f'First 200 chars: {response.text[:200]}')
