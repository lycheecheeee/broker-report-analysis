f = open('backend.py', 'r', encoding='utf-8')
content = f.read()
f.close()

if 'CSP' not in content:
    csp_code = """
@app.after_request
def add_csp_header(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self';"
    return response
"""
    content = content.replace('CORS(app)', 'CORS(app)' + csp_code)
    f = open('backend.py', 'w', encoding='utf-8')
    f.write(content)
    f.close()
    print('CSP header added successfully!')
else:
    print('CSP already exists')
