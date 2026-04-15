# 🚀 Supabase 配置快速啟動指南

**目標**: 5 分鐘內完成 Supabase 配置，讓圖表功能正常工作

---

## 📋 前置準備

### 1. 獲取 Supabase 憑證

1. 訪問 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的項目（或創建新項目）
3. 點擊左側菜單 **Settings** → **API**
4. 複製以下信息：

   - **Project URL**: `https://xxx.supabase.co`
   - **service_role key**: `eyJhbGci...` (長約 200+ 字符)

⚠️ **重要**：必須使用 **service_role key**，不是 anon key！

---

## 🔧 自動化配置（推薦）

### 方法 A: 使用 PowerShell 腳本（最簡單）

```powershell
# 在項目根目錄運行
powershell -ExecutionPolicy Bypass -File setup-supabase-env.ps1
```

腳本會自動：
1. ✅ 檢查 Vercel CLI 是否安裝
2. ✅ 提示輸入 Supabase 憑證
3. ✅ 設置 Vercel 環境變數
4. ✅ 提交代碼到 GitHub
5. ✅ 重新部署到 Vercel

---

### 方法 B: 手動配置 Vercel Dashboard

如果不想用腳本，可以手動操作：

1. 訪問 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇項目：`broker-report-analysis`
3. Settings → **Environment Variables**
4. 添加以下變數：

   | 變數名 | 值 | 環境 |
   |--------|-----|------|
   | `SUPABASE_URL` | `https://xxx.supabase.co` | Production |
   | `SUPABASE_KEY` | `eyJhbGci...` | Production |

5. 點擊 **Save**
6. 重新部署項目（Deployments → Redeploy）

---

## 🗄️ 創建數據庫表

### 步驟 1: 打開 Supabase SQL Editor

1. 訪問 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的項目
3. 左側菜單 **SQL Editor**
4. 點擊 **New Query**

### 步驟 2: 執行建表 SQL

複製 `setup-supabase.sql` 文件的內容，粘貼到 SQL Editor，然後點擊 **Run**。

或者直接在 SQL Editor 中執行以下簡化版：

```sql
-- 創建表
CREATE TABLE IF NOT EXISTS analysis_results (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1,
    pdf_filename TEXT NOT NULL,
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
    prompt_used TEXT,
    upload_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_rating ON analysis_results(rating);
CREATE INDEX IF NOT EXISTS idx_analysis_broker ON analysis_results(broker_name);

-- 禁用 RLS（開發階段）
ALTER TABLE analysis_results DISABLE ROW LEVEL SECURITY;
```

### 步驟 3: 驗證表已創建

在 SQL Editor 中運行：

```sql
SELECT COUNT(*) FROM analysis_results;
```

應該返回 `0`（表示表已創建但還沒有數據）。

---

## ✅ 驗證配置

### 測試 1: 運行診斷腳本

```bash
python test_charts.py
```

**預期輸出**（成功）：
```
✅ API 返回成功！

數據驗證:
1. 評級分佈: 0 條記錄（正常，因為還沒掃描 PDF）
2. 目標價統計: 總報告數 0
3. 券商覆蓋: 0 家券商
4. 時間趨勢: 0 天數據

診斷結論: ✅ Supabase 連接正常，等待掃描 PDF
```

**預期輸出**（失敗）：
```
❌ Supabase 中沒有數據
   → 根本原因: 環境變數未配置或表不存在
```

### 測試 2: 掃描 PDF 文件

1. 訪問儀表板：
   - 本地: http://localhost:5000/broker_3quilm/universal_pdf_dashboard.html
   - 生產: https://broker-report-analysis.vercel.app

2. 輸入文件夾路徑：`reports`

3. 點擊「開始掃描」按鈕

4. 等待所有 13 個 PDF 分析完成（約 2-5 分鐘）

### 測試 3: 查看圖表

掃描完成後，刷新頁面，應該看到：

- ✅ 📊 評級分佈圓餅圖
- ✅ 🏦 券商覆蓋 Top 10 柱狀圖
- ✅ 📈 最近 30 天分析趨勢折線圖
- ✅ 💰 目標價統計卡片

### 測試 4: 導出 Excel

點擊「📥 導出詳細分析報告 (Excel)」按鈕，應該能下載 Excel 文件。

---

## 🐛 常見問題排查

### 問題 1: Vercel CLI 未安裝

**錯誤訊息**：
```
'vercel' 不是內部或外部命令
```

**解決方案**：
```bash
npm install -g vercel
```

---

### 問題 2: Service Role Key 錯誤

**錯誤訊息**：
```
Supabase request failed: Invalid API key
```

**解決方案**：
1. 確認使用的是 **service_role key**（不是 anon key）
2. service_role key 長度約 200+ 字符
3. 在 Supabase Dashboard → Settings → API 重新複製

---

### 問題 3: 表不存在

**錯誤訊息**：
```
relation "analysis_results" does not exist
```

**解決方案**：
1. 在 Supabase SQL Editor 中執行 `setup-supabase.sql`
2. 確認表名拼寫正確（`analysis_results`）

---

### 問題 4: RLS 策略阻止寫入

**錯誤訊息**：
```
new row violates row-level security policy
```

**解決方案**：
在 Supabase SQL Editor 中運行：
```sql
ALTER TABLE analysis_results DISABLE ROW LEVEL SECURITY;
```

---

### 問題 5: 圖表仍然不顯示

**檢查清單**：
1. ✅ 環境變數已配置（Vercel Dashboard → Environment Variables）
2. ✅ 表已創建（Supabase SQL Editor → 運行 SELECT COUNT(*)）
3. ✅ RLS 已禁用（`ALTER TABLE ... DISABLE ROW LEVEL SECURITY`）
4. ✅ 已掃描 PDF 文件（儀表板 → 開始掃描）
5. ✅ 瀏覽器 Console 無錯誤（F12 → Console 標籤）

**調試步驟**：
```bash
# 1. 檢查 API 響應
python test_charts.py

# 2. 檢查 Vercel Function Logs
# Vercel Dashboard → Functions → 最新部署 → Logs

# 3. 檢查瀏覽器 Console
# F12 → Console → 搜索 "[CHART]"
```

---

## 📞 需要協助？

如果按照上述步驟仍然無法解決問題，請提供：

1. `python test_charts.py` 的完整輸出
2. 瀏覽器 Console 截圖（F12 → Console 標籤）
3. Supabase Table Editor 截圖（顯示 analysis_results 表）
4. Vercel Environment Variables 截圖（隱藏敏感信息）

我會根據具體情況提供針對性幫助。

---

## 🎯 下一步

配置完成後，你可以：

1. **掃描更多 PDF 文件**：上傳新的券商研報
2. **查看歷史分析**：所有分析結果都會保存在 Supabase
3. **導出 Excel 報告**：點擊「導出詳細分析報告」按鈕
4. **分享儀表板**：將 Vercel Link 分享給團隊成員

---

**最後更新**: 2026-04-13  
**狀態**: 🟢 就緒（等待你執行配置步驟）
