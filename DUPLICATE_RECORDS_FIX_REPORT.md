# 🔧 重複記錄問題診斷與修復報告

## 📊 問題概述

**發現時間**: 2026-04-15  
**問題描述**: Supabase 數據庫中存在嚴重重複記錄，67 條記錄對應僅 13 份 PDF 文件  
**根本原因**: `backend.py` 中的數據保存邏輯未檢查是否存在相同 `pdf_filename` 的記錄，導致每次掃描都創建新記錄

---

## 🔍 診斷結果

### 當前狀態（修復前）
- **總記錄數**: 67 條
- **唯一 PDF 文件**: 13 份
- **重複記錄**: 54 條（80.6% 冗餘率）

### 重複分佈詳情

| PDF 文件名 | 記錄數 | 應保留 | 需刪除 |
|-----------|--------|--------|--------|
| BOA-700.pdf | 7 | 1 (ID: 55) | 6 |
| UBS-700.pdf | 5 | 1 (ID: 67) | 4 |
| NOMURA-700.pdf | 5 | 1 (ID: 66) | 4 |
| MS-700.pdf | 5 | 1 (ID: 65) | 4 |
| MAC-700.pdf | 5 | 1 (ID: 64) | 4 |
| JP-700.pdf | 5 | 1 (ID: 63) | 4 |
| DEUTSCHE-700.pdf | 5 | 1 (ID: 62) | 4 |
| DAIWA-700.pdf | 5 | 1 (ID: 61) | 4 |
| CMS-700.pdf | 5 | 1 (ID: 60) | 4 |
| CMB-700.pdf | 5 | 1 (ID: 59) | 4 |
| CLSA-700.pdf | 5 | 1 (ID: 58) | 4 |
| CITIGROUP-700.pdf | 5 | 1 (ID: 57) | 4 |
| CICC-700.pdf | 5 | 1 (ID: 56) | 4 |

**總計**: 需刪除 **54 條**重複記錄

---

## 🛠️ 修復方案

### 1. 代碼修復（已完成 ✅）

**文件**: `backend.py` (Line 1620-1687)

**修改內容**:
```python
# 修復前：直接 INSERT，不檢查是否已存在
result = supabase_request('POST', 'analysis_results', data=supabase_data)

# 修復後：先檢查，再決定 UPDATE 或 INSERT
# Step 1: 檢查是否已存在相同 pdf_filename 的記錄
check_url = f"{SUPABASE_URL}/rest/v1/analysis_results?pdf_filename=eq.{filename}&select=id"
check_response = requests.get(check_url, headers=check_headers, timeout=10)
existing_records = check_response.json() if check_response.status_code == 200 else []

if existing_records and len(existing_records) > 0:
    # Step 2a: 如果已存在，執行 UPDATE 操作
    existing_id = existing_records[0]['id']
    update_url = f"{SUPABASE_URL}/rest/v1/analysis_results?id=eq.{existing_id}"
    update_response = requests.patch(update_url, headers=check_headers, json=supabase_data, timeout=10)
    analysis_id = existing_id
else:
    # Step 2b: 如果不存在，執行 INSERT 操作
    result = supabase_request('POST', 'analysis_results', data=supabase_data)
    analysis_id = result[0]['id'] if result else None
```

**改進點**:
- ✅ 避免重複插入相同 PDF 的記錄
- ✅ 如果記錄已存在，自動更新為最新數據
- ✅ 新增字段保存到數據庫（release_date, stock_name, industry 等）
- ✅ 完善的錯誤處理和日誌記錄

### 2. 數據清理工具（已創建 ✅）

#### 工具 1: `clean_duplicates.py`
**用途**: 通過直接 Supabase API 訪問清理重複記錄  
**使用方法**:
```bash
# 1. 創建 .env 文件
echo "SUPABASE_URL=https://your-project.supabase.co" > .env
echo "SUPABASE_KEY=eyJ..." >> .env

# 2. 運行清理腳本
python clean_duplicates.py
```

**功能**:
- 自動識別所有重複記錄
- 保留每份 PDF 的最新記錄（按 `created_at` 排序）
- 批量刪除重複記錄
- 驗證清理結果

#### 工具 2: `auto_clean_duplicates.py`
**用途**: 自動化清理（無需手動確認）  
**使用方法**:
```bash
python auto_clean_duplicates.py
```

**特點**:
- 無需手動輸入 `yes` 確認
- 適合 CI/CD 流程或定時任務
- 詳細的進度顯示

#### 工具 3: `clean_via_api.py`
**用途**: 通過生產環境 API 診斷重複情況  
**使用方法**:
```bash
python clean_via_api.py
```

**限制**:
- 只能識別重複記錄，無法直接刪除
- 提供手動清理指南

---

## 📋 清理步驟（推薦）

### 方法 A: 使用自動化腳本（推薦 ⭐）

```bash
# Step 1: 設置環境變數
# 創建 .env 文件，包含 SUPABASE_URL 和 SUPABASE_KEY

# Step 2: 運行自動清理
python auto_clean_duplicates.py

# Step 3: 驗證結果
python test_production.py
```

**預期結果**:
- 刪除 54 條重複記錄
- 剩餘 13 條記錄（每份 PDF 一條）
- `/broker_3quilm/api/results` 返回 13 條記錄

### 方法 B: 手動在 Supabase Dashboard 清理

1. 訪問 [Supabase Dashboard](https://app.supabase.com)
2. 選擇項目 → Table Editor → `analysis_results`
3. 按 `created_at` 降序排序
4. 對於每份 PDF，保留第一條（最新），刪除其他
5. 或使用 SQL 查詢批量刪除：

```sql
-- 查看重複記錄
SELECT pdf_filename, COUNT(*) as count, 
       ARRAY_AGG(id ORDER BY created_at DESC) as ids
FROM analysis_results
GROUP BY pdf_filename
HAVING COUNT(*) > 1;

-- 刪除重複記錄（保留每組最新的）
DELETE FROM analysis_results
WHERE id IN (
    SELECT id FROM (
        SELECT id, 
               ROW_NUMBER() OVER (PARTITION BY pdf_filename ORDER BY created_at DESC) as rn
        FROM analysis_results
    ) t
    WHERE rn > 1
);
```

---

## ✅ 驗證清單

清理完成後，請驗證以下項目：

### 1. 記錄數量驗證
```bash
python -c "import requests; r = requests.get('https://broker-report-analysis.vercel.app/broker_3quilm/api/results'); print(f'Records: {len(r.json())}')"
```
**預期**: 返回 **13** 條記錄

### 2. 無重複驗證
```bash
python clean_via_api.py
```
**預期**: 顯示 "✅ No duplicates found. Database is clean!"

### 3. 防止再犯驗證
重新掃描同一份 PDF，確認不會創建新記錄：
```bash
python test_scan.py
```
**預期**: 
- 第一次掃描：創建新記錄
- 第二次掃描：更新現有記錄（不創建新記錄）
- 總記錄數保持 13 條

### 4. API 端點驗證
```bash
python test_production.py
```
**預期**: 所有測試通過

---

## 🎯 預防措施

### 1. 數據庫層面（建議實施）

在 Supabase 中為 `pdf_filename` 添加唯一約束：

```sql
-- 添加唯一索引（防止重複插入）
CREATE UNIQUE INDEX idx_unique_pdf_filename 
ON analysis_results(pdf_filename);

-- 如果已存在重複記錄，先清理再添加約束
```

**優點**:
- 數據庫層面強制唯一性
- 即使代碼有 bug 也能防止重複
- 提升查詢性能

**注意**:
- 需要先清理現有重複記錄
- UPDATE 操作不受影響

### 2. 應用層面（已實施 ✅）

- ✅ `backend.py` 已添加重複檢查邏輯
- ✅ 使用 UPSERT 模式（UPDATE if exists, INSERT if not）
- ✅ 完善的錯誤處理和日誌記錄

### 3. 監控與告警（建議實施）

定期運行檢查腳本：

```python
# cron job: 每天凌晨 2 點運行
# 0 2 * * * cd /path/to/project && python check_duplicates.py

def check_duplicates():
    """檢查是否有重複記錄"""
    response = requests.get(f"{BASE_URL}/broker_3quilm/api/results")
    records = response.json()
    
    pdf_counts = {}
    for record in records:
        filename = record['pdf_filename']
        pdf_counts[filename] = pdf_counts.get(filename, 0) + 1
    
    duplicates = {k: v for k, v in pdf_counts.items() if v > 1}
    
    if duplicates:
        send_alert(f"發現重複記錄: {duplicates}")
    else:
        log("✅ 無重複記錄")
```

---

## 📊 影響評估

### 修復前
- ❌ 67 條記錄，54 條重複（80.6% 冗餘）
- ❌ 圖表統計不準確（平均值、中位數被拉偏）
- ❌ Excel 導出包含大量重複數據
- ❌ 存儲空間浪費
- ❌ 查詢性能下降

### 修復後
- ✅ 13 條記錄，0 條重複（0% 冗餘）
- ✅ 圖表統計準確反映真實數據
- ✅ Excel 導出乾淨無重複
- ✅ 存儲空間優化
- ✅ 查詢性能提升
- ✅ 未來不會再產生重複記錄

---

## 🚀 下一步行動

### 立即執行（優先級：高 🔴）

1. **清理現有重複記錄**
   ```bash
   python auto_clean_duplicates.py
   ```

2. **驗證清理結果**
   ```bash
   python test_production.py
   ```

3. **部署修復後的代碼**
   ```bash
   git add backend.py auto_clean_duplicates.py clean_duplicates.py clean_via_api.py
   git commit -m "fix: 防止重複記錄 - 添加 UPSERT 邏輯並創建清理工具"
   git push origin master
   ```

### 短期計劃（優先級：中 🟡）

4. **添加數據庫唯一約束**
   ```sql
   CREATE UNIQUE INDEX idx_unique_pdf_filename ON analysis_results(pdf_filename);
   ```

5. **設置監控告警**
   - 每日檢查重複記錄
   - 發現異常時發送通知

### 長期計劃（優先級：低 🟢）

6. **優化掃描策略**
   - 添加增量掃描（只掃描新文件）
   - 添加掃描歷史記錄
   - 實現定時自動掃描

7. **數據備份策略**
   - 定期備份 Supabase 數據
   - 保留歷史版本以便回滾

---

## 📝 技術細節

### API 端點行為變化

#### `/broker_3quilm/api/analyze-existing-pdf`

**修復前**:
- 每次調用都創建新記錄
- 同一 PDF 多次掃描 → 多條記錄

**修復後**:
- 首次掃描：創建新記錄（INSERT）
- 再次掃描：更新現有記錄（UPDATE）
- 同一 PDF 多次掃描 → 始終只有 1 條記錄

#### `/broker_3quilm/api/results`

**修復前**:
- 返回 67 條記錄（含 54 條重複）

**修復後**:
- 返回 13 條記錄（無重複）

#### `/broker_3quilm/api/chart-data`

**修復前**:
- 統計基於 67 條記錄（包含重複）
- 平均值、中位數不準確

**修復後**:
- 統計基於 13 條記錄（無重複）
- 數據準確反映實際情況

---

## 🎓 經驗教訓

### 問題根源
1. **缺少唯一性檢查**: 插入前未檢查是否已存在相同 `pdf_filename`
2. **缺少數據庫約束**: 未在數據庫層面添加唯一索引
3. **缺少測試覆蓋**: 未測試多次掃描同一文件的場景

### 改進措施
1. ✅ 添加應用層面的重複檢查（UPSERT 模式）
2. 🔄 建議添加數據庫唯一約束
3. ✅ 創建自動化清理工具
4. 🔄 建議添加監控告警機制

### 最佳實踐
- **防禦性編程**: 永遠不要假設數據是唯一的，始終在插入前檢查
- **數據庫約束**: 在數據庫層面強制業務規則（唯一性、外鍵等）
- **自動化測試**: 測試邊界情況（重複插入、並發寫入等）
- **監控與告警**: 定期檢查數據質量，及時發現問題

---

## 📞 支持

如有問題，請參考以下資源：

1. **清理工具**: `auto_clean_duplicates.py`, `clean_duplicates.py`
2. **測試腳本**: `test_production.py`, `test_scan.py`
3. **Supabase 文檔**: https://supabase.com/docs
4. **Vercel 日誌**: Vercel Dashboard → Functions → Logs

---

**報告生成時間**: 2026-04-15  
**修復狀態**: ✅ 代碼已修復，待清理數據  
**預計完成時間**: 5-10 分鐘（運行清理腳本）
