# Broker Report 分析系統 - 項目結構

**項目名稱**: Broker Report Analysis System  
**版本**: v1.0  
**最後更新**: 2026-04-14  
**技術棧**: Python (Flask) + SQLite + HTML/CSS/JS + OpenRouter AI

---

## 📁 目錄結構總覽

```
Broker report 分析/
├── 📄 核心文件
│   ├── backend.py                    # ✅ Flask 後端主程序（唯一使用）
│   ├── broker_analysis.db            # ✅ SQLite 數據庫
│   ├── PROJECT-STRUCTURE.md          # ✅ 本文件
│   └── TODO.md                       # ✅ 完整待辦清單
│
├── 🌐 Web 前端
│   └── web/
│       ├── universal_pdf_dashboard.html  # ✅ 主儀表板（當前使用）
│       ├── login.html                    # ✅ 登入頁面
│       ├── favicon.ico                   # ✅ 網站圖標
│       └── archive/                      # 📦 舊版HTML文件歸檔
│           ├── README.md
│           ├── charts/                   # 智能分析圖表（5個PNG）
│           └── [8個舊版HTML文件]
│
├── 📊 數據文件
│   ├── data/
│   │   ├── broker_data.json            # JSON格式數據
│   │   ├── 騰訊控股_券商評級彙總.xlsx    # Excel報告
│   │   └── archive_corrupted_pdfs/     # ⚠️ 損壞PDF歸檔（13個）
│   │
│   └── reports/                        # ✅ PDF研報源文件（正確版本）
│       ├── BOA-700.pdf
│       ├── CICC-700.pdf
│       └── ... (共13個PDF)
│
├── 📝 文檔
│   ├── docs/
│   │   ├── README.md                   # 項目說明
│   │   ├── traditional_chinese_optimization.md  # 繁體中文優化記錄
│   │   └── 整理報告.md
│   └── reverse_thinking_100.md         # 逆向思維100條原則
│
├── 🛠️ 生成器腳本（定期使用）
│   ├── generate_tencent_broker_report.py  # 生成騰訊券商報告
│   └── generate_tencent_excel.py          # 生成Excel報告
│
├── 📦 開發腳本歸檔
│   └── scripts/
│       └── archive/                      # 🗂️ 一次性腳本歸檔
│           ├── README.md                 # 歸檔說明
│           ├── [30+個開發輔助腳本]
│           └── src_backup/               # 源代碼備份
│
├── 🔧 配置文件
│   └── config/
│       └── mcporter.json               # 配置信息
│
└── 🎵 其他
    └── audio/
        └── audio_20260409_175125.mp3   # 語音記錄
```

---

## 🎯 核心模塊說明

### 1. 後端服務 (`backend.py`)

**職責**: Flask API 服務器 + 業務邏輯

**主要功能**:
- 🔐 用戶認證系統 (JWT Token)
- 📄 PDF 文件解析 (PyPDF2)
- 🤖 AI 字段提取 (OpenRouter API - Qwen 2.5)
- 💾 數據庫存儲 (SQLite)
- 📊 數據匯總與統計
- 🌐 RESTful API 端點

**關鍵函數**:
```python
parse_pdf()                    # PDF解析
extract_broker_info()          # 提取券商信息
extract_release_date()         # 提取發布日期
generate_ai_summary_with_fields()  # AI字段提取 + 摘要
ensure_traditional_chinese()   # 繁體中文強制轉換
analyze_existing_pdf()         # 分析現有PDF文件
```

**API 端點**:
- `POST /broker_3quilm/api/login` - 用戶登入
- `POST /broker_3quilm/api/analyze-existing-pdf` - 分析PDF文件夾
- `GET /broker_3quilm/api/analysis-results` - 獲取分析結果
- `GET /broker_3quilm/universal_pdf_dashboard.html` - 主儀表板

---

### 2. 前端界面 (`web/universal_pdf_dashboard.html`)

**職責**: 用戶交互界面

**主要功能**:
- 📁 文件夾選擇 (webkitdirectory)
- 📊 實時進度條顯示
- 🎨 Glassmorphism UI 設計
- 📈 智能圖表展示 (Chart.js)
- 🔄 AI 摘要摺疊顯示
- ⚠️ 損壞文件自動跳過

**技術特點**:
- 純 HTML/CSS/JavaScript (無框架)
- 響應式設計
- 漸變色主題 (#667eea → #764ba2)
- 毛玻璃效果 (backdrop-filter)

---

### 3. 數據庫 (`broker_analysis.db`)

**職責**: 持久化存儲分析結果

**主要表格**:
```sql
users                     # 用戶表
  - id, username, password_hash, email, created_at

pdf_analyses             # PDF分析結果表
  - id, filename, broker_name, rating, target_price
  - stock_name, industry, sub_industry, indexes
  - investment_horizon, ai_summary, analyzed_at
```

---

### 4. AI 集成 (OpenRouter)

**模型**: `qwen/qwen-2.5-7b-instruct` (免費)

**提取字段**:
- ✅ 發布日期 (release_date)
- ✅ 股票名稱 (stock_name) - 智能推算
- ✅ 行業分類 (industry) - 多維度標籤
- ✅ 子行業 (sub_industry)
- ✅ 相關指數 (indexes) - 智能推算
- ✅ 投資期限 (investment_horizon) - 默認12個月
- ✅ AI 摘要 (ai_summary) - 繁體中文

**智能推算機制**:
- 從文件名提取股票代碼 (如 `BOA-700.pdf` → 騰訊控股)
- 從業務描述推斷行業分類
- 根據公司規模推算相關指數
- 後處理強制轉換英文為繁體中文 (40+ 映射表)

---

## 📦 依賴項

### Python 包
```txt
Flask==3.0.0
Flask-CORS==4.0.0
PyPDF2==3.0.1
requests==2.31.0
```

### 前端庫 (CDN)
- Chart.js 4.4.0 - 圖表繪製
- Google Fonts - Noto Sans TC (繁體中文)

---

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install flask flask-cors PyPDF2 requests
```

### 2. 啟動服務
```bash
python backend.py
```

### 3. 訪問應用
- 登入頁面: http://localhost:62190/broker_3quilm/
- 主儀表板: http://localhost:62190/broker_3quilm/universal_pdf_dashboard.html

### 4. 測試帳號
- 用戶名: `lychee`
- 密碼: `lycheechee2026`

---

## 📊 數據流程

```
用戶上傳PDF文件夾
    ↓
後端遍歷文件夾
    ↓
逐个解析PDF (PyPDF2)
    ↓
提取文本內容
    ↓
調用 OpenRouter API
    ↓
AI 提取字段 + 生成摘要
    ↓
繁體中文強制轉換
    ↓
存入 SQLite 數據庫
    ↓
返回前端展示
    ↓
生成智能圖表
```

---

## 🔒 安全注意事項

1. **API Key 管理**: OpenRouter API Key 硬編碼在 `backend.py`，生產環境應使用環境變量
2. **密碼存儲**: 使用 SHA-256 哈希，建議升級為 bcrypt
3. **CORS 配置**: 當前允許所有來源，生產環境應限制特定域名
4. **SQL 注入**: 使用參數化查詢，已防護
5. **文件驗證**: 檢查文件大小 (< 1000 bytes 視為損壞)

---

## 📝 開發規範

### 代碼風格
- Python: PEP 8
- JavaScript: ES6+
- HTML/CSS: 語義化標籤

### Git 提交規範
```
feat: 新功能
fix: 修復bug
docs: 文檔更新
style: 代碼格式
refactor: 重構
test: 測試
chore: 構建/工具
```

### 分支策略
- `main` - 生產環境
- `develop` - 開發環境
- `feature/*` - 功能分支

---

## 🧪 測試清單

### 功能測試
- [ ] PDF 解析成功率 > 95%
- [ ] AI 字段提取準確率 > 85%
- [ ] 繁體中文輸出 100%
- [ ] 損壞文件自動跳過
- [ ] 進度條實時更新

### 性能測試
- [ ] API 響應時間 < 2秒
- [ ] 單個PDF分析 < 10秒
- [ ] 批量處理吞吐量 > 50 PDF/小時
- [ ] 內存使用 < 512MB

---

## 📞 聯絡資訊

**項目維護者**: AI Assistant  
**最後審查**: 2026-04-14  
**下次審查**: 2026-04-21  

---

## 🔄 版本歷史

### v1.0 (2026-04-14)
- ✅ 基礎功能完成
- ✅ AI 智能推算字段
- ✅ 繁體中文強制輸出
- ✅ 文件歸檔整理
- ✅ 完整文檔編寫

---

**備註**: 此項目結構文檔應隨項目演進定期更新，確保準確反映當前狀態。
