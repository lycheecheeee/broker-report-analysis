import os
import shutil
from pathlib import Path

# 根目錄
root_dir = r'c:\Users\user\Desktop\02_工作項目\Broker report 分析'

# 定義文件夾結構
folders = {
    'reports': [],  # PDF報告
    'src': ['.py'],  # Python源代碼
    'web': ['.html'],  # Web文件
    'data': ['.db', '.json', '.xlsx'],  # 數據文件
    'charts': ['.png'],  # 圖表
    'audio': ['.mp3'],  # 音頻
    'docs': []  # 文檔
}

# 文件分類規則
file_mapping = {
    # PDF報告
    'BOA-700.pdf': 'reports',
    'CICC-700.pdf': 'reports',
    'CITIGROUP-700.pdf': 'reports',
    'CLSA-700.pdf': 'reports',
    'CMB-700.pdf': 'reports',
    'CMS-700.pdf': 'reports',
    'DAIWA-700.pdf': 'reports',
    'DEUTSCHE-700.pdf': 'reports',
    'JP-700.pdf': 'reports',
    'MAC-700.pdf': 'reports',
    'MS-700.pdf': 'reports',
    'NOMURA-700.pdf': 'reports',
    'UBS-700.pdf': 'reports',
    
    # Python源代碼
    'backend.py': 'src',
    'parse_pdfs.py': 'src',
    'scrape_etnet_research.py': 'src',
    'generate_tencent_excel.py': 'src',
    'generate_pdf_broker_report.py': 'src',
    'generate_tencent_broker_report.py': 'src',
    
    # Web文件
    'tencent_dashboard.html': 'web',
    'dashboard.html': 'web',
    'auto_diagnosis.html': 'web',
    'test_system.html': 'web',
    
    # 數據文件
    'broker_analysis.db': 'data',
    'broker_data.json': 'data',
    '騰訊控股_券商評級彙總.xlsx': 'data',
    '騰訊控股_券商評級彙總_20260409_182226.xlsx': 'data',
}

def create_folders():
    """創建文件夾結構"""
    for folder in folders.keys():
        folder_path = os.path.join(root_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"✅ 創建文件夾: {folder}")
        else:
            print(f"⚠️  文件夾已存在: {folder}")

def move_files():
    """移動文件到對應文件夾"""
    moved_count = 0
    
    for filename, target_folder in file_mapping.items():
        src_path = os.path.join(root_dir, filename)
        dst_path = os.path.join(root_dir, target_folder, filename)
        
        if os.path.exists(src_path):
            if not os.path.exists(dst_path):
                shutil.move(src_path, dst_path)
                print(f"📦 移動: {filename} -> {target_folder}/")
                moved_count += 1
            else:
                print(f"⚠️  文件已存在，跳過: {dst_path}")
        else:
            print(f"❌ 文件不存在: {src_path}")
    
    return moved_count

def handle_700_folder():
    """處理700文件夾中的PDF"""
    folder_700 = os.path.join(root_dir, '700')
    if os.path.exists(folder_700):
        pdf_files = [f for f in os.listdir(folder_700) if f.endswith('.pdf')]
        for pdf_file in pdf_files:
            src_path = os.path.join(folder_700, pdf_file)
            dst_path = os.path.join(root_dir, 'reports', pdf_file)
            
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
                print(f"📋 複製: 700/{pdf_file} -> reports/")
            else:
                print(f"⚠️  PDF已存在: {dst_path}")

def create_readme():
    """創建README.md"""
    readme_content = (
        "# 騰訊控股 (00700.HK) 券商評級分析系統\n\n"
        "## 📁 文件夾結構\n\n"
        "- **reports/** - 券商研究報告PDF文件\n"
        "- **src/** - Python源代碼\n"
        "  - `backend.py` - Flask後端服務器\n"
        "  - `parse_pdfs.py` - PDF解析腳本\n"
        "  - `scrape_etnet_research.py` - 東網數據爬蟲\n"
        "  - `generate_tencent_excel.py` - Excel報告生成\n"
        "  - `generate_pdf_broker_report.py` - PDF報告生成\n"
        "  - `generate_tencent_broker_report.py` - 騰訊券商報告生成\n"
        "- **web/** - Web儀表板界面\n"
        "  - `tencent_dashboard.html` - 主儀表板\n"
        "  - `dashboard.html` - 通用儀表板\n"
        "  - `auto_diagnosis.html` - 自動診斷頁面\n"
        "  - `test_system.html` - 系統測試頁面\n"
        "- **data/** - 數據文件\n"
        "  - `broker_analysis.db` - SQLite數據庫\n"
        "  - `broker_data.json` - JSON數據\n"
        "  - `*.xlsx` - Excel報告\n"
        "- **charts/** - 生成的圖表圖片\n"
        "- **audio/** - 語音文件\n"
        "- **docs/** - 文檔說明\n\n"
        "## 🚀 快速開始\n\n"
        "### 啟動後端服務\n"
        "```bash\n"
        'cd "c:\\Users\\user\\Desktop\\02_工作項目\\Broker report 分析"\n'
        "python backend.py\n"
        "```\n\n"
        "### 訪問儀表板\n"
        "打開瀏覽器訪問: http://localhost:5000/tencent_dashboard.html\n\n"
        "## 📊 功能特點\n\n"
        "- ✅ 自動解析券商PDF報告\n"
        "- ✅ 提取評級和目標價\n"
        "- ✅ 可視化儀表板\n"
        "- ✅ 拖拽上傳PDF\n"
        "- ✅ AI智能分析\n"
        "- ✅ 動態卡片排序\n\n"
        "## 📝 數據來源\n\n"
        "- 13家國際券商研究報告\n"
        "- 東網(etnet)實時數據\n"
        "- 騰訊控股財報數據\n\n"
        "## 🔧 技術棧\n\n"
        "- **後端**: Flask + SQLite\n"
        "- **前端**: HTML5 + CSS3 + JavaScript\n"
        "- **PDF解析**: PyPDF2\n"
        "- **數據可視化**: Matplotlib\n"
        "- **AI集成**: NVIDIA API\n\n"
        "## 📅 更新日期\n\n"
        "最後更新: 2026-04-10\n"
    )
    
    docs_folder = os.path.join(root_dir, 'docs')
    if not os.path.exists(docs_folder):
        os.makedirs(docs_folder)
    
    readme_path = os.path.join(docs_folder, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📄 創建 README.md")

def main():
    print("=" * 60)
    print("🗂️  開始整理文件夾結構...")
    print("=" * 60)
    
    # 1. 創建文件夾
    print("\n📂 步驟 1: 創建文件夾結構")
    create_folders()
    
    # 2. 處理700文件夾的PDF
    print("\n📄 步驟 2: 處理700文件夾中的PDF")
    handle_700_folder()
    
    # 3. 移動根目錄文件
    print("\n📦 步驟 3: 移動根目錄文件")
    moved = move_files()
    
    # 4. 創建README
    print("\n📝 步驟 4: 創建文檔")
    create_readme()
    
    print("\n" + "=" * 60)
    print(f"✅ 整理完成! 共移動 {moved} 個文件")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 檢查新結構是否符合預期")
    print("   - 確認所有文件都已正確移動")
    print("   - 可以安全刪除空的 700/ 文件夾")
    print("   - 更新 backend.py 中的文件路徑引用")

if __name__ == '__main__':
    main()
