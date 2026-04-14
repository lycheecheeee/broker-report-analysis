# Add chart section to dashboard
with open('web/broker_dashboard_v2.html', 'r', encoding='utf-8') as f:
    content = f.read()

chart_section = '''
        <!-- Charts Section -->
        <div class="results-section" style="margin-top: 30px;">
            <h2>📊 智能分析圖表</h2>
            <div id="chartsContainer">
                <div class="empty-state">
                    <p>上傳PDF文件後將自動生成分析圖表</p>
                </div>
            </div>
        </div>
'''

# Insert charts section before closing container
content = content.replace('</div>\n    \n    <script>', chart_section + '\n    </div>\n    \n    <script>')

# Add chart rendering function
chart_js = '''
        async function loadCharts() {
            try {
                const response = await fetch('/broker_3quilm/api/charts', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                
                const data = await response.json();
                
                if (response.ok && data.brokers && data.brokers.length > 0) {
                    renderCharts(data);
                }
            } catch (error) {
                console.error('Error loading charts:', error);
            }
        }
        
        function renderCharts(data) {
            const container = document.getElementById('chartsContainer');
            
            // Rating Distribution Chart
            const distHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h4 style="margin-bottom: 15px; color: #333;">評級分佈</h4>
                        <div style="display: flex; justify-content: space-around; align-items: center; height: 150px;">
                            <div style="text-align: center;">
                                <div style="font-size: 36px; font-weight: bold; color: #28a745;">${data.distribution.Buy || 0}</div>
                                <div style="color: #666; margin-top: 5px;">Buy</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 36px; font-weight: bold; color: #ffc107;">${data.distribution.Hold || 0}</div>
                                <div style="color: #666; margin-top: 5px;">Hold</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 36px; font-weight: bold; color: #dc3545;">${data.distribution.Sell || 0}</div>
                                <div style="color: #666; margin-top: 5px;">Sell</div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h4 style="margin-bottom: 15px; color: #333;">平均上漲潛力</h4>
                        <div style="display: flex; align-items: center; justify-content: center; height: 150px;">
                            <div style="text-align: center;">
                                <div style="font-size: 48px; font-weight: bold; color: ${data.upsides.reduce((a,b)=>a+b,0)/data.upsides.length > 0 ? '#28a745' : '#dc3545'};">
                                    ${(data.upsides.reduce((a,b)=>a+b,0)/data.upsides.length).toFixed(1)}%
                                </div>
                                <div style="color: #666; margin-top: 10px;">平均預期回報</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h4 style="margin-bottom: 15px; color: #333;">各券商上漲潛力對比</h4>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        ${data.brokers.map((broker, i) => `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="min-width: 150px; font-weight: 500;">${broker}</div>
                                <div style="flex: 1; background: #e9ecef; border-radius: 10px; overflow: hidden; height: 30px; position: relative;">
                                    <div style="width: ${Math.min(Math.abs(data.upsides[i]) * 2, 100)}%; height: 100%; background: ${data.upsides[i] >= 0 ? 'linear-gradient(90deg, #28a745, #20c997)' : 'linear-gradient(90deg, #dc3545, #fd7e14)'}; transition: width 0.5s;"></div>
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: 600; color: #333;">
                                        ${data.upsides[i] > 0 ? '+' : ''}${data.upsides[i].toFixed(1)}%
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            container.innerHTML = distHTML;
        }
        
        // Load charts after results
        setTimeout(loadCharts, 1000);
'''

# Insert before closing script tag
content = content.replace('</script>\n</body>', chart_js + '\n    </script>\n</body>')

with open('web/broker_dashboard_v2.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Added smart charts to dashboard')
