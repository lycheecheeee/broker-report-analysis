# 騰訊控股 (00700.HK) 券商評級分析系統

## 📁 文件夾結構

- **reports/** - 券商研究報告PDF文件
- **src/** - Python源代碼
  - `backend.py` - Flask後端服務器
  - `parse_pdfs.py` - PDF解析腳本
  - `scrape_etnet_research.py` - 東網數據爬蟲
  - `generate_tencent_excel.py` - Excel報告生成
  - `generate_pdf_broker_report.py` - PDF報告生成
  - `generate_tencent_broker_report.py` - 騰訊券商報告生成
- **web/** - Web儀表板界面
  - `tencent_dashboard.html` - 主儀表板
  - `dashboard.html` - 通用儀表板
  - `auto_diagnosis.html` - 自動診斷頁面
  - `test_system.html` - 系統測試頁面
- **data/** - 數據文件
  - `broker_analysis.db` - SQLite數據庫
  - `broker_data.json` - JSON數據
  - `*.xlsx` - Excel報告
- **charts/** - 生成的圖表圖片
- **audio/** - 語音文件
- **docs/** - 文檔說明

## 🚀 快速開始

### 啟動後端服務
```bash
cd "c:\Users\user\Desktop\02_工作項目\Broker report 分析"
python backend.py
```

### 訪問儀表板
打開瀏覽器訪問: http://localhost:5000/tencent_dashboard.html

## 📊 功能特點

- ✅ 自動解析券商PDF報告
- ✅ 提取評級和目標價
- ✅ 可視化儀表板
- ✅ 拖拽上傳PDF
- ✅ AI智能分析
- ✅ 動態卡片排序

## 📝 數據來源

- 13家國際券商研究報告
- 東網(etnet)實時數據
- 騰訊控股財報數據

## 🔧 技術棧

- **後端**: Flask + SQLite
- **前端**: HTML5 + CSS3 + JavaScript
- **PDF解析**: PyPDF2
- **數據可視化**: Matplotlib
- **AI集成**: NVIDIA API

## 📅 更新日期

最後更新: 2026-04-10
