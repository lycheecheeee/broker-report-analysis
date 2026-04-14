# Scripts Archive - 開發腳本歸檔

**歸檔日期**: 2026-04-14  
**說明**: 此文件夾包含一次性使用的開發輔助腳本，已完成使命並歸檔保存。

---

## 📁 歸檔腳本清單

### 功能添加腳本
- `add_chart_api.py` - 添加圖表API端點
- `add_csp.py` - 添加CSP安全策略
- `add_csp_proper.py` - 正確添加CSP策略
- `add_favicon.py` - 添加網站圖標支持
- `add_folder_scan.py` - 添加文件夾掃描功能
- `add_meta_csp.py` - 添加Meta CSP標籤
- `add_simple_chart.py` - 添加簡單圖表
- `add_smart_charts.py` - 添加智能圖表
- `add_static_routes.py` - 添加靜態路由

### 檢查與診斷腳本
- `check_ai_capabilities.py` - 檢查AI能力
- `check_csp.py` - 檢查CSP配置
- `check_dashboard.py` - 檢查儀表板
- `check_old_dashboard.py` - 檢查舊儀表板
- `diagnose_api.py` - API診斷工具

### 清理與修復腳本
- `clean_routes.py` - 清理路由
- `cleanup_and_generate.py` - 清理並生成
- `fix_backend.py` - 修復後端
- `fix_csp_eval.py` - 修復CSP評估
- `fix_endpoint.py` - 修復端點
- `fix_routes.py` - 修復路由
- `fix_stocks.py` - 修復股票數據

### 創建腳本
- `create_dashboard.py` - 創建儀表板
- `create_minimal_login.py` - 創建最小化登入頁面

### 測試腳本
- `dry_run_test.py` - Dry Run測試
- `final_qa_check.py` - 最終QA檢查
- `quality_check.py` - 質量檢查
- `reverse_test.py` - 逆向測試
- `test_dashboard.py` - 儀表板測試

### 其他工具
- `extract_folder_scan.py` - 提取文件夾掃描代碼
- `organize_files.py` - 組織文件結構
- `update_config.py` - 更新配置

### 備份文件
- `backend_v2_old.py` - 後端v2版本備份
- `src_backup/` - 源代碼備份文件夾

---

## 🎯 當前使用的核心文件

### 生產環境
- ✅ `backend.py` - Flask後端主程序（唯一使用）
- ✅ `web/universal_pdf_dashboard.html` - 主儀表板
- ✅ `web/login.html` - 登入頁面
- ✅ `broker_analysis.db` - SQLite數據庫

### 文檔
- ✅ `PROJECT-STRUCTURE.md` - 項目結構說明
- ✅ `TODO.md` - 待辦清單
- ✅ `docs/traditional_chinese_optimization.md` - 繁體中文優化記錄
- ✅ `reverse_thinking_100.md` - 逆向思維原則

### 數據
- ✅ `reports/` - PDF研報源文件（13個正確版本）
- ✅ `data/` - Excel/JSON報告輸出
- ⚠️ `data/archive_corrupted_pdfs/` - 損壞PDF歸檔（13個13bytes文件）

---

## 📝 使用建議

1. **不要修改**：這些腳本已完成使命，不應再修改
2. **參考學習**：如需類似功能，可參考這些腳本的實現方式
3. **定期清理**：建議每半年審查一次，刪除完全無用的腳本
4. **版本控制**：重要腳本應提交到Git歷史記錄

---

## 🔄 歸檔標準

符合以下條件的腳本應歸檔：
- ✅ 一次性使用的開發輔助腳本
- ✅ 已被整合到主代碼的功能
- ✅ 過時或棄用的實現方案
- ✅ 測試和診斷工具（完成後）

不符合歸檔條件：
- ❌ 當前生產環境正在使用的腳本
- ❌ 需要定期運行的維護腳本
- ❌ 用戶直接調用的工具

---

**最後更新**: 2026-04-14  
**維護者**: AI Assistant
