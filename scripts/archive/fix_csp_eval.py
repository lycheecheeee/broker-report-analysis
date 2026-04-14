import re

files = ['web/login.html', 'web/broker_dashboard_v2.html', 'web/dashboard.html', 'web/auto_diagnosis.html']

for filepath in files:
    f = open(filepath, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    
    # Update CSP to include unsafe-eval
    if "script-src 'self' 'unsafe-inline'" in content and "'unsafe-eval'" not in content:
        content = content.replace(
            "script-src 'self' 'unsafe-inline'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
        )
        f = open(filepath, 'w', encoding='utf-8')
        f.write(content)
        f.close()
        print(f'Updated CSP in {filepath}')
    else:
        print(f'CSP already correct or not found in {filepath}')
