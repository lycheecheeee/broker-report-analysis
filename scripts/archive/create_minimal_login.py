# Create a minimal login page that works without any extensions
html_content = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Broker Report Analysis - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 24px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .message {
            margin-top: 15px;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            display: none;
        }
        .success {
            background: #d4edda;
            color: #155724;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>📊 Broker Report Analysis</h1>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">用戶名</label>
                <input type="text" id="username" name="username" required value="vangieyau">
            </div>
            <div class="form-group">
                <label for="password">密碼</label>
                <input type="password" id="password" name="password" required value="28806408">
            </div>
            <button type="submit">登錄</button>
        </form>
        <div id="message" class="message"></div>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');
            
            try {
                const response = await fetch('/broker_3quilm/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    messageDiv.className = 'message success';
                    messageDiv.textContent = '✓ 登錄成功！正在跳轉...';
                    messageDiv.style.display = 'block';
                    localStorage.setItem('token', data.token);
                    setTimeout(() => {
                        window.location.href = '/broker_3quilm/dashboard';
                    }, 1000);
                } else {
                    messageDiv.className = 'message error';
                    messageDiv.textContent = '✗ ' + (data.error || '登錄失敗');
                    messageDiv.style.display = 'block';
                }
            } catch (error) {
                messageDiv.className = 'message error';
                messageDiv.textContent = '✗ 網絡錯誤: ' + error.message;
                messageDiv.style.display = 'block';
            }
        });
    </script>
</body>
</html>'''

with open('web/login.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('✓ Created minimal login page (no external dependencies)')
