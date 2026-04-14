f = open("backend.py", "r", encoding="utf-8")
content = f.read()
f.close()

# Add routes before if __name__ using send_static_file
routes_code = """
@app.route('/')
def root():
    return app.send_static_file('web/login.html')

@app.route('/dashboard')
def dashboard_page():
    return app.send_static_file('web/broker_dashboard_v2.html')

"""

new_content = content.replace("if __name__ == '__main__':", routes_code + "if __name__ == '__main__':")

f = open("backend.py", "w", encoding="utf-8")
f.write(new_content)
f.close()

print("Routes added with send_static_file!")
