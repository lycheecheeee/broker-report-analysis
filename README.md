# 📊 Broker Report Analysis System

騰訊控股券商研究報告分析系統 - 自動提取、分析同可視化券商評級數據。

## ✨ 功能特點

- 🔍 **PDF 自動解析** - 從券商研報提取評級、目標價等關鍵信息
- 🤖 **AI 智能分析** - 使用 OpenRouter API 生成投資摘要
- 📈 **數據可視化** - 評級分佈、趨勢分析、統計圖表
- 📥 **Excel 導出** - 一鍵導出詳細分析報告
- 🔄 **去重機制** - 避免重複分析同一文件
- 🌐 **Web 儀表板** - 美觀嘅 Glassmorphism UI 設計

## 🚀 快速開始

### 本地運行

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 初始化數據庫並啟動服務
python backend.py

# 3. 訪問系統
# 登錄頁面: http://localhost:62190/broker_3quilm/
# 儀表板: http://localhost:62190/broker_3quilm/dashboard
```

### 默認賬號

- 用戶名: `admin`
- 密碼: `admin`

## 📁 項目結構

```
Broker report 分析/
├── backend.py              # Flask 後端主文件
├── requirements.txt        # Python 依賴
├── vercel.json            # Vercel 部署配置
├── web/                   # 前端 HTML 文件
│   ├── login.html         # 登錄頁面
│   └── universal_pdf_dashboard.html  # 儀表板
├── reports/               # PDF 研報文件夾
├── data/                  # 數據文件
└── broker_analysis.db     # SQLite 數據庫
```

## 🔧 API 端點

### 認證
- `POST /broker_3quilm/api/login` - 用戶登錄
- `POST /broker_3quilm/api/register` - 用戶註冊

### PDF 分析
- `POST /broker_3quilm/api/v1/upload` - 上傳並分析單個 PDF
- `POST /broker_3quilm/api/v1/scan/folder` - 批量掃描文件夾
- `GET /broker_3quilm/api/list-pdfs` - 列出 PDF 文件

### 數據查詢
- `GET /broker_3quilm/api/stats` - 獲取統計數據
- `GET /broker_3quilm/api/export-analysis` - 導出 Excel 報告

## 🌐 部署到 Vercel

```bash
# 1. 安裝 Vercel CLI
npm i -g vercel

# 2. 登錄 Vercel
vercel login

# 3. 部署項目
vercel

# 4. 生產環境部署
vercel --prod
```

## ⚠️ 注意事項

1. **OpenRouter API** - 需要有效嘅 API Key 同餘額
2. **數據庫** - 首次運行會自動創建 `broker_analysis.db`
3. **文件路徑** - 確保 `reports/` 文件夾存在並包含 PDF 文件
4. **端口** - 默認使用 62190 端口，可喺 `backend.py` 修改

## 🛠️ 技術棧

- **後端**: Flask (Python)
- **數據庫**: SQLite
- **前端**: HTML5 + CSS3 + JavaScript (Chart.js)
- **PDF 解析**: PyPDF2
- **AI 集成**: OpenRouter API
- **Excel 生成**: openpyxl

## 📝 許可證

MIT License
