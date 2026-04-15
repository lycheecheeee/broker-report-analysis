# 🚀 圖表生成問題 - 快速修復指南

**問題**: 系統完全無法生成圖表  
**根本原因**: Supabase 數據庫中沒有分析記錄  
**影響**: 所有 4 個圖表（評級分佈、券商覆蓋、時間趨勢、目標價統計）均無法顯示

---

## ✅ 已完成的修復

### 1. 前端用戶體驗改進

**文件**: `web/universal_pdf_dashboard.html`

#### 改進 1: Chart.js 載入檢查
- ✅ 在頁面加載時檢查 Chart.js 是否成功載入
- ✅ 如果載入失敗，顯示醒目的紅色警告橫幅
- ✅ Console 輸出詳細錯誤信息

#### 改進 2: 空數據友好提示
- ✅ 當 Supabase 無數據時，顯示友好的引導界面
- ✅ 提供清晰的排查步驟（3 步）
- ✅ 不再「靜默失敗」，用戶能立即知道問題所在

#### 改進 3: 錯誤重試機制
- ✅ API 請求失敗時顯示錯誤卡片
- ✅ 提供「🔄 重試」按鈕
- ✅ Toast 通知顯示具體錯誤信息

#### 改進 4: 成功反饋
- ✅ 圖表渲染成功後顯示 Toast 通知
- ✅ Console 輸出成功日志

---

## 🔧 需要執行的修復步驟

### Step 1: 配置 Supabase 環境變數（必須）

#### 選項 A: 本地測試

在項目根目錄創建 `.env` 文件：

```bash
# Windows PowerShell
echo "SUPABASE_URL=https://your-project-id.supabase.co" > .env
echo "SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." >> .env
```

#### 選項 B: Vercel 生產環境

1. 訪問 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇 `broker-report-analysis` 項目
3. Settings → Environment Variables
4. 添加：
   ```
   SUPABASE_URL = https://your-project-id.supabase.co
   SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
5. 重新部署

**如何獲取 Service Role Key**：
1. 登錄 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的項目
3. Settings → API
4. 複製 **service_role key**（⚠️ 不是 anon key）

---

### Step 2: 創建 Supabase 數據表

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

### Step 3: 重新掃描 PDF 文件

1. 訪問儀表板：
   - 本地: http://localhost:5000/broker_3quilm/universal_pdf_dashboard.html
   - 生產: https://broker-report-analysis.vercel.app

2. 輸入文件夾路徑：`reports`

3. 點擊「開始掃描」按鈕

4. 等待所有 13 個 PDF 文件分析完成（約 2-5 分鐘）

---

### Step 4: 驗證圖表生成

刷新頁面，應該看到以下內容：

#### ✅ 預期結果

1. **📊 評級分佈圓餅圖**
   - 顯示不同評級的比例
   - 每個扇區有顏色和百分比

2. **🏦 券商覆蓋 Top 10 柱狀圖**
   - 橫向柱狀圖
   - 按報告數量排序

3. **📈 最近 30 天分析趨勢折線圖**
   - 平滑曲線顯示每日分析數量

4. **💰 目標價統計卡片**
   - 4 個指標：總報告數、平均/最低/最高目標價

#### ❌ 如果仍然無法顯示

打開瀏覽器 Console（F12），檢查是否有以下錯誤：

```javascript
// 錯誤 1: Chart.js 未載入
[CHART] ❌ Chart.js 未成功載入！

// 錯誤 2: Supabase 無數據
[CHART] Supabase 中沒有數據，無法生成圖表

// 錯誤 3: API 請求失敗
[CHART] 加載失敗: TypeError: Failed to fetch
```

根據錯誤信息採取對應措施：
- **錯誤 1**: 檢查網絡連接，刷新頁面
- **錯誤 2**: 確認已完成 Step 1-3
- **錯誤 3**: 檢查後端服務是否運行

---

## 🧪 診斷工具

### 測試 API 端點

```bash
python test_charts.py
```

**預期輸出**（成功）：
```
✅ API 返回成功！
1. 評級分佈: 3 條記錄
   • 買入: 8
   • 增持: 3
   • 持有: 2
2. 目標價統計: 總報告數 13
   - 平均目標價: HK$750.50
3. 券商覆蓋: 10 家券商
4. 時間趨勢: 5 天數據
診斷結論: ✅ Supabase 中有數據，API 正常返回
```

**預期輸出**（失敗）：
```
❌ Supabase 中沒有數據
   → 根本原因: PDF 分析結果未保存到 Supabase
   → 解決方法: 配置 Vercel 環境變數 (SUPABASE_URL, SUPABASE_KEY)
```

---

## 📋 檢查清單

完成以下所有項目後，圖表應該能正常顯示：

- [ ] `.env` 文件已創建並包含正確的 Supabase 憑證
- [ ] Supabase 表中 `analysis_results` 已創建
- [ ] RLS 已禁用或已配置正確策略
- [ ] 運行 `python test_charts.py` 看到非零數據
- [ ] 已成功掃描 `reports/` 文件夾中的所有 PDF
- [ ] 瀏覽器 Console 無 JavaScript 錯誤
- [ ] 儀表板上顯示 4 個圖表/統計卡片
- [ ] 點擊「導出詳細分析報告」能下載 Excel 文件

---

## 🎯 5 分鐘快速修復

如果你想要最快的解決方案：

```bash
# 1. 創建 .env 文件（替換為你的實際值）
echo "SUPABASE_URL=https://xxx.supabase.co" > .env
echo "SUPABASE_KEY=your-key-here" >> .env

# 2. 在 Supabase SQL Editor 中執行上面的 CREATE TABLE SQL

# 3. 重新掃描 PDF
#    訪問儀表板 → 輸入 "reports" → 點擊「開始掃描」

# 4. 等待完成並刷新頁面
```

---

## 📞 需要協助？

如果按照上述步驟仍然無法解決問題，請提供：

1. `python test_charts.py` 的完整輸出
2. 瀏覽器 Console 的截圖（F12 → Console 標籤）
3. Supabase Dashboard 中 `analysis_results` 表的截圖
4. Vercel Environment Variables 頁面的截圖（隱藏敏感信息）

我會根據具體情況提供更針對性的幫助。

---

## 📝 技術說明

### 為什麼之前沒有發現這個問題？

之前的 Dry Run 測試主要關注：
- ✅ Health Check 端點
- ✅ List PDFs 功能
- ✅ PDF 解析邏輯
- ❌ **但未驗證數據是否真正保存到 Supabase**

這次診斷發現：**PDF 解析成功但數據持久化失敗**，導致圖表 API 返回空數據。

### 前端圖表渲染流程

```
用戶點擊「開始掃描」
  ↓
scanFolder() 函數
  ↓
列出 PDF 文件
  ↓
逐個分析 PDF
  ↓
保存到 Supabase ← ⚠️ 這一步失敗了！
  ↓
generateCharts() 本地圖表（基於內存數據）
  ↓
loadCharts() 從 API 加載 ← ⚠️ API 返回空數據
  ↓
{hasData?}
  ├─ Yes → 渲染 4 個圖表 ✅
  └─ No  → 顯示友好提示（新增）✅
```

### 代碼改進對比

**修復前**：
```javascript
} catch (error) {
    console.error('[CHART] 加載失敗:', error);
    // 不顯示錯誤，靜默失敗 ← 用戶完全不知道發生什麼
}
```

**修復後**：
```javascript
if (!hasData) {
    // 顯示友好的引導界面
    container.innerHTML = `
        <div class="glass-card">
            <h3>📊 暫無圖表數據</h3>
            <p>請先使用「開始掃描」功能...</p>
            <ol>排查步驟...</ol>
        </div>
    `;
    return;
}

} catch (error) {
    console.error('[CHART] 加載失敗:', error);
    
    // 顯示錯誤卡片和重試按鈕
    container.innerHTML = `
        <div class="glass-card">
            <h3>❌ 圖表加載失敗</h3>
            <button onclick="loadCharts()">🔄 重試</button>
        </div>
    `;
    
    showToast(`圖表加載失敗: ${error.message}`, 'error', 5000);
}
```

---

## 🎉 修復後的用戶體驗

### 場景 1: 首次訪問（無數據）

**之前**：空白頁面，用戶不知道為什麼沒有圖表

**現在**：
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
```

### 場景 2: 掃描完成後（有數據）

**之前**：可能靜默失敗，用戶不知道是否成功

**現在**：
```
✅ Toast 通知: 「圖表加載成功」
📊 評級分佈圓餅圖（渲染完成）
🏦 券商覆蓋柱狀圖（渲染完成）
📈 時間趨勢折線圖（渲染完成）
💰 目標價統計卡片（渲染完成）
📥 導出詳細分析報告按鈕
```

### 場景 3: API 請求失敗

**之前**：完全沒有反饋

**現在**：
```
┌──────────────────────────────────────┐
│  ❌ 圖表加載失敗                      │
│                                      │
│  Failed to fetch                     │
│                                      │
│  [🔄 重試]                           │
└──────────────────────────────────────┘

❌ Toast 通知: 「圖表加載失敗: Failed to fetch」
```

---

**最後更新**: 2026-04-13  
**狀態**: 🟡 待執行（需要配置 Supabase 環境變數）
