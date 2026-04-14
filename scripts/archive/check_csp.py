files = ['web/login.html', 'web/broker_dashboard_v2.html', 'web/dashboard.html', 'web/auto_diagnosis.html']

for filepath in files:
    f = open(filepath, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    
    # Check if CSP exists
    if '<meta http-equiv="Content-Security-Policy"' in content:
        print(f'{filepath}: CSP exists')
        # Show the CSP line
        for line in content.split('\n'):
            if 'Content-Security-Policy' in line:
                print(f'  {line.strip()}')
    else:
        print(f'{filepath}: NO CSP - need to add')
