dashboard_html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Broker Report Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 24px; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .logout-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid white;
            color: white;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .logout-btn:hover { background: rgba(255,255,255,0.3); }
        .container {
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
        }
        .upload-section {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        .upload-section h2 {
            color: #333;
            margin-bottom: 20px;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 60px 20px;
            cursor: pointer;
            transition: all 0.3s;
            background: #f8f9ff;
        }
        .upload-area:hover {
            background: #eef0ff;
            border-color: #764ba2;
        }
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .upload-text {
            color: #666;
            font-size: 16px;
        }
        #fileInput { display: none; }
        .results-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .results-section h2 {
            color: #333;
            margin-bottom: 20px;
        }
        .result-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        .result-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .broker-name {
            font-size: 20px;
            font-weight: 600;
            color: #333;
        }
        .rating {
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        .rating.buy { background: #d4edda; color: #155724; }
        .rating.hold { background: #fff3cd; color: #856404; }
        .rating.sell { background: #f8d7da; color: #721c24; }
        .result-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .detail-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .detail-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        .detail-value {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        .ai-summary {
            margin-top: 15px;
            padding: 15px;
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            border-radius: 5px;
        }
        .ai-summary h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .ai-summary p {
            color: #555;
            line-height: 1.6;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Broker Report Analysis</h1>
        <div class="user-info">
            <span id="username">vangieyau</span>
            <button class="logout-btn" onclick="logout()">登出</button>
        </div>
    </div>
    
    <div class="container">
        <div class="upload-section">
            <h2>上傳 Broker Report PDF</h2>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">📄</div>
                <div class="upload-text">點擊此處或拖曳 PDF 文件到此</div>
            </div>
            <input type="file" id="fileInput" accept=".pdf" onchange="handleFileUpload(event)">
        </div>
        
        <div class="results-section">
            <h2>分析結果</h2>
            <div id="resultsContainer">
                <div class="empty-state">
                    <div class="empty-state-icon">📈</div>
                    <p>尚無分析結果，請上傳 PDF 文件開始分析</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const token = localStorage.getItem('token');
        
        if (!token) {
            window.location.href = '/broker_3quilm/';
        }
        
        function logout() {
            localStorage.removeItem('token');
            window.location.href = '/broker_3quilm/';
        }
        
        async function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            const resultsContainer = document.getElementById('resultsContainer');
            resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在分析中...</p></div>';
            
            try {
                const response = await fetch('/broker_3quilm/api/upload-pdf', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + token
                    },
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    loadResults();
                } else {
                    resultsContainer.innerHTML = '<div class="empty-state"><p>上傳失敗: ' + (data.error || '未知錯誤') + '</p></div>';
                }
            } catch (error) {
                resultsContainer.innerHTML = '<div class="empty-state"><p>網絡錯誤: ' + error.message + '</p></div>';
            }
        }
        
        async function loadResults() {
            try {
                const response = await fetch('/broker_3quilm/api/results', {
                    headers: {
                        'Authorization': 'Bearer ' + token
                    }
                });
                
                const data = await response.json();
                
                if (response.ok && data.results && data.results.length > 0) {
                    displayResults(data.results);
                } else {
                    document.getElementById('resultsContainer').innerHTML = 
                        '<div class="empty-state"><div class="empty-state-icon">📈</div><p>尚無分析結果，請上傳 PDF 文件開始分析</p></div>';
                }
            } catch (error) {
                console.error('Error loading results:', error);
            }
        }
        
        function displayResults(results) {
            const container = document.getElementById('resultsContainer');
            container.innerHTML = '';
            
            results.forEach(result => {
                const card = document.createElement('div');
                card.className = 'result-card';
                
                const ratingClass = result.rating ? result.rating.toLowerCase() : '';
                
                card.innerHTML = `
                    <div class="result-header">
                        <div class="broker-name">${result.broker_name || 'Unknown Broker'}</div>
                        ${result.rating ? `<div class="rating ${ratingClass}">${result.rating}</div>` : ''}
                    </div>
                    <div class="result-details">
                        ${result.target_price ? `
                            <div class="detail-item">
                                <div class="detail-label">目標價格</div>
                                <div class="detail-value">$${result.target_price.toFixed(2)}</div>
                            </div>
                        ` : ''}
                        ${result.current_price ? `
                            <div class="detail-item">
                                <div class="detail-label">當前價格</div>
                                <div class="detail-value">$${result.current_price.toFixed(2)}</div>
                            </div>
                        ` : ''}
                        ${result.upside_potential ? `
                            <div class="detail-item">
                                <div class="detail-label">上漲潛力</div>
                                <div class="detail-value" style="color: ${result.upside_potential > 0 ? '#28a745' : '#dc3545'}">
                                    ${result.upside_potential > 0 ? '+' : ''}${result.upside_potential.toFixed(2)}%
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    ${result.ai_summary ? `
                        <div class="ai-summary">
                            <h4>🤖 AI 摘要</h4>
                            <p>${result.ai_summary}</p>
                        </div>
                    ` : ''}
                `;
                
                container.appendChild(card);
            });
        }
        
        // Load results on page load
        loadResults();
    </script>
</body>
</html>'''

with open('web/broker_dashboard_v2.html', 'w', encoding='utf-8') as f:
    f.write(dashboard_html)

print('✓ Created complete dashboard page')
