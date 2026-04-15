# 🔍 Dry Run 測試結果與 Supabase 連接問題診斷

## 📊 測試執行時間
**日期**: 2026-04-15 12:53  
**部署 URL**: https://broker-report-analysis.vercel.app

---

## ✅ 通過的測試

### Test A: Health Check Endpoint
- **狀態**: ✅ PASSED (HTTP 200)
- **端點**: `/broker_3quilm/api/health`
- **修復**: 添加了 `/broker_3quilm` 前綴以匹配其他端點

### Test B: List PDFs (Folder Scan)
- **狀態**: ✅ PASSED (HTTP 200)
- **端點**: `/broker_3quilm/api/list-pdfs?path=reports`
- **結果**: 找到 13 個 PDF 文件
- **首個文件**: BOA-700.pdf

### Test C: Get Results (Supabase Integration)
- **狀態**: ✅ PASSED (HTTP 200)
- **端點**: `/broker_3quilm/api/results`
- **結果**: 返回空列表 `[]`（0 條記錄）
- **說明**: API 正常工作，但 Supabase 中沒有數據

---

## ❌ 失敗的測試

### Test D: Export Analysis (Excel Generation)
- **狀態**: ❌ FAILED (HTTP 404)
- **端點**: `/broker_3quilm/api/export-analysis`
- **錯誤訊息**: `{"error":"沒有可導出的數據"}`
- **根本原因**: Supabase 中沒有數據（Records Count: 0）
- **說明**: 這不是代碼錯誤，而是預期的行為（無數據可導出）

### Test E: Single PDF Analysis & Data Persistence
- **PDF 解析**: ✅ 成功
  - Broker: 瑞銀
  - Rating: 買入
  - Target Price: HK$780.0
- **數據保存**: ❌ 失敗
  - `analysis_id`: None
  - Supabase Records: 0（未增加）

---

## 🔍 根本原因分析

### 問題：數據未能保存到 Supabase

**症狀**:
1. PDF 解析成功，返回正確的評級和目標價
2. `analyze-existing-pdf` 端點返回 HTTP 200
3. 但 `analysis_id` 為 `None`
4. `/api/results` 返回空列表
5. `/api/export-analysis` 返回 404（無數據）

**可能原因**（按可能性排序）:

#### 1️⃣ Vercel 環境變數未配置或配置錯誤（最可能）
- `SUPABASE_URL` 未設置或格式錯誤
- `SUPABASE_KEY` 未設置或使用錯誤的 key（應使用 service_role key）

**驗證方法**:
```bash
# 在 Vercel Dashboard 檢查
Settings → Environment Variables
```

**預期值**:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (service_role key, ~200 chars)
```

#### 2️⃣ Supabase 表不存在
- `analysis_results` 表未在 Supabase 中創建
- 或表名拼寫錯誤

**驗證方法**:
```sql
-- 在 Supabase SQL Editor 中運行
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'analysis_results';
```

#### 3️⃣ RLS (Row Level Security) 策略阻止寫入
- 表啟用了 RLS
- 但沒有允許匿名插入的策略

**驗證方法**:
```sql
-- 檢查 RLS 狀態
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename = 'analysis_results';
```

#### 4️⃣ 網絡連接問題
- Vercel Serverless Function 無法訪問 Supabase
- SSL/TLS 握手失敗
- 超時（當前 timeout=10s）

**驗證方法**:
查看 Vercel Function Logs 中的詳細錯誤訊息

---

## 🛠️ 修復步驟

### Step 1: 檢查 Vercel 環境變數

1. 訪問 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇項目：`broker-report-analysis`
3. 進入 **Settings** → **Environment Variables**
4. 確認以下變數已設置：

| 變數名 | 值 | 環境 |
|--------|-----|------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | Production |
| `SUPABASE_KEY` | `eyJ...` (service_role key) | Production |

**重要**:
- ✅ 必須使用 **service_role key**（不是 anon key）
- ✅ URL 必須以 `https://` 開頭
- ✅ Key 長度約 200+ 字符

### Step 2: 創建 Supabase 表（如果不存在）

在 Supabase Dashboard → SQL Editor 中運行：

```sql
CREATE TABLE IF NOT EXISTS analysis_results (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    pdf_filename TEXT NOT NULL,
    broker_name TEXT,
    rating TEXT,
    target_price FLOAT,
    current_price FLOAT,
    upside_potential FLOAT,
    ai_summary TEXT,
    prompt_used TEXT,
    release_date TEXT,
    stock_name TEXT,
    industry TEXT,
    sub_industry TEXT,
    indexes TEXT,
    investment_horizon TEXT,
    target_hit_date TEXT,
    rating_revised_date TEXT,
    target_revised_date TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加索引以提升查詢性能
CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_pdf_filename ON analysis_results(pdf_filename);
```

### Step 3: 配置 RLS 策略（如果需要匿名訪問）

```sql
-- 選項 A: 完全禁用 RLS（開發階段推薦）
ALTER TABLE analysis_results DISABLE ROW LEVEL SECURITY;

-- 選項 B: 啟用 RLS 但允許所有操作（生產環境推薦）
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations for public tool"
ON analysis_results
FOR ALL
USING (true)
WITH CHECK (true);
```

### Step 4: 重新部署到 Vercel

```bash
git add backend.py diagnose_supabase.py test_scan.py dry_run_test.py
git commit -m "Fix: Add diagnostic tools and fix health check endpoint path"
git push origin master
```

Vercel 會自動觸發部署（約 30-60 秒）。

### Step 5: 驗證修復

部署完成後，再次運行測試：

```bash
python dry_run_test.py
python test_scan.py
```

**預期結果**:
- ✅ Health Check: HTTP 200
- ✅ List PDFs: HTTP 200, 13 files
- ✅ Analyze PDF: HTTP 200, analysis_id 不為 None
- ✅ Get Results: HTTP 200, Records Count > 0
- ✅ Export Analysis: HTTP 200, Excel file generated

---

## 📋 診斷工具說明

### 1. dry_run_test.py
**用途**: 快速檢查所有 API 端點是否正常  
**運行**: `python dry_run_test.py`  
**測試內容**:
- Health Check
- List PDFs
- Get Results
- Export Analysis

### 2. test_scan.py
**用途**: 模擬完整的文件夾掃描流程  
**運行**: `python test_scan.py`  
**測試內容**:
- 列出 PDF 文件
- 分析單一 PDF
- 驗證數據持久化
- 測試 Excel 導出

### 3. diagnose_supabase.py
**用途**: 診斷 Supabase 連接問題  
**運行**: `python diagnose_supabase.py`（需要本地 .env 文件）  
**測試內容**:
- 環境變數檢查
- 表存在性檢查
- INSERT 操作測試
- 清理測試數據

---

## 🎯 下一步行動

### 立即執行:
1. ✅ 檢查 Vercel Dashboard 中的環境變數
2. ✅ 確認 Supabase 表已創建
3. ✅ 配置 RLS 策略（禁用或允許匿名訪問）
4. ✅ 重新部署並運行測試

### 如果仍然失敗:
1. 查看 Vercel Function Logs：
   ```
   Vercel Dashboard → Functions → 點擊最新部署 → Logs
   ```
2. 搜索關鍵詞：
   - `Supabase error`
   - `Supabase request failed`
   - `Failed to save to Supabase`
3. 將日誌內容提供給我進行進一步診斷

---

## 📝 總結

**當前狀態**:
- ✅ 代碼邏輯正確（已移除所有 SQLite 調用）
- ✅ API 端點正常響應（HTTP 200）
- ✅ PDF 解析功能正常
- ❌ 數據未保存到 Supabase（環境配置問題）

**核心問題**:
Vercel 環境中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 未正確配置，或 Supabase 表/RLS 策略未設置。

**解決方案**:
按照上述 Step 1-3 配置 Supabase，然後重新部署即可解決。
