f = open("backend.py", "r", encoding="utf-8")
lines = f.readlines()
f.close()

# Find and remove the duplicate routes we added
new_lines = []
skip_next = 0
for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue
    if "@app.route('/')" in line or (i > 0 and "def home():" in line) or (i > 0 and "def index():" in line):
        # Skip this route and the next few lines (the function definition)
        skip_next = 2  # Skip def line and return line
        continue
    new_lines.append(line)

f = open("backend.py", "w", encoding="utf-8")
f.writelines(new_lines)
f.close()

print("Removed duplicate routes!")
