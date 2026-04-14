f = open('web/login.html', 'r', encoding='utf-8')
content = f.read()
f.close()

if '<link rel="icon"' not in content:
    content = content.replace('</head>', '    <link rel="icon" type="image/x-icon" href="/broker_3quilm/web/favicon.ico">\n</head>')
    f = open('web/login.html', 'w', encoding='utf-8')
    f.write(content)
    f.close()
    print('Favicon link added to login.html')
else:
    print('Favicon already exists')
