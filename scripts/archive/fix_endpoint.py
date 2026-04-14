f = open("backend.py", "r", encoding="utf-8")
content = f.read()
f.close()

# Fix the duplicate endpoint issue
content = content.replace("@app.route('/')\ndef index():", "@app.route('/')\ndef home():")

f = open("backend.py", "w", encoding="utf-8")
f.write(content)
f.close()

print("Fixed duplicate endpoint!")
