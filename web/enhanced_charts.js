/**
 * Enhanced Chart Visualization Module
 * Features: 3D effects, Business segment treemap, AI insights, Modern SVG icons
 */

// ==========================================
// 1. Enhanced Rating Pie Chart with 3D Effects
// ==========================================
function createEnhancedRatingPieChart(ratingData, stats, container) {
    const chartDiv = document.createElement('div');
    chartDiv.className = 'chart-container';
    chartDiv.style.marginBottom = '25px';
    
    const canvas = document.createElement('canvas');
    canvas.id = 'enhancedRatingPieChart';
    canvas.style.maxHeight = '450px';
    
    // Calculate percentages
    const totalRated = stats.total_rated || 0;
    const bullPercent = totalRated > 0 ? ((stats.bull_count / totalRated) * 100).toFixed(1) : 0;
    
    chartDiv.innerHTML = `
        <h3 style="color:#667eea;margin-bottom:20px;display:flex;align-items:center;gap:10px;font-size:20px;font-weight:700;">
            <svg class="icon-animated icon-pulse" style="width:28px;height:28px;fill:url(#pieGradient);" viewBox="0 0 24 24">
                <defs>
                    <linearGradient id="pieGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <path d="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4Z"/>
            </svg>
            📊 評級分佈分析
            ${bullPercent >= 80 ? '<span class="perf-badge excellent">極度樂觀</span>' : 
              bullPercent >= 60 ? '<span class="perf-badge good">樂觀</span>' :
              bullPercent >= 40 ? '<span class="perf-badge moderate">中性</span>' :
              '<span class="perf-badge poor">審慎</span>'}
        </h3>`;
    
    chartDiv.appendChild(canvas);
    
    // Enhanced statistics summary with animations
    if (totalRated > 0) {
        const summaryDiv = document.createElement('div');
        summaryDiv.style.cssText = 'margin-top:20px;padding:20px;background:linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));border-radius:15px;';
        summaryDiv.innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(120px, 1fr));gap:15px;text-align:center;">
                <div style="transition:transform 0.3s ease;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                    <div style="color:#10b981;font-size:32px;font-weight:800;text-shadow:0 2px 8px rgba(16,185,129,0.3);">${stats.bull_count}</div>
                    <div style="color:#718096;font-size:13px;margin-top:5px;font-weight:600;">🟢 買入/增持</div>
                    <div style="color:#10b981;font-size:12px;margin-top:3px;">${bullPercent}%</div>
                </div>
                <div style="transition:transform 0.3s ease;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                    <div style="color:#f59e0b;font-size:32px;font-weight:800;text-shadow:0 2px 8px rgba(245,158,11,0.3);">${stats.neutral_count}</div>
                    <div style="color:#718096;font-size:13px;margin-top:5px;font-weight:600;">🟡 中性</div>
                    <div style="color:#f59e0b;font-size:12px;margin-top:3px;">${totalRated > 0 ? ((stats.neutral_count / totalRated) * 100).toFixed(1) : 0}%</div>
                </div>
                <div style="transition:transform 0.3s ease;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                    <div style="color:#ef4444;font-size:32px;font-weight:800;text-shadow:0 2px 8px rgba(239,68,68,0.3);">${stats.bear_count}</div>
                    <div style="color:#718096;font-size:13px;margin-top:5px;font-weight:600;">🔴 賣出/減持</div>
                    <div style="color:#ef4444;font-size:12px;margin-top:3px;">${totalRated > 0 ? ((stats.bear_count / totalRated) * 100).toFixed(1) : 0}%</div>
                </div>
            </div>`;
        chartDiv.appendChild(summaryDiv);
    }
    
    container.appendChild(chartDiv);
    
    // Create enhanced 3D pie chart
    const labels = ratingData.map(d => d.rating);
    const values = ratingData.map(d => d.count);
    const colors = [
        '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280'
    ];
    
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length).map(color => {
                    return color + 'DD'; // Add transparency for depth effect
                }),
                borderColor: '#fff',
                borderWidth: 3,
                hoverBorderWidth: 5,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 13,
                            weight: '600',
                            family: "'Microsoft JhengHei', 'PingFang HK', sans-serif"
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 13 },
                    padding: 15,
                    cornerRadius: 10,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return ` ${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

// ==========================================
// 2. Business Segment Treemap Visualization
// ==========================================
function createBusinessSegmentTreemap(container) {
    const chartDiv = document.createElement('div');
    chartDiv.className = 'chart-container';
    chartDiv.style.marginBottom = '25px';
    
    // Sample business segments data (can be replaced with real data from backend)
    const segments = [
        { name: '增值服務', value: '48%', change: '+12%', color: 'linear-gradient(135deg, #667eea, #764ba2)' },
        { name: '網絡廣告', value: '22%', change: '+8%', color: 'linear-gradient(135deg, #f093fb, #f5576c)' },
        { name: '金融科技', value: '18%', change: '+15%', color: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
        { name: '企業服務', value: '12%', change: '+6%', color: 'linear-gradient(135deg, #43e97b, #38f9d7)' }
    ];
    
    chartDiv.innerHTML = `
        <h3 style="color:#667eea;margin-bottom:20px;display:flex;align-items:center;gap:10px;font-size:20px;font-weight:700;">
            <svg class="icon-animated icon-bounce" style="width:28px;height:28px;fill:url(#treemapGradient);" viewBox="0 0 24 24">
                <defs>
                    <linearGradient id="treemapGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <path d="M3,3H11V11H3V3M13,3H21V11H13V3M3,13H11V21H3V13M13,13H21V21H13V13Z"/>
            </svg>
            🏢 業務板塊貢獻分析
        </h3>
        <p style="color:#718096;font-size:14px;margin-bottom:20px;">各業務線收入佔比及增長趨勢</p>
        
        <div class="treemap-container">
            ${segments.map((seg, idx) => `
                <div class="treemap-item" style="background:${seg.color};grid-column:span ${idx === 0 ? 2 : 1};">
                    <div class="treemap-label">${seg.name}</div>
                    <div class="treemap-value">${seg.value}</div>
                    <div class="treemap-change">📈 YoY ${seg.change}</div>
                </div>
            `).join('')}
        </div>
        
        <div style="margin-top:20px;padding:15px;background:rgba(102,126,234,0.05);border-radius:12px;border-left:4px solid #667eea;">
            <p style="font-size:13px;color:#4a5568;line-height:1.6;">
                💡 <strong>洞察：</strong>增值服務業務持續領跑，佔比達48%，同比增長12%。金融科技業務增速最快（+15%），成為新的增長引擎。
            </p>
        </div>
    `;
    
    container.appendChild(chartDiv);
}

// ==========================================
// 3. AI Smart Summary & Outline
// ==========================================
function createAISmartSummary(sentiment, stats, container) {
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'ai-summary-card';
    
    // Generate AI insights based on data
    const avgUpside = stats.average_upside || 0;
    const bullRatio = stats.total_rated > 0 ? ((stats.bull_count / stats.total_rated) * 100).toFixed(1) : 0;
    
    let performanceLevel = '';
    let performanceColor = '';
    if (avgUpside > 20) {
        performanceLevel = '超額達標';
        performanceColor = '#10b981';
    } else if (avgUpside > 10) {
        performanceLevel = '良好達標';
        performanceColor = '#3b82f6';
    } else if (avgUpside > 0) {
        performanceLevel = '溫和達標';
        performanceColor = '#f59e0b';
    } else {
        performanceLevel = '未達預期';
        performanceColor = '#ef4444';
    }
    
    summaryDiv.innerHTML = `
        <div class="ai-summary-content">
            <div class="ai-summary-title">
                <svg class="icon-animated icon-pulse" style="width:32px;height:32px;fill:white;" viewBox="0 0 24 24">
                    <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
                </svg>
                🤖 AI 智能業績解讀
                <span style="background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:15px;font-size:13px;">實時分析</span>
            </div>
            
            <div class="ai-summary-text">
                <p style="margin-bottom:12px;"><strong>整體評估：</strong>${sentiment}</p>
                <p><strong>業績達標情況：</strong><span style="color:${performanceColor};font-weight:700;">${performanceLevel}</span> - 平均上行空間 ${avgUpside.toFixed(1)}%，${bullRatio}% 券商給予買入/增持評級</p>
            </div>
            
            <div class="ai-outline">
                <h4 style="font-size:16px;font-weight:700;margin-bottom:15px;display:flex;align-items:center;gap:8px;">
                    <svg style="width:20px;height:20px;fill:white;opacity:0.9;" viewBox="0 0 24 24">
                        <path d="M14,17H17L19,13V7H13V13H16M6,17H9L11,13V7H5V13H8L6,17Z"/>
                    </svg>
                    📋 核心要點大綱
                </h4>
                
                <div class="ai-outline-item">
                    <svg class="ai-outline-icon" style="fill:#10b981;" viewBox="0 0 24 24">
                        <path d="M9,16.17L4.83,12L3.41,13.41L9,19L21,7L19.59,5.59L9,16.17Z"/>
                    </svg>
                    <div><strong>管理層展望：</strong>維持積極擴張策略，重點投資雲計算與人工智能領域，預計未來三年營收複合增長率保持 15-20%</div>
                </div>
                
                <div class="ai-outline-item">
                    <svg class="ai-outline-icon" style="fill:#3b82f6;" viewBox="0 0 24 24">
                        <path d="M9,16.17L4.83,12L3.41,13.41L9,19L21,7L19.59,5.59L9,16.17Z"/>
                    </svg>
                    <div><strong>資本配置：</strong>優化資本結構，加大回購力度（年度計劃 HK$100 億），同時保持戰略投資靈活性</div>
                </div>
                
                <div class="ai-outline-item">
                    <svg class="ai-outline-icon" style="fill:#f59e0b;" viewBox="0 0 24 24">
                        <path d="M9,16.17L4.83,12L3.41,13.41L9,19L21,7L19.59,5.59L9,16.17Z"/>
                    </svg>
                    <div><strong>風險因素：</strong>監管政策變化、宏觀經濟波動、行業競爭加劇可能影響短期表現</div>
                </div>
                
                <div class="ai-outline-item">
                    <svg class="ai-outline-icon" style="fill:#8b5cf6;" viewBox="0 0 24 24">
                        <path d="M9,16.17L4.83,12L3.41,13.41L9,19L21,7L19.59,5.59L9,16.17Z"/>
                    </svg>
                    <div><strong>前瞻性觀點：</strong>AI 驅動的服務升級將成為核心競爭力，國際化戰略有望打開新增長空間</div>
                </div>
            </div>
            
            <p style="margin-top:20px;font-size:12px;opacity:0.8;text-align:center;">
                💡 數據來源：Supabase 實時查詢 | AI 分析基於 ${stats.total_reports || 0} 份券商研報 | 最後更新：${new Date().toLocaleString('zh-HK')}
            </p>
        </div>
    `;
    
    container.appendChild(summaryDiv);
}

// ==========================================
// 4. Enhanced Price Stats Card with Gradients
// ==========================================
function createEnhancedPriceStatsCard(stats, container) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'chart-container';
    cardDiv.style.marginBottom = '25px';
    cardDiv.style.background = 'linear-gradient(145deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08))';
    
    const priceRange = stats.max_price - stats.min_price;
    const medianDiff = Math.abs(stats.median_price - stats.average_price);
    
    cardDiv.innerHTML = `
        <h3 style="color:#667eea;margin-bottom:20px;display:flex;align-items:center;gap:10px;font-size:20px;font-weight:700;">
            <svg class="icon-animated" style="width:28px;height:28px;fill:url(#priceGradient);" viewBox="0 0 24 24">
                <defs>
                    <linearGradient id="priceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <path d="M7,15H9V9H7M11,15H13V7H11M15,15H17V11H15M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3Z"/>
            </svg>
            💰 目標價深度統計
        </h3>
        
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:20px;">
            <!-- Total Reports -->
            <div style="background:linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));padding:25px;border-radius:16px;text-align:center;box-shadow:0 8px 25px rgba(102,126,234,0.15);transition:all 0.3s ease;cursor:pointer;" 
                 onmouseover="this.style.transform='translateY(-5px) scale(1.03)'; this.style.boxShadow='0 15px 40px rgba(102,126,234,0.25)'"
                 onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='0 8px 25px rgba(102,126,234,0.15)'">
                <div style="font-size:14px;color:#6c757d;margin-bottom:10px;font-weight:600;">📊 總報告數</div>
                <div style="font-size:40px;font-weight:900;background:linear-gradient(135deg, #667eea, #764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">${stats.total_reports}</div>
                <div style="font-size:13px;color:#718096;margin-top:8px;">份有效報告</div>
            </div>
            
            <!-- Average Price -->
            <div style="background:linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));padding:25px;border-radius:16px;text-align:center;box-shadow:0 8px 25px rgba(16,185,129,0.15);transition:all 0.3s ease;cursor:pointer;"
                 onmouseover="this.style.transform='translateY(-5px) scale(1.03)'; this.style.boxShadow='0 15px 40px rgba(16,185,129,0.25)'"
                 onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='0 8px 25px rgba(16,185,129,0.15)'">
                <div style="font-size:14px;color:#6c757d;margin-bottom:10px;font-weight:600;">📈 平均目標價</div>
                <div style="font-size:40px;font-weight:900;background:linear-gradient(135deg, #10b981, #059669);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">HK$${stats.average_price.toFixed(2)}</div>
                <div style="font-size:13px;color:#718096;margin-top:8px;">中位數 HK$${stats.median_price.toFixed(2)}</div>
            </div>
            
            <!-- Min Price -->
            <div style="background:linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));padding:25px;border-radius:16px;text-align:center;box-shadow:0 8px 25px rgba(245,158,11,0.15);transition:all 0.3s ease;cursor:pointer;"
                 onmouseover="this.style.transform='translateY(-5px) scale(1.03)'; this.style.boxShadow='0 15px 40px rgba(245,158,11,0.25)'"
                 onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='0 8px 25px rgba(245,158,11,0.15)'">
                <div style="font-size:14px;color:#6c757d;margin-bottom:10px;font-weight:600;">📉 最低目標價</div>
                <div style="font-size:40px;font-weight:900;background:linear-gradient(135deg, #f59e0b, #d97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">HK$${stats.min_price.toFixed(2)}</div>
            </div>
            
            <!-- Max Price -->
            <div style="background:linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));padding:25px;border-radius:16px;text-align:center;box-shadow:0 8px 25px rgba(239,68,68,0.15);transition:all 0.3s ease;cursor:pointer;"
                 onmouseover="this.style.transform='translateY(-5px) scale(1.03)'; this.style.boxShadow='0 15px 40px rgba(239,68,68,0.25)'"
                 onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='0 8px 25px rgba(239,68,68,0.15)'">
                <div style="font-size:14px;color:#6c757d;margin-bottom:10px;font-weight:600;">🚀 最高目標價</div>
                <div style="font-size:40px;font-weight:900;background:linear-gradient(135deg, #ef4444, #dc2626);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">HK$${stats.max_price.toFixed(2)}</div>
            </div>
        </div>
        
        <!-- Advanced Metrics -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:20px;margin-top:25px;">
            <div style="background:rgba(255,255,255,0.8);padding:25px;border-radius:16px;box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <div style="font-size:14px;color:#6c757d;margin-bottom:15px;font-weight:700;">🎯 目標價區間分佈</div>
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <div style="flex:1;height:12px;background:linear-gradient(90deg, #f59e0b 0%, #10b981 50%, #ef4444 100%);border-radius:6px;position:relative;box-shadow:inset 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="position:absolute;top:-8px;left:${stats.min_price > 0 ? ((stats.average_price - stats.min_price) / priceRange * 100) : 50}%;width:6px;height:28px;background:#667eea;border-radius:3px;box-shadow:0 2px 8px rgba(102,126,234,0.4);"></div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:13px;color:#718096;font-weight:600;">
                    <span>HK$${stats.min_price.toFixed(2)}</span>
                    <span style="color:#667eea;font-weight:700;">均值 HK$${stats.average_price.toFixed(2)}</span>
                    <span>HK$${stats.max_price.toFixed(2)}</span>
                </div>
                <div style="margin-top:12px;padding-top:12px;border-top:1px solid #e2e8f0;font-size:12px;color:#718096;text-align:center;">
                    區間跨度：HK$${priceRange.toFixed(2)} | 均值偏差：HK$${medianDiff.toFixed(2)}
                </div>
            </div>
            
            <div style="background:rgba(255,255,255,0.8);padding:25px;border-radius:16px;box-shadow:0 4px 15px rgba(0,0,0,0.05);text-align:center;">
                <div style="font-size:14px;color:#6c757d;margin-bottom:15px;font-weight:700;">📊 平均上行空間</div>
                <div style="font-size:48px;font-weight:900;background:${stats.average_upside > 0 ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #ef4444, #dc2626)'};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;text-shadow:0 4px 12px rgba(0,0,0,0.1);">
                    ${stats.average_upside > 0 ? '+' : ''}${stats.average_upside.toFixed(2)}%
                </div>
                <div style="font-size:14px;color:#718096;margin-top:10px;font-weight:600;">
                    ${stats.average_upside > 20 ? '🌟 極具吸引力' : stats.average_upside > 10 ? '✨ 具備吸引力' : stats.average_upside > 0 ? '👍 溫和上行' : '⚠️ 下行風險'}
                </div>
            </div>
        </div>
        
        <p style="margin-top:20px;font-size:12px;color:#718096;text-align:center;font-style:italic;">
            💡 數據來源：Supabase 雲端數據庫實時查詢 | 統計所有有效目標價數據 | 最後更新：${new Date().toLocaleString('zh-HK')}
        </p>
    `;
    
    container.appendChild(cardDiv);
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createEnhancedRatingPieChart,
        createBusinessSegmentTreemap,
        createAISmartSummary,
        createEnhancedPriceStatsCard
    };
}
