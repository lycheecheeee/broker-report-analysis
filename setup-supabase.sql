-- ============================================================================
-- Supabase 數據庫初始化腳本
-- 用途：創建 analysis_results 表並配置索引和 RLS 策略
-- ============================================================================

-- 1. 創建分析結果表
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

-- 2. 添加註釋
COMMENT ON TABLE analysis_results IS '券商研報分析結果存儲表';
COMMENT ON COLUMN analysis_results.pdf_filename IS 'PDF 文件名';
COMMENT ON COLUMN analysis_results.broker_name IS '券商名稱';
COMMENT ON COLUMN analysis_results.rating IS '投資評級（買入/增持/持有/減持）';
COMMENT ON COLUMN analysis_results.target_price IS '目標價（HKD）';
COMMENT ON COLUMN analysis_results.current_price IS '當前股價（HKD）';
COMMENT ON COLUMN analysis_results.upside_potential IS '上行空間（%）';

-- 3. 創建索引以提升查詢性能
CREATE INDEX IF NOT EXISTS idx_analysis_user_id 
ON analysis_results(user_id);

CREATE INDEX IF NOT EXISTS idx_analysis_created_at 
ON analysis_results(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_pdf_filename 
ON analysis_results(pdf_filename);

CREATE INDEX IF NOT EXISTS idx_analysis_rating 
ON analysis_results(rating);

CREATE INDEX IF NOT EXISTS idx_analysis_broker 
ON analysis_results(broker_name);

-- 4. 配置 Row Level Security (RLS)

-- 選項 A: 完全禁用 RLS（開發階段推薦，最簡單）
ALTER TABLE analysis_results DISABLE ROW LEVEL SECURITY;

-- 選項 B: 啟用 RLS 但允許所有操作（生產環境推薦，更安全）
-- 如果需要使用選項 B，請取消以下註釋並註釋掉上面的 DISABLE 語句：
-- ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;
-- 
-- CREATE POLICY "Allow all operations for public tool"
-- ON analysis_results
-- FOR ALL
-- USING (true)
-- WITH CHECK (true);

-- 5. 驗證表結構
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'analysis_results'
ORDER BY ordinal_position;

-- 6. 顯示索引信息
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'analysis_results';

-- 7. 檢查 RLS 狀態
SELECT 
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public' 
  AND tablename = 'analysis_results';

-- ============================================================================
-- 執行完成後，你應該看到：
-- ✅ 表已創建
-- ✅ 索引已建立
-- ✅ RLS 已禁用（或已配置策略）
-- ============================================================================
