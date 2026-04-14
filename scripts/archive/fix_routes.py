import re

f = open("backend.py", "r", encoding="utf-8")
content = f.read()
f.close()

routes_code = """
@app.route('/')
def index():
    return send_from_directory('.', 'web/login.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'web/broker_dashboard_v2.html')

"""

new_content = content.replace("if __name__ == '__main__':", routes_code + "if __name__ == '__main__':")

f = open("backend.py", "w", encoding="utf-8")
f.write(new_content)
f.close()

print("Routes added successfully!")
