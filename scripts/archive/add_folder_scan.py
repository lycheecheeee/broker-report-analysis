# Read current dashboard
with open('web/broker_dashboard_v2.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add folder scan feature before </body>
folder_scan_html = '''
    <!-- Folder Scan Modal -->
    <div id="folderModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000;">
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); background:white; padding:30px; border-radius:10px; max-width:600px; width:90%;">
            <h3 style="margin-bottom:20px; color:#333;">📁 批量掃描文件夾</h3>
            <div style="margin-bottom:15px;">
                <label style="display:block; margin-bottom:5px; color:#666;">文件夾路徑：</label>
                <input type="text" id="folderPath" placeholder="例如: C:\\Users\\user\\Desktop\\BrokerReports" 
                       style="width:100%; padding:10px; border:1px solid #ddd; border-radius:5px; font-size:14px;">
            </div>
            <div style="display:flex; gap:10px; justify-content:flex-end;">
                <button onclick="closeFolderModal()" style="padding:10px 20px; border:1px solid #ddd; background:white; border-radius:5px; cursor:pointer;">取消</button>
                <button onclick="startFolderScan()" style="padding:10px 20px; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; border:none; border-radius:5px; cursor:pointer; font-weight:600;">開始掃描</button>
            </div>
            <div id="scanProgress" style="margin-top:20px; display:none;">
                <div class="spinner" style="border:3px solid #f3f3f3; border-top:3px solid #667eea; border-radius:50%; width:30px; height:30px; animation:spin 1s linear infinite; margin:0 auto 10px;"></div>
                <p style="text-align:center; color:#666;" id="scanStatus">掃描中...</p>
            </div>
        </div>
    </div>
    
    <script>
        function openFolderModal() {
            document.getElementById('folderModal').style.display = 'block';
        }
        
        function closeFolderModal() {
            document.getElementById('folderModal').style.display = 'none';
            document.getElementById('scanProgress').style.display = 'none';
        }
        
        async function startFolderScan() {
            const folderPath = document.getElementById('folderPath').value.trim();
            if (!folderPath) {
                alert('請輸入文件夾路徑');
                return;
            }
            
            document.getElementById('scanProgress').style.display = 'block';
            document.getElementById('scanStatus').textContent = '正在掃描文件夾...';
            
            try {
                const response = await fetch('/broker_3quilm/api/v1/scan/folder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ folder_path: folderPath })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('scanStatus').textContent = `✓ 掃描完成！找到 ${data.total_files} 個PDF文件`;
                    setTimeout(() => {
                        closeFolderModal();
                        loadResults();
                    }, 2000);
                } else {
                    document.getElementById('scanStatus').textContent = '✗ 錯誤: ' + (data.error || '未知錯誤');
                }
            } catch (error) {
                document.getElementById('scanStatus').textContent = '✗ 網絡錯誤: ' + error.message;
            }
        }
    </script>
'''

# Insert before </body>
content = content.replace('</body>', folder_scan_html + '\n</body>')

# Also add a button in the upload section
upload_section_addition = '''
            <div style="margin-top:20px;">
                <button onclick="openFolderModal()" style="padding:12px 24px; background:white; border:2px solid #667eea; color:#667eea; border-radius:5px; cursor:pointer; font-size:14px; font-weight:600; transition:all 0.3s;">
                    📁 批量掃描文件夾
                </button>
            </div>
'''

content = content.replace('<input type="file" id="fileInput"', upload_section_addition + '\n            <input type="file" id="fileInput"')

with open('web/broker_dashboard_v2.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Added folder scan feature to dashboard')
