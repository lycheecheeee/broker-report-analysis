f = open("backend.py", "r", encoding="utf-8")
content = f.read()
f.close()

# Update port to random high port and add prefix to routes
content = content.replace("app.run(debug=True, port=5000)", "app.run(debug=True, port=62190)")

# Add prefix to all routes
content = content.replace("@app.route('/')", "@app.route('/broker_3quilm/')")
content = content.replace("@app.route('/dashboard')", "@app.route('/broker_3quilm/dashboard')")
content = content.replace("@app.route('/api/", "@app.route('/broker_3quilm/api/")

f = open("backend.py", "w", encoding="utf-8")
f.write(content)
f.close()

print("Updated with random port 62190 and prefix broker_3quilm!")
