f = open('backend.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()

# Remove the broken CSP lines
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if '@app.after_request' in line:
        skip_next = True
        continue
    if skip_next and 'return response' in line:
        skip_next = False
        continue
    new_lines.append(line)

f = open('backend.py', 'w', encoding='utf-8')
f.writelines(new_lines)
f.close()
print('Fixed backend.py!')
