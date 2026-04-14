files = ['web/login.html', 'web/broker_dashboard_v2.html', 'web/dashboard.html', 'web/auto_diagnosis.html']

csp_meta = '''    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self';">'''

for filepath in files:
    f = open(filepath, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    
    if '<meta http-equiv="Content-Security-Policy"' not in content:
        # Add after <head> tag
        content = content.replace('<head>', '<head>\n' + csp_meta)
        f = open(filepath, 'w', encoding='utf-8')
        f.write(content)
        f.close()
        print(f'Added CSP to {filepath}')
    else:
        print(f'CSP already exists in {filepath}')
