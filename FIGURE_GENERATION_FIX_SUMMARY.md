# 圖表生成問題 - 完整診斷與修復報告

**日期**: 2026-04-13  
**狀態**: ✅ 代碼修復完成 | 🟡 待配置環境變數  
**嚴重程度**: 🔴 高（完全無法生成圖表）

---

## 📋 執行摘要

### 問題描述
用戶報告系統**完全無法生成圖表**，包括：
- 📊 評級分佈圓餅圖
- 🏦 券商覆蓋柱狀圖
- 📈 時間趨勢折線圖
- 💰 目標價統計卡片

### 根本原因
**Supabase 數據庫中沒有任何分析記錄**，導致 `/broker_3quilm/api/chart-data` API 返回空數據結構。

進一步追溯發現：
1. PDF 解析功能正常運作
2. 但分析結果**未能保存到 Supabase**
3. 原因是 **Supabase 環境變數未配置**（`SUPABASE_URL` 和 `SUPABASE_KEY`）

### 已完成的修復
✅ 前端用戶體驗大幅改進  
✅ 添加完整的錯誤處理和用戶反饋  
✅ 創建診斷工具和文檔  
✅ 所有代碼已提交並推送到 GitHub  

### 待執行的步驟
🟡 配置 Supabase 環境變數（本地 `.env` 或 Vercel Dashboard）  
🟡 在 Supabase 中創建 `analysis_results` 表  
🟡 重新掃描 PDF 文件以填充數據  

---

## 🔍 詳細診斷過程

### Step 1: API 端點測試

運行 `test_charts.py` 診斷腳本：

```bash
python test_charts.py
```

**結果**：
```
Status Code: 200
{
  "rating_distribution": [],
  "price_statistics": {
    "total_reports": 0,
    "average_price": 0,
    "min_price": 0,
    "max_price": 0
  },
  "broker_coverage": [],
  "trend_data": []
}
```

✅ API 端點存在且響應格式正確  
❌ 所有數據字段為空或零值

---

### Step 2: Supabase 連接測試

檢查本地 `.env` 文件：

```
⚠️ .env 文件不存在或為空
SUPABASE_URL: 未設置
SUPABASE_KEY: 未設置
```

**結論**：環境變數未配置，導致後端無法連接到 Supabase。

---

### Step 3: 前端代碼審查

檢查 `web/universal_pdf_dashboard.html`：

#### 發現的問題

1. **Chart.js CDN 載入無檢查**
   ```html
   <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   <!-- 沒有驗證是否成功載入 -->
   ```

2. **空數據時靜默失敗**
   ```javascript
   // Line 1301-1304 (修復前)
   } catch (error) {
       console.error('[CHART] 加載失敗:', error);
       // 不顯示錯誤，靜默失敗 ← 用戶完全不知道
   }
   ```

3. **無用戶引導**
   - 當沒有數據時，頁面空白
   - 用戶不知道需要執行什麼操作

---

## 🛠️ 實施的修復

### 修復 1: Chart.js 載入檢查

**文件**: `web/universal_pdf_dashboard.html` (Line 7-26)

```javascript
<script>
    // 檢查 Chart.js 是否成功載入
    if (typeof Chart === 'undefined') {
        console.error('[CHART] ❌ Chart.js 未成功載入！');
        console.error('[CHART] 請檢查網絡連接或 CDN 可用性');
        window.addEventListener('load', function() {
            const body = document.body;
            const warningDiv = document.createElement('div');
            warningDiv.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#f56565;color:white;padding:15px 30px;border-radius:12px;box-shadow:0 8px 24px rgba(245,101,101,0.3);z-index:99999;font-weight:bold;text-align:center;';
            warningDiv.innerHTML = `
                <div style="font-size:16px;margin-bottom:8px;">⚠️ Chart.js 載入失敗</div>
                <div style="font-size:13px;opacity:0.9;">圖表功能將無法使用，請刷新頁面重試</div>
            `;
            body.appendChild(warningDiv);
        });
    } else {
        console.log('[CHART] ✅ Chart.js 已成功載入，版本:', Chart.version || '未知');
    }
</script>
```

**效果**：
- ✅ 立即檢測 CDN 載入失敗
- ✅ 顯示醒目的紅色警告橫幅
- ✅ Console 輸出詳細錯誤信息

---

### 修復 2: 空數據友好提示

**文件**: `web/universal_pdf_dashboard.html` (Line 1260-1301)

```javascript
// 檢查是否有數據
const hasData = (
    (data.rating_distribution && data.rating_distribution.length > 0) ||
    (data.broker_coverage && data.broker_coverage.length > 0) ||
    (data.trend_data && data.trend_data.length > 0) ||
    (data.price_statistics && data.price_statistics.total_reports > 0)
);

if (!hasData) {
    console.warn('[CHART] Supabase 中沒有數據，無法生成圖表');
    console.warn('[CHART] 請確認:');
    console.warn('  1. Vercel 環境變數已配置 SUPABASE_URL 和 SUPABASE_KEY');
    console.warn('  2. Supabase 表中存在 analysis_results 表');
    console.warn('  3. 已成功掃描並分析 PDF 文件');
    
    // 顯示友好提示
    const container = document.getElementById('chartsContainer');
    container.innerHTML = `
        <div class="glass-card" style="text-align:center; padding:40px;">
            <svg style="width:64px;height:64px;fill:#cbd5e0;margin-bottom:20px;" viewBox="0 0 24 24">
                <path d="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M13,17H11V15H13V17M13,13H11V7H13V13Z"/>
            </svg>
            <h3 style="color:#667eea;margin-bottom:15px;">📊 暫無圖表數據</h3>
            <p style="color:#718096;margin-bottom:20px;line-height:1.8;">
                系統尚未收集到足夠的數據來生成圖表。<br>
                請先使用「開始掃描」功能分析 PDF 文件。
            </p>
            <div style="background:#f7fafc;padding:15px;border-radius:8px;text-align:left;max-width:500px;margin:0 auto;">
                <h4 style="color:#4a5568;margin-bottom:10px;font-size:14px;">💡 排查步驟：</h4>
                <ol style="color:#718096;font-size:13px;line-height:2;padding-left:20px;margin:0;">
                    <li>確認已輸入正確的 PDF 文件夾路徑（例如：<code>reports</code>）</li>
                    <li>點擊「開始掃描」按鈕等待分析完成</li>
                    <li>如果仍然無法顯示，請聯繫管理員檢查 Supabase 配置</li>
                </ol>
            </div>
        </div>
    `;
    document.getElementById('chartsSection').style.display = 'block';
    return;
}
```

**效果**：
- ✅ 清晰的視覺提示（圖標 + 標題 + 說明）
- ✅ 具體的排查步驟（3 步）
- ✅ 不再讓用戶面對空白頁面

---

### 修復 3: 錯誤重試機制

**文件**: `web/universal_pdf_dashboard.html` (Line 1345-1376)

```javascript
} catch (error) {
    console.error('[CHART] 加載失敗:', error);
    
    // 顯示錯誤提示
    const container = document.getElementById('chartsContainer');
    container.innerHTML = `
        <div class="glass-card" style="text-align:center; padding:40px;border-left:4px solid #f56565;">
            <svg style="width:64px;height:64px;fill:#f56565;margin-bottom:20px;" viewBox="0 0 24 24">
                <path d="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z"/>
            </svg>
            <h3 style="color:#f56565;margin-bottom:15px;">❌ 圖表加載失敗</h3>
            <p style="color:#718096;margin-bottom:20px;">
                ${error.message}
            </p>
            <button onclick="loadCharts()" style="
                background:#667eea;
                color:white;
                border:none;
                padding:10px 20px;
                border-radius:8px;
                cursor:pointer;
                font-size:14px;
            ">
                🔄 重試
            </button>
        </div>
    `;
    document.getElementById('chartsSection').style.display = 'block';
    
    showToast(`圖表加載失敗: ${error.message}`, 'error', 5000);
}
```

**效果**：
- ✅ 顯示具體錯誤消息
- ✅ 提供「🔄 重試」按鈕
- ✅ Toast 通知提醒用戶

---

### 修復 4: 成功反饋

**文件**: `web/universal_pdf_dashboard.html` (Line 1341-1342)

```javascript
console.log('[CHART] ✅ 圖表渲染成功！');
showToast('圖表加載成功', 'success', 2000);
```

**效果**：
- ✅ 用戶立即知道操作成功
- ✅ Console 日志便於調試

---

## 📁 創建的Diagnostic 工具

### 1. test_charts.py

**功能**：
- 測試 `/broker_3quilm/api/chart-data` API 端點
- 驗證返回數據結構
- 檢查 Supabase 連接狀態
- 提供具體的下一步建議

**使用方法**：
```bash
python test_charts.py
```

**示例輸出**：
```
================================================================
測試 Chart Data API
================================================================
Status Code: 200

✅ API 返回成功！

數據驗證:
1. 評級分佈: 0 條記錄 ⚠️
2. 目標價統計: 總報告數 0 ⚠️
3. 券商覆蓋: 0 家券商 ⚠️
4. 時間趨勢: 0 天數據 ⚠️

診斷結論:
❌ Supabase 中沒有數據
   → 根本原因: PDF 分析結果未保存到 Supabase
   → 解決方法: 配置 Vercel 環境變數 (SUPABASE_URL, SUPABASE_KEY)
```

---

### 2. CHART_DIAGNOSIS_REPORT.md

**內容**：
- 完整的問題分析
- 根本原因說明
- 詳細的修復步驟（Step 1-5）
- Supabase SQL 建表語句
- RLS 配置指南
- 檢查清單

**用途**：技術人員參考文檔

---

### 3. QUICK_FIX_CHARTS.md

**內容**：
- 5 分鐘快速修復指南
- 簡化的步驟說明
- 常見問題解答
- 用戶體驗對比（修復前後）

**用途**：快速上手指南

---

## 🎯 下一步行動

### 必須執行的步驟

#### Step 1: 獲取 Supabase 憑證

1. 訪問 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的項目
3. Settings → API
4. 複製以下信息：
   - **Project URL**: `https://xxx.supabase.co`
   - **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

⚠️ **重要**：必須使用 **service_role key**，不是 anon key！

---

#### Step 2: 配置環境變數

##### 選項 A: 本地測試

在項目根目錄創建 `.env` 文件：

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

##### 選項 B: Vercel 生產環境

1. 訪問 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇 `broker-report-analysis` 項目
3. Settings → Environment Variables
4. 添加：
   ```
   SUPABASE_URL = https://your-project-id.supabase.co
   SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
5. 重新部署

---

#### Step 3: 創建 Supabase 表

在 Supabase SQL Editor 中執行：

```sql
-- 創建分析結果表
CREATE TABLE IF NOT EXISTS analysis_results (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1,
    pdf_filename TEXT,
    broker_name TEXT,
    stock_name TEXT DEFAULT '騰訊控股',
    industry TEXT DEFAULT '互聯網',
    sub_industry TEXT DEFAULT '社交媒體',
    indexes TEXT DEFAULT '恒生指數',
    rating TEXT,
    target_price DECIMAL(10, 2),
    current_price DECIMAL(10, 2),
    upside_potential DECIMAL(10, 2),
    release_date TEXT,
    target_hit_date TEXT,
    rating_revised_date TEXT,
    target_revised_date TEXT,
    investment_horizon TEXT DEFAULT '12個月',
    ai_summary TEXT,
    upload_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at 
ON analysis_results(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_results_rating 
ON analysis_results(rating);

CREATE INDEX IF NOT EXISTS idx_analysis_results_broker 
ON analysis_results(broker_name);

-- 禁用 RLS（開發階段）
ALTER TABLE analysis_results DISABLE ROW LEVEL SECURITY;
```

---

#### Step 4: 重新掃描 PDF

1. 訪問儀表板：
   - 本地: http://localhost:5000/broker_3quilm/universal_pdf_dashboard.html
   - 生產: https://broker-report-analysis.vercel.app

2. 輸入文件夾路徑：`reports`

3. 點擊「開始掃描」按鈕

4. 等待所有 13 個 PDF 文件分析完成（約 2-5 分鐘）

---

#### Step 5: 驗證圖表

刷新頁面，應該看到：

✅ **📊 評級分佈圓餅圖**  
✅ **🏦 券商覆蓋 Top 10 柱狀圖**  
✅ **📈 最近 30 天分析趨勢折線圖**  
✅ **💰 目標價統計卡片**  

---

## 📊 預期結果

### 成功場景

運行 `python test_charts.py` 應該看到：

```
✅ API 返回成功！

數據驗證:
1. 評級分佈: 3 條記錄
   • 買入: 8
   • 增持: 3
   • 持有: 2

2. 目標價統計:
   - 總報告數: 13
   - 平均目標價: HK$750.50
   - 最低目標價: HK$680.00
   - 最高目標價: HK$820.00

3. 券商覆蓋: 10 家券商
   • 瑞銀: 2 份報告
   • 摩根士丹利: 2 份報告
   • 高盛: 1 份報告
   ...

4. 時間趨勢: 5 天數據

診斷結論:
✅ Supabase 中有數據，API 正常返回
   → 問題可能在前端 JavaScript 或 Chart.js 載入
```

---

## 📝 Git 提交記錄

```bash
commit cb5800f
Author: lycheecheeee
Date: 2026-04-13

fix: 修復圖表生成問題 - 添加用戶友好提示和錯誤處理

- 新增 Chart.js 載入檢查，失敗時顯示警告橫幅
- 改進 loadCharts() 函數，空數據時顯示引導界面
- 添加錯誤重試機制和 Toast 通知
- 創建診斷工具 test_charts.py
- 創建詳細診斷報告 CHART_DIAGNOSIS_REPORT.md
- 創建快速修復指南 QUICK_FIX_CHARTS.md

根本原因：Supabase 無數據導致圖表 API 返回空結果
解決方案：配置環境變數後重新掃描 PDF
```

**修改的文件**：
- `web/universal_pdf_dashboard.html` (+91 行)
- `test_charts.py` (新建，182 行)
- `CHART_DIAGNOSIS_REPORT.md` (新建，370 行)
- `QUICK_FIX_CHARTS.md` (新建，381 行)

**總計**: +1,024 行代碼和文檔

---

## 🎨 用戶體驗對比

### 修復前

**場景 1: 首次訪問（無數據）**
```
[空白頁面]
用戶: 「為什麼沒有圖表？是不是壞了？」
```

**場景 2: API 請求失敗**
```
[空白頁面]
Console: [CHART] 加載失敗: TypeError: Failed to fetch
用戶: （完全不知道發生什麼）
```

**場景 3: Chart.js 未載入**
```
[JavaScript 錯誤]
Console: Uncaught ReferenceError: Chart is not defined
用戶: 「網頁怎麼沒反應？」
```

---

### 修復後

**場景 1: 首次訪問（無數據）**
```
┌──────────────────────────────────────┐
│  📊 暫無圖表數據                      │
│                                      │
│  系統尚未收集到足夠的數據來生成圖表。  │
│  請先使用「開始掃描」功能分析 PDF 文件。│
│                                      │
│  💡 排查步驟：                        │
│  1. 確認已輸入正確的 PDF 文件夾路徑   │
│  2. 點擊「開始掃描」按鈕等待分析完成  │
│  3. 如果仍然無法顯示，請聯繫管理員    │
└──────────────────────────────────────┘

用戶: 「哦，我需要先掃描文件！」
```

**場景 2: API 請求失敗**
```
┌──────────────────────────────────────┐
│  ❌ 圖表加載失敗                      │
│                                      │
│  Failed to fetch                     │
│                                      │
│  [🔄 重試]                           │
└──────────────────────────────────────┘

❌ Toast: 「圖表加載失敗: Failed to fetch」

用戶: 「我可以點擊重試，或者檢查網絡」
```

**場景 3: Chart.js 未載入**
```
┌──────────────────────────────────────┐
│  ⚠️ Chart.js 載入失敗                │
│  圖表功能將無法使用，請刷新頁面重試    │
└──────────────────────────────────────┘

Console: [CHART] ❌ Chart.js 未成功載入！

用戶: 「我知道是 CDN 問題，刷新試試」
```

**場景 4: 成功加載**
```
✅ Toast: 「圖表加載成功」

📊 評級分佈圓餅圖（渲染完成）
🏦 券商覆蓋柱狀圖（渲染完成）
📈 時間趨勢折線圖（渲染完成）
💰 目標價統計卡片（渲染完成）
📥 導出詳細分析報告按鈕

用戶: 「太棒了！所有圖表都顯示了！」
```

---

## 🔗 相關資源

### 文檔
- [CHART_DIAGNOSIS_REPORT.md](./CHART_DIAGNOSIS_REPORT.md) - 詳細技術診斷
- [QUICK_FIX_CHARTS.md](./QUICK_FIX_CHARTS.md) - 5 分鐘快速修復
- [DRY_RUN_TEST_RESULTS.md](./DRY_RUN_TEST_RESULTS.md) - 之前的 Dry Run 測試報告

### 工具
- [test_charts.py](./test_charts.py) - API 診斷腳本
- [test_scan.py](./test_scan.py) - 完整掃描流程測試
- [diagnose_supabase.py](./diagnose_supabase.py) - Supabase 連接診斷

### 代碼
- [web/universal_pdf_dashboard.html](./web/universal_pdf_dashboard.html) - 前端主頁面
- [backend.py](./backend.py) - 後端 API（Line 1455-1533）

---

## 💡 經驗教訓

### 1. 錯誤處理的重要性

**之前**：靜默失敗，用戶完全不知道問題所在  
**現在**：清晰的錯誤提示和引導，用戶能自主排查

### 2. 用戶反饋的關鍵性

**之前**：無任何反饋，用戶面對空白頁面  
**現在**：Toast 通知 + 視覺提示，用戶立即知道狀態

### 3. 診斷工具的價值

**之前**：手動檢查每個環節，耗時且容易遺漏  
**現在**：一鍵運行 `test_charts.py`，快速定位問題

### 4. 文檔的必要性

**之前**：問題重複出現，每次都要重新診斷  
**現在**：完整的文檔記錄，未來可快速參考

---

## 📞 支援

如果在執行上述步驟時遇到問題，請提供：

1. `python test_charts.py` 的完整輸出
2. 瀏覽器 Console 的截圖（F12 → Console 標籤）
3. Supabase Dashboard 中 `analysis_results` 表的截圖
4. Vercel Environment Variables 頁面的截圖（隱藏敏感信息）

我會根據具體情況提供更針對性的幫助。

---

**最後更新**: 2026-04-13  
**狀態**: ✅ 代碼修復完成 | 🟡 待配置環境變數  
**下一個里程碑**: 配置 Supabase 後驗證圖表正常顯示
