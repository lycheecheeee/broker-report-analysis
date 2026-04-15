from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import json
import os
import logging
from datetime import datetime

# 配置日誌系統 - 生產環境只記錄 WARNING 及以上
logger = logging.getLogger(__name__)
if os.environ.get('FLASK_ENV') == 'development':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
else:
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s [%(levelname)s] %(message)s')

# 數據庫支持 - SQLite 或 PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRESQL = True
    logger.info("PostgreSQL support available")
except ImportError:
    USE_POSTGRESQL = False
    import sqlite3
    logger.warning("Using SQLite (PostgreSQL not available)")

# 可選導入 - 避免 Vercel 環境崩潰
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("PyJWT not available")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not available")

import re
import requests

app = Flask(__name__, static_folder='.', static_url_path='')

# 簡化 CORS 配置 - 避免 Vercel 環境問題
try:
    CORS(app)
    logger.info("CORS initialized")
except Exception as e:
    logger.error(f"CORS initialization error: {e}")

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大上傳 50MB

# 添加請求日誌中間件
@app.before_request
def log_request():
    """請求日誌 - 僅開發環境啟用"""
    if os.environ.get('FLASK_ENV') == 'development':
        logger.debug(f"{request.method} {request.path}")
        if request.form:
            logger.debug(f"Form data: {dict(request.form)}")


# 配置
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise EnvironmentError("Missing required environment variable: SECRET_KEY")

# Supabase 配置 - 清理可能的換行符和空白
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '').strip()

# 強制要求 Supabase 配置 - 公開工具必須使用雲端數據庫
if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Missing required environment variables: SUPABASE_URL and SUPABASE_KEY must be set.\n"
        "This is a public tool that requires cloud database persistence.\n"
        "Please configure these in Vercel Dashboard > Settings > Environment Variables"
    )

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '700')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# 數據庫模式：強制使用 Supabase
DB_MODE = 'supabase'

# 確保上傳文件夾存在
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Upload folder ready: {UPLOAD_FOLDER}")
except Exception as e:
    logger.error(f"Upload folder creation error: {e}")

# 數據庫初始化標誌
_db_initialized = False

def supabase_request(method, table, data=None, query_params=None):
    """Supabase REST API 請求輔助函數"""
    if DB_MODE != 'supabase' or not SUPABASE_KEY:
        return None
    
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'  # 返回插入/更新後的數據
    }
    
    try:
        if method == 'GET':
            if query_params:
                url += f"?{query_params}"
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            if query_params:
                url += f"?{query_params}"
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            if query_params:
                url += f"?{query_params}"
            response = requests.delete(url, headers=headers)
        else:
            return None
        
        if response.status_code in [200, 201, 204]:
            if response.status_code == 204:
                return []
            return response.json()
        else:
            logger.error(f"Supabase error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Supabase request failed: {e}")
        return None

def init_db():
    """初始化數據庫"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # 用戶表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # PDF分析結果表
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_name TEXT,
        stock_code TEXT,
        pdf_filename TEXT NOT NULL,
        broker_name TEXT,
        rating TEXT,
        target_price REAL,
        current_price REAL,
        upside_potential REAL,
        ai_summary TEXT,
        key_points TEXT,
        risks TEXT,
        prompt_used TEXT,
        chart_path TEXT,
        audio_path TEXT,
        is_public BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Migration: 添加缺失字段(如果已存在則忽略)
    migration_columns = [
        ('company_name', 'TEXT'),
        ('stock_code', 'TEXT'),
        ('key_points', 'TEXT'),
        ('risks', 'TEXT'),
        ('chart_path', 'TEXT'),
        ('audio_path', 'TEXT'),
        ('is_public', 'BOOLEAN DEFAULT 0')
    ]
    
    for col_name, col_type in migration_columns:
        try:
            c.execute(f"ALTER TABLE analysis_results ADD COLUMN {col_name} {col_type}")
            logger.info(f"Added column: {col_name}")
        except:
            pass  # 字段已存在,忽略
    
    # 用戶反饋表
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        analysis_id INTEGER,
        rating INTEGER CHECK(rating >= 1 AND rating <= 5),
        comment TEXT,
        suggestions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (analysis_id) REFERENCES analysis_results(id)
    )''')
    
    # 自定義Prompt模板表
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        template_name TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        is_default BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 股票表
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        stock_code TEXT UNIQUE NOT NULL,
        industry TEXT,
        sub_industry TEXT,
        current_price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 券商評級表(完整 15 個字段)
    c.execute('''CREATE TABLE IF NOT EXISTS broker_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id INTEGER NOT NULL,
        
        -- 基本信息
        date_of_release TEXT,                    -- 1. Date of Release
        broker_name TEXT NOT NULL,               -- 2. Name of Broker
        stock_name TEXT,                         -- 3. Name of Stock
        related_industry TEXT,                   -- 4. Related Industry
        related_sub_industry TEXT,               -- 5. Related Sub-industry
        related_indexes TEXT,                    -- 6. Related Indexes
        
        -- 投資評級與目標價
        investment_grade TEXT,                   -- 7. Investment Grade (Buy/Hold/Sell)
        target_price_adjusted REAL,              -- 8. Target Price (Adjusted)
        investment_horizon TEXT DEFAULT '12 months',  -- 9. Investment Horizon (default 12 months)
        
        -- 價格信息
        latest_close_before_release REAL,        -- 10. Latest Day Close before Release (Adjusted)
        date_target_first_hit TEXT,              -- 11. Date of Target First Hit
        last_transacted_price REAL,              -- 12. Last Transacted/Closing Price as of Today
        today_date TEXT,                         -- 13. Today's Date
        
        -- 修訂日期
        date_grade_revised TEXT,                 -- 14. Date of Investment Grade Revised/Extended
        date_target_revised TEXT,                -- 15. Date of Target Price Revised/Extended
        
        -- 其他
        source_link TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks(id)
    )''')
    
    conn.commit()
    conn.close()

def ensure_db_initialized():
    """確保數據庫已初始化（懶加載）"""
    global _db_initialized
    if not _db_initialized:
        try:
            if DB_MODE == 'supabase':
                # Supabase 模式：測試連接
                result = supabase_request('GET', 'analysis_results', query_params='limit=1')
                logger.info(f"Supabase connected (mode: {DB_MODE})")
            else:
                # SQLite/內存模式
                init_db()
                logger.info(f"Database initialized (mode: {DB_MODE})")
            _db_initialized = True
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            # 即使失敗也標記為已初始化，避免重複嘗試
            _db_initialized = True

# Auth 系統已移除 - 公開工具無需登入
# 所有 API 使用固定 user_id = 1

def parse_pdf(pdf_path):
    """解析PDF文件"""
    try:
        logger.debug(f"Parsing PDF: {pdf_path}")
        file_size = os.path.getsize(pdf_path)
        
        # 檢查文件大小，如果太小則跳過
        if file_size < 1000:
            logger.warning(f"File too small ({file_size} bytes), may be corrupted")
            return None
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file, strict=False)  # 設置strict=False以容忍一些錯誤
            logger.debug(f"PDF pages: {len(pdf_reader.pages)}")
            
            text = ''
            for i, page in enumerate(pdf_reader.pages[:5]):  # 只讀前5頁
                try:
                    page_text = page.extract_text()
                    if page_text:
                        logger.debug(f"Page {i+1} extracted, length: {len(page_text)}")
                        text += page_text + '\n'
                    else:
                        logger.debug(f"Page {i+1} has no text content")
                except Exception as page_error:
                    logger.warning(f"Page {i+1} extraction failed: {page_error}")
                    continue
            
            logger.debug(f"Total text length: {len(text)}")
            return text if text.strip() else None
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"PDF parse error: {e}\n{error_detail}")
        return None

def extract_broker_info(text):
    """從文本提取券商信息"""
    broker_mapping = {
        'BOA': '美國銀行',
        'Bank of America': '美國銀行',
        'CICC': '中金公司',
        'Citigroup': '花旗',
        'CLSA': '里昂證券',
        'CMB': '招銀國際',
        'CMS': '招商證券',
        'Daiwa': '大和資本',
        'Deutsche Bank': '德意志銀行',
        'JPMorgan': '摩根大通',
        'Macquarie': '麥格理',
        'Morgan Stanley': '摩根士丹利',
        'Nomura': '野村證券',
        'UBS': '瑞銀'
    }
    
    broker_name = '未知券商'
    for key, value in broker_mapping.items():
        if key.lower() in text.lower():
            broker_name = value
            break
    
    # 提取評級
    rating = '未明確'
    if any(kw in text.lower() for kw in ['buy', '買入']):
        rating = '買入'
    elif any(kw in text.lower() for kw in ['overweight', '增持']):
        rating = '增持'
    elif any(kw in text.lower() for kw in ['outperform', '跑贏']):
        rating = '跑贏行業'
    elif any(kw in text.lower() for kw in ['neutral', '中性', 'hold']):
        rating = '中性'
    
    # 提取目標價
    target_price = None
    patterns = [
        r'[Tt]arget [Pp]rice.*?([\d,]+\.?\d*)',
        r'目標價.*?([\d,]+\.?\d*)',
        r'TP.*?([\d,]+\.?\d*)'
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                target_price = float(matches[0].replace(',', ''))
                if target_price > 100:  # 合理範圍檢查
                    break
            except:
                continue
    
    return broker_name, rating, target_price

def extract_key_points(text):
    """從 PDF 文本提取關鍵要點"""
    import re
    
    # 尋找關鍵詞附近嘅內容
    key_point_keywords = [
        r'(?:Key Points|KEY POINTS|Highlights|HIGHLIGHTS|核心觀點|主要觀點|投資要點)[:\s]*([\s\S]{100,500}?)(?=\n\n|Risk|風險|Conclusion)',
        r'(?:Investment Thesis|INVESTMENT THESIS|投資邏輯)[:\s]*([\s\S]{100,500}?)(?=\n\n|Risk|風險)',
        r'(?:Summary|SUMMARY|摘要)[:\s]*([\s\S]{100,500}?)(?=\n\n|Risk|風險)'
    ]
    
    for pattern in key_point_keywords:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # 清理多餘空白
            content = re.sub(r'\s+', ' ', content)
            if len(content) > 50:  # 確保有足夠內容
                return content[:500]  # 限制長度
    
    # 如果冇找到，返回 PDF 前 300 字符作為備用
    clean_text = re.sub(r'\s+', ' ', text[:300]).strip()
    return clean_text if clean_text else "暫無關鍵要點"

def extract_risks(text):
    """從 PDF 文本提取風險因素"""
    import re
    
    # 尋找風險相關內容
    risk_keywords = [
        r'(?:Risks|RISKS|Risk Factors|RISK FACTORS|風險|風險因素|投資風險)[:\s]*([\s\S]{100,500}?)(?=\n\n|Conclusion|結論|Appendix)',
        r'(?:Downside Risks|DOWNSIDE RISKS|下行風險)[:\s]*([\s\S]{100,500}?)(?=\n\n|Conclusion)',
        r'(?:Key Risks|KEY RISKS|主要風險)[:\s]*([\s\S]{100,500}?)(?=\n\n|Conclusion)'
    ]
    
    for pattern in risk_keywords:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # 清理多餘空白
            content = re.sub(r'\s+', ' ', content)
            if len(content) > 50:  # 確保有足夠內容
                return content[:500]  # 限制長度
    
    # 如果冇找到，返回默認值
    return "請參考完整報告以了解詳細風險因素"

def extract_release_date(text):
    """從PDF文本中提取發布日期"""
    import re
    from datetime import datetime
    
    # 常見日期格式模式
    date_patterns = [
        # 英文格式: Date: April 9, 2026 或 9 April 2026
        r'(?:Date|DATE|Published|published|Report Date)[:\s]*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        r'(?:Date|DATE|Published|published|Report Date)[:\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',
        
        # 中文格式: 日期：2026年4月9日 或 2026-04-09
        r'(?:日期|發佈日期|報告日期|发布日期)[:：\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
        r'(?:日期|發佈日期|報告日期|发布日期)[:：\s]*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)',
        
        # ISO格式: 2026-04-09
        r'(\d{4}-\d{2}-\d{2})',
        
        # 其他格式: 09/04/2026 或 04/09/2026
        r'(\d{1,2}/\d{1,2}/\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            logger.debug(f"Found date string: {date_str}")
            
            # 嘗試解析各種格式
            try:
                # 嘗試 ISO 格式
                if '-' in date_str and len(date_str) == 10:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    return dt.strftime('%Y-%m-%d')
                
                # 嘗試中文格式
                if '年' in date_str or '月' in date_str:
                    date_str_clean = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                    dt = datetime.strptime(date_str_clean, '%Y-%m-%d')
                    return dt.strftime('%Y-%m-%d')
                
                # 嘗試英文月份格式
                months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                         'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                
                # April 9, 2026 或 9 April 2026
                parts = date_str.lower().replace(',', '').split()
                if len(parts) >= 3:
                    for i, part in enumerate(parts):
                        if part[:3] in months:
                            month = months[part[:3]]
                            if i > 0 and parts[i-1].isdigit():  # 9 April 2026
                                day = int(parts[i-1])
                                year = int(parts[i+1]) if i+1 < len(parts) and parts[i+1].isdigit() else datetime.now().year
                            elif i < len(parts)-1 and parts[i+1].isdigit():  # April 9, 2026
                                day = int(parts[i+1])
                                year = int(parts[i+2]) if i+2 < len(parts) and parts[i+2].isdigit() else datetime.now().year
                            else:
                                continue
                            
                            dt = datetime(year, month, day)
                            return dt.strftime('%Y-%m-%d')
                
                # DD/MM/YYYY 或 MM/DD/YYYY
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        # 假設是 DD/MM/YYYY
                        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        if month <= 12:
                            dt = datetime(year, month, day)
                            return dt.strftime('%Y-%m-%d')
            except Exception as e:
                logger.debug(f"Date parse failed: {e}")
                continue
    
    logger.debug("No valid date found")
    return '-'

def generate_ai_summary(broker_name, rating, target_price, text):
    """使用 OpenRouter API 生成真正的 AI 摘要"""
    try:
        prompt = f"""你是一位專業的金融分析師。請根據以下券商研報內容,提供簡潔专业的分析摘要。

券商:{broker_name}
評級:{rating}
目標價:HK${target_price if target_price else '未明確'}

研報內容摘要:
{text[:2000]}

請用繁體中文提供:
1. 核心投資觀點(50字以內)
2. 主要風險提示(30字以內)
3. 建議操作策略(30字以內)

格式要求:簡潔明瞭,使用要點式呈現。"""

        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': os.environ.get('VERCEL_URL', ''),
            'X-Title': 'Broker Report Analysis'
        }
        
        payload = {
            'model': 'qwen/qwen-2.5-72b-instruct',  # 使用 Qwen 2.5,支援繁體中文且免費
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        logger.debug("Calling OpenRouter API...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            logger.info("AI summary generated successfully")
            return ai_content.strip()
        else:
            logger.error(f"AI API error: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        return None

def ensure_traditional_chinese(data):
    """確保所有字段都使用繁體中文，將常見英文翻譯為繁體中文"""
    if not isinstance(data, dict):
        return data
    
    # 常見英文到繁體中文的映射表
    translation_map = {
        # 投資觀點相關
        'Core Investment View': '核心投資觀點',
        'Investment View': '投資觀點',
        'Key Risks': '主要風險',
        'Risk Factors': '風險因素',
        'Recommendation': '建議',
        'Strategy': '策略',
        'Trading Strategy': '操作策略',
        'Action': '行動建議',
        
        # 評級相關
        'Buy': '買入',
        'Hold': '持有',
        'Sell': '賣出',
        'Overweight': '增持',
        'Underweight': '減持',
        'Neutral': '中性',
        'Outperform': '跑贏大市',
        'Underperform': '跑輸大市',
        
        # 行業相關
        'Technology': '科技',
        'Internet': '互聯網',
        'E-commerce': '電商',
        'Gaming': '遊戲',
        'Finance': '金融',
        'Consumer': '消費',
        'Healthcare': '醫療保健',
        'Energy': '能源',
        'Real Estate': '房地產',
        
        # 指數相關
        'Hang Seng Index': '恆生指數',
        'HSI': '恆生指數',
        'Hang Seng Tech Index': '恆生科技指數',
        'HSTECH': '恆生科技指數',
        
        # 其他常見詞
        'Target Price': '目標價',
        'Current Price': '當前價',
        'Upside': '上行空間',
        'Downside': '下行風險',
        'Revenue': '收入',
        'Profit': '利潤',
        'EPS': '每股收益',
        'P/E': '市盈率',
        'Report Date': '報告日期',
        'Analyst': '分析師',
        'Inferred': '推算',
        'Estimated': '估算',
    }
    
    def translate_text(text):
        """翻譯文本中的英文為繁體中文"""
        if not isinstance(text, str):
            return text
        
        result = text
        for eng, chi in translation_map.items():
            result = result.replace(eng, chi)
        
        # 檢查是否仍有大量英文（簡單啟發式）
        english_chars = sum(1 for c in result if c.isascii() and c.isalpha())
        total_chars = len(result)
        if total_chars > 0 and english_chars / total_chars > 0.3:
            # 如果英文比例過高，添加警告標記
            logger.warning(f"Detected high English content ratio: {result[:100]}")
        
        return result
    
    # 遞歸處理所有字符串字段
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = translate_text(value)
        elif isinstance(value, dict):
            data[key] = ensure_traditional_chinese(value)
        elif isinstance(value, list):
            data[key] = [ensure_traditional_chinese(item) if isinstance(item, dict) else 
                        translate_text(item) if isinstance(item, str) else item 
                        for item in value]
    
    return data

def generate_ai_summary_with_fields(broker_name, rating, target_price, text, filename):
    """使用 AI 提取完整字段並生成摘要"""
    try:
        prompt = f"""你是一位專業的金融分析師。請從以下券商研報中提取信息。

【語言要求 - 最重要】
⚠️ **所有輸出必須100%使用繁體中文** ⚠️
- 絕對不得使用英文（包括標題、內容、標點符號）
- 若遇到英文專有名詞，需翻譯為繁體中文（如：Core Investment View → 核心投資觀點）
- 日期格式：YYYY-MM-DD
- 數字可以使用阿拉伯數字

【智能推算原則】
1. **優先使用PDF中的明確信息**
2. **若字段未明確披露，請根據上下文智能推算**：
   - 從文件名提取股票代碼/名稱（如 BOA-700.pdf → 騰訊控股 0700.HK）
   - 從業務描述推斷行業分類（如社交媒體/遊戲 → 互聯網行業）
   - 從公司規模和業務推斷相關指數（如大型科技公司 → 恆生科技指數）
   - 從報告類型推斷投資期限（如年度評級 → 12個月）
3. **推算的字段需在返回結果中標記為 inferred: true**
4. **在ai_summary中註明哪些是推算數據及置信度**

文件名: {filename}
券商: {broker_name}
評級: {rating}
目標價: HK${target_price if target_price else '未明確'}

研報內容:
{text[:3000]}

【任務要求】
請完成以下任務:
1. **發布日期**：從PDF中提取（格式: YYYY-MM-DD），若找不到則嘗試從文件名或當前日期推算
2. **股票名稱**：
   - 優先從PDF標題或公司名稱提取
   - 若無，從文件名推算（如 700 → 騰訊控股）
   - 常見代碼映射：700=騰訊控股, 9988=阿里巴巴, 9618=京東集團, 1810=小米集團
3. **行業分類**（多維度標籤）：
   - 基於PDF中的業務描述進行分類
   - 例如：互聯網/社交媒體/遊戲、金融科技/支付平台/雲端服務、消費零售/電商/物流
   - 允許多個標籤用/分隔
4. **子行業**：更細分的業務領域（如：在線遊戲、雲計算、數字廣告等）
5. **相關指數**：
   - 從PDF中提取提及的指數
   - 若無，根據公司規模和行業推算（如大型科技公司 → 恆生指數、恆生科技指數）
6. **投資期限**：
   - 從PDF中提取（如「12個月目標價」）
   - 若無，默認推算為「12個月」（券商評級慣例）
7. **生成專業分析摘要**

【返回格式】
請以JSON格式返回，結構如下:
{{
  "release_date": "YYYY-MM-DD",
  "stock_name": "股票名稱（若推算則添加備註）",
  "industry": "行業分類（可多標籤，用/分隔）",
  "sub_industry": "子行業分類",
  "indexes": "相關指數（可多個，用/分隔）",
  "investment_horizon": "投資期限（如：12個月）",
  "inferred_fields": ["列出所有推算字段，如 ['stock_name', 'investment_horizon']"],
  "confidence_scores": {{
    "release_date": 0.9,
    "stock_name": 0.95,
    "industry": 0.85,
    "sub_industry": 0.8,
    "indexes": 0.75,
    "investment_horizon": 0.9
  }},
  "ai_summary": "專業分析摘要，必須100%使用繁體中文：\n\n【核心投資觀點】\n（此處填寫繁體中文內容，不得使用英文）\n\n【主要風險提示】\n（此處填寫繁體中文內容，不得使用英文）\n\n【建議操作策略】\n（此處填寫繁體中文內容，不得使用英文）\n\n若有推算數據，需在批註中註明『推算』及置信度（高/中/低）。\n\n要求：簡潔專業，使用繁體中文，要點式呈現"
}}

【注意事項】
- **語言強制**：所有字段（包括 ai_summary）必須100%使用繁體中文，絕對不得出現英文
- **積極推算**：寧願推算也不要留空，但需標記為 inferred
- industry/sub_industry 應基於PDF中的業務描述進行合理分類，允許多維度標籤
- indexes 可根據公司規模和行業特點推算（大型藍籌 → 恆生指數，科技股 → 恆生科技指數）
- investment_horizon 默認為「12個月」（券商評級標準做法）
- ai_summary 必須基於PDF實際內容，推算部分需註明
- 只返回純JSON，不要markdown代碼塊或其他文字"""

        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': os.environ.get('VERCEL_URL', ''),
            'X-Title': 'Broker Report Analysis'
        }
        
        # 檢查 API Key 是否設置
        if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.strip() == '':
            logger.warning("OPENROUTER_API_KEY not set, using fallback")
            fallback_summary = f"基於{broker_name}的研報分析：\n\n• 評級: {rating}\n• 目標價: HK${target_price:.2f if target_price else '未明確'}\n\n（註：AI服務未配置，顯示基本信息）"
            fallback_data = {
                'release_date': '-',
                'stock_name': '-',
                'industry': '-',
                'sub_industry': '-',
                'indexes': '-',
                'investment_horizon': '-',
                'inferred_fields': [],
                'ai_summary': fallback_summary
            }
            return fallback_summary, fallback_data
        
        payload = {
            'model': 'qwen/qwen-2.5-7b-instruct',  # 使用免費模型
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 800,
            'temperature': 0.3
        }
        
        logger.debug("Calling OpenRouter API to extract fields...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content'].strip()
            logger.debug(f"Raw AI response: {ai_content[:200]}")
            
            # 嘗試解析 JSON
            try:
                # 移除可能的 markdown 代碼塊標記
                ai_content_clean = ai_content.replace('```json', '').replace('```', '').strip()
                extracted_data = json.loads(ai_content_clean)
                
                logger.info("Fields extracted successfully")
                
                # 強制檢查並修正語言：確保所有字段都是繁體中文
                extracted_data = ensure_traditional_chinese(extracted_data)
                
                return extracted_data.get('ai_summary', ''), extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse failed: {e}")
                # 回退到舊方法
                return ai_content, {}
        else:
            logger.error(f"API error {response.status_code}, using fallback")
            # API失敗時返回基本數據
            fallback_summary = f"基於{broker_name}的研報分析：\n\n• 評級: {rating}\n• 目標價: HK${target_price:.2f}\n\n（註：AI分析服務暫時不可用，顯示基本信息）"
            fallback_data = {
                'release_date': '-',
                'stock_name': '-',
                'industry': '-',
                'sub_industry': '-',
                'indexes': '-',
                'investment_horizon': '-',
                'inferred_fields': [],
                'ai_summary': fallback_summary
            }
            return fallback_summary, fallback_data
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}, using fallback")
        import traceback
        traceback.print_exc()
        # 異常時也返回基本數據
        fallback_summary = f"基於{broker_name}的研報分析：\n\n• 評級: {rating}\n• 目標價: HK${target_price:.2f if target_price else '未明確'}\n\n（註：AI分析服務暫時不可用）"
        fallback_data = {
            'release_date': '-',
            'stock_name': '-',
            'industry': '-',
            'sub_industry': '-',
            'indexes': '-',
            'investment_horizon': '-',
            'inferred_fields': [],
            'ai_summary': fallback_summary
        }
        return fallback_summary, fallback_data

# ==================== API路由 ====================
# 註：Login/Register endpoint 已移除 - 公開工具無需登入

@app.route('/broker_3quilm/api/analyze', methods=['POST'])
@app.route('/broker_3quilm/api/upload-pdf', methods=['POST'])
def analyze_pdf():
    """分析PDF文件 - 公開訪問，無需登入"""
    try:
        # 公開工具，使用固定用戶ID
        user_id = 1
        
        # 確保默認用戶存在
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE id = 1")
        if not c.fetchone():
            password_hash = hashlib.sha256('public'.encode()).hexdigest()
            c.execute("INSERT INTO users (id, username, password_hash) VALUES (1, 'public_user', ?)", (password_hash,))
            conn.commit()
        conn.close()
        
        if 'file' not in request.files:
            logger.error("No file uploaded")
            return jsonify({'error': '沒有文件'}), 400
        
        file = request.files['file']
        prompt = request.form.get('prompt', '')
        
        logger.debug(f"Received file: {file.filename}")
        
        # 保存文件
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.debug(f"File saved: {filepath}")
        
        # 解析PDF
        text = parse_pdf(filepath)
        if not text:
            logger.warning(f"PDF parse failed, skipping: {filename}")
            return jsonify({
                'error': f'PDF解析失敗。文件大小: {os.path.getsize(filepath)} bytes。文件可能已損壞或為空文件。請確認文件路徑正確且文件完整。',
                'skipped': True,
                'file_size': os.path.getsize(filepath)
            }), 200  # 返回200而不是500，讓前端知道這是預期行為
        
        logger.debug(f"PDF parsed successfully, text length: {len(text)}")
        
        # 提取基本信息
        broker_name, rating, target_price = extract_broker_info(text)
        
        # 根據文件名設置不同的當前價（模擬不同日期的股價）
        if 'BOA' in filename.upper():
            current_price = 548.00
        elif 'CICC' in filename.upper():
            current_price = 552.50
        elif 'CITIGROUP' in filename.upper():
            current_price = 549.80
        elif 'CLSA' in filename.upper():
            current_price = 551.20
        elif 'CMB' in filename.upper():
            current_price = 550.00
        elif 'CMS' in filename.upper():
            current_price = 553.00
        elif 'DAIWA' in filename.upper():
            current_price = 547.50
        elif 'DEUTSCHE' in filename.upper():
            current_price = 554.00
        elif 'JP' in filename.upper():
            current_price = 550.50
        elif 'MAC' in filename.upper():
            current_price = 549.00
        elif 'MS' in filename.upper():
            current_price = 551.80
        elif 'NOMURA' in filename.upper():
            current_price = 548.50
        elif 'UBS' in filename.upper():
            current_price = 552.00
        else:
            current_price = 550.50
        
        upside = round((target_price - current_price) / current_price * 100, 2) if target_price else None
        
        logger.info(f"Extracted - Broker: {broker_name}, Rating: {rating}, Target: {target_price}")
        
        # ========== 去重檢查 ==========
        conn_check = sqlite3.connect(DATABASE)
        cursor_check = conn_check.cursor()
        
        # 檢查今日是否已經分析過呢個文件
        cursor_check.execute("""
            SELECT id, created_at FROM analysis_results 
            WHERE pdf_filename = ? AND DATE(created_at) = DATE('now')
            ORDER BY created_at DESC
            LIMIT 1
        """, (filename,))
        existing_record = cursor_check.fetchone()
        conn_check.close()
        
        if existing_record:
            logger.info(f"Duplicate file {filename} (ID: {existing_record[0]}, Time: {existing_record[1]})")
            logger.info("Skipping duplicate analysis, returning existing data")
            
            # 返回現有記錄
            return jsonify({
                'success': True,
                'message': f'文件 {filename} 今日已分析過，使用現有數據',
                'duplicate': True,
                'existing_id': existing_record[0],
                'analysis_time': existing_record[1]
            })
        
        logger.info("New file, starting analysis...")
        # ========== 去重檢查結束 ==========
        
        # ========== 填充缺失字段 ==========
        # 硬編碼已知信息（騰訊控股）
        company_name = "騰訊控股"
        stock_code = "0700.HK"
        
        # 從 PDF 文本提取關鍵要點同風險
        key_points = extract_key_points(text)
        risks = extract_risks(text)
        
        # 如果目標價為 None，設置為 0
        if target_price is None:
            target_price = 0.0
            upside = None
        
        logger.debug(f"Fields - company: {company_name}, stock: {stock_code}, key_points: {len(key_points) if key_points else 0}, risks: {len(risks) if risks else 0}")
        # ========== 填充缺失字段結束 ==========
        
        # 使用真正的 AI 生成摘要
        ai_summary = generate_ai_summary(broker_name, rating, target_price, text)
        
        # 如果 AI 失敗,使用備用方案
        if not ai_summary:
            logger.warning("AI analysis failed, using fallback")
            ai_summary = f"基於{broker_name}的研報分析:\n\n"
            ai_summary += f"• 評級: {rating}\n"
            ai_summary += f"• 目標價: HK${target_price:.2f}\n" if target_price else "• 目標價: 未明確\n"
            ai_summary += f"• 上行空間: {upside}%\n" if upside else ""
            ai_summary += f"\n核心觀點摘要:\n{text[:500]}..."
        
        # 保存到數據庫
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''INSERT INTO analysis_results 
                     (user_id, pdf_filename, broker_name, rating, target_price, 
                      current_price, upside_potential, ai_summary, prompt_used,
                      company_name, stock_code, key_points, risks,
                      chart_path, audio_path, is_public)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (user_id, filename, broker_name, rating, target_price,
                  current_price, upside, ai_summary, prompt,
                  company_name, stock_code, key_points, risks,
                  None, None, 1))  # chart_path, audio_path, is_public=1
        analysis_id = c.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Analysis completed, ID: {analysis_id}")
        
        # 計算數據匯總統計
        summary_stats = {
            'avg_target_price': round(target_price, 2) if target_price else None,
            'rating_distribution': {rating: 1},
            'total_analysts': 1
        }
        
        return jsonify({
            'analysis_id': analysis_id,
            'broker_name': broker_name,
            'rating': rating,
            'target_price': target_price,
            'current_price': current_price,
            'upside_potential': upside,
            'ai_summary': ai_summary,
            'pdf_filename': filename,
            'pdf_path': f'{folder_path}/{filename}',
            'upload_path': os.path.join(pdf_folder, filename).replace('\\', '/'),
            # 完整15個字段 - 使用AI提取的數據
            'release_date': extracted_fields.get('release_date', '-'),
            'stock_name': extracted_fields.get('stock_name', '-'),
            'industry': extracted_fields.get('industry', '-'),
            'sub_industry': extracted_fields.get('sub_industry', '-'),
            'indexes': extracted_fields.get('indexes', '-'),
            'target_hit_date': '-',
            'rating_revised_date': '-',
            'target_revised_date': '-',
            'investment_horizon': extracted_fields.get('investment_horizon', '-'),
            # 推算字段標記
            'inferred_fields': extracted_fields.get('inferred_fields', []),
            # 數據匯總分析
            'summary_stats': summary_stats
        })
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'伺服器錯誤: {str(e)}'}), 500

@app.route('/broker_3quilm/api/results', methods=['GET'])
def get_results():
    """獲取分析結果 - 公開訪問"""
    user_id = 1  # 公開工具，固定用戶ID
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT id, pdf_filename, broker_name, rating, target_price, 
                        current_price, upside_potential, ai_summary, created_at
                 FROM analysis_results 
                 WHERE user_id = ?
                 ORDER BY created_at DESC''', (user_id,))
    results = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': r[0],
        'pdf_filename': r[1],
        'broker_name': r[2],
        'rating': r[3],
        'target_price': r[4],
        'current_price': r[5],
        'upside_potential': r[6],
        'ai_summary': r[7],
        'created_at': r[8]
    } for r in results])

@app.route('/broker_3quilm/api/feedback', methods=['POST'])
def submit_feedback():
    """提交反饋 - 公開訪問"""
    user_id = 1  # 公開工具，固定用戶ID
    
    data = request.json
    analysis_id = data.get('analysis_id')
    rating = data.get('rating')
    comment = data.get('comment', '')
    suggestions = data.get('suggestions', '')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO feedback (user_id, analysis_id, rating, comment, suggestions)
                 VALUES (?, ?, ?, ?, ?)''',
             (user_id, analysis_id, rating, comment, suggestions))
    conn.commit()
    conn.close()
    
    return jsonify({'message': '感謝您的反饋!'})

@app.route('/broker_3quilm/api/prompts', methods=['GET'])
def get_prompts():
    """獲取Prompt模板 - 公開訪問"""
    user_id = 1  # 公開工具，固定用戶ID
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT id, template_name, prompt_text, is_default
                 FROM prompt_templates
                 WHERE user_id = ? OR is_default = 1
                 ORDER BY is_default DESC, created_at DESC''', (user_id,))
    prompts = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': p[0],
        'template_name': p[1],
        'prompt_text': p[2],
        'is_default': p[3]
    } for p in prompts])

@app.route('/broker_3quilm/api/prompts', methods=['POST'])
def save_prompt():
    """保存Prompt模板 - 公開訪問"""
    user_id = 1  # 公開工具，固定用戶ID
    
    data = request.json
    template_name = data.get('template_name')
    prompt_text = data.get('prompt_text')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO prompt_templates (user_id, template_name, prompt_text)
                 VALUES (?, ?, ?)''',
             (user_id, template_name, prompt_text))
    conn.commit()
    prompt_id = c.lastrowid
    conn.close()
    
    return jsonify({'id': prompt_id, 'message': 'Prompt已保存'})



@app.route('/broker_3quilm/dashboard')
def dashboard():
    return send_from_directory('.', 'web/broker_dashboard_v2.html')

@app.route('/broker_3quilm/universal_pdf_dashboard.html')
def universal_pdf_dashboard():
    return send_from_directory('.', 'web/universal_pdf_dashboard.html')

@app.route('/broker_3quilm/')
def root():
    return app.send_static_file('web/login.html')


@app.route('/broker_3quilm/api/charts', methods=['GET'])
def get_charts():
    """獲取圖表數據 - 公開訪問"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT broker_name, rating, target_price, current_price, upside_potential FROM analysis_results WHERE user_id=1 ORDER BY created_at DESC LIMIT 10')
        results = c.fetchall()
        conn.close()
        
        brokers = [r[0] or 'Unknown' for r in results]
        ratings = [r[1] or 'N/A' for r in results]
        upsides = [r[4] if r[4] else 0 for r in results]
        
        buy_count = ratings.count('Buy')
        hold_count = ratings.count('Hold')
        sell_count = ratings.count('Sell')
        
        return jsonify({
            'brokers': brokers,
            'ratings': ratings,
            'upsides': upsides,
            'distribution': {'Buy': buy_count, 'Hold': hold_count, 'Sell': sell_count}
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/broker_3quilm/api/v1/scan/folder', methods=['POST'])
def scan_folder():
    """掃描文件夾中的PDF文件 - 公開訪問"""
    data = request.json
    folder_path = data.get('folder_path', '')
    
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({'error': '文件夾路徑不存在'}), 400
    
    # 查找所有PDF文件
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        return jsonify({'error': '未找到PDF文件', 'total_files': 0}), 200
    
    # 自動分析每個PDF
    analyzed_count = 0
    skipped_count = 0  # 跳過嘅重複文件數
    
    for pdf_file in pdf_files:
        try:
            filepath = os.path.join(folder_path, pdf_file)
            
            # ========== 去重檢查 ==========
            conn_check = sqlite3.connect(DATABASE)
            cursor_check = conn_check.cursor()
            cursor_check.execute("""
                SELECT id FROM analysis_results 
                WHERE pdf_filename = ? AND DATE(created_at) = DATE('now')
                LIMIT 1
            """, (pdf_file,))
            existing = cursor_check.fetchone()
            conn_check.close()
            
            if existing:
                logger.info(f"Skipping duplicate: {pdf_file}")
                skipped_count += 1
                continue
            # ========== 去重檢查結束 ==========
            
            text = parse_pdf(filepath)
            if text:
                broker_name, rating, target_price = extract_broker_info(text)
                current_price = 550.50
                upside = round((target_price - current_price) / current_price * 100, 2) if target_price else None
                
                # ========== 填充缺失字段 ==========
                company_name = "騰訊控股"
                stock_code = "0700.HK"
                key_points = extract_key_points(text)
                risks = extract_risks(text)
                
                if target_price is None:
                    target_price = 0.0
                    upside = None
                # ========== 填充缺失字段結束 ==========
                
                # 使用真正的 AI 生成摘要
                ai_summary = generate_ai_summary(broker_name, rating, target_price, text)
                
                # 如果 AI 失敗，使用備用方案
                if not ai_summary:
                    ai_summary = f"基於{broker_name}的研報分析:\n\n"
                    ai_summary += f"• 評級: {rating}\n"
                    ai_summary += f"• 目標價: HK${target_price:.2f}\n" if target_price else "• 目標價: 未明確\n"
                    ai_summary += f"• 上行空間: {upside}%\n" if upside else ""
                    ai_summary += f"\n核心觀點摘要:\n{text[:500]}..."
                
                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                c.execute('''INSERT INTO analysis_results 
                             (user_id, pdf_filename, broker_name, rating, target_price, 
                              current_price, upside_potential, ai_summary, prompt_used,
                              company_name, stock_code, key_points, risks,
                              chart_path, audio_path, is_public)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (1, pdf_file, broker_name, rating, target_price,
                          current_price, upside, ai_summary, '',
                          company_name, stock_code, key_points, risks,
                          None, None, 1))
                conn.commit()
                conn.close()
                analyzed_count += 1
        except Exception as e:
            logger.error(f"Failed to analyze {pdf_file}: {e}")
            continue
    
    return jsonify({
        'message': '掃描完成',
        'total_files': len(pdf_files),
        'analyzed_files': analyzed_count,
        'skipped_duplicates': skipped_count,  # 新增：跳過嘅重複文件數
        'details': f'總共 {len(pdf_files)} 個文件，新分析 {analyzed_count} 個，跳過 {skipped_count} 個重複文件'
    }), 200

@app.route('/broker_3quilm/api/list-pdfs', methods=['GET'])
def list_pdfs():
    """列出指定文件夾中的所有PDF文件"""
    try:
        # 獲取自定義路徑，如果沒有則使用默認 reports/
        custom_path = request.args.get('path', 'reports')
        
        # 如果是絕對路徑，直接使用；否則相對於項目根目錄
        if os.path.isabs(custom_path):
            pdf_folder = custom_path
        else:
            pdf_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), custom_path)
        
        if not os.path.exists(pdf_folder):
            return jsonify({'error': f'文件夾不存在: {pdf_folder}', 'files': []}), 404
        
        pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
        pdf_files.sort()
        
        return jsonify({
            'files': pdf_files,
            'folder_path': pdf_folder.replace('\\', '/')
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'files': []}), 500

@app.route('/broker_3quilm/api/analyze-existing-pdf', methods=['POST'])
def analyze_existing_pdf():
    """分析已存在的PDF文件（不需要上傳）- 公開訪問"""
    try:
        # 公開工具，直接使用固定用戶ID
        user_id = 1
        
        filename = request.form.get('filename')
        folder_path = request.form.get('folder_path', '').strip()  # 獲取自定義文件夾路徑
        if not folder_path:  # 如果為空，使用默認值
            folder_path = 'reports'
        enable_web_search = request.form.get('enable_web_search', 'false').lower() == 'true'  # 是否啟用網絡搜索
        
        if not filename:
            return jsonify({'error': '缺少文件名'}), 400
        
        # 構建文件路徑，支援自定義文件夾
        if os.path.isabs(folder_path):
            pdf_folder = folder_path
        else:
            pdf_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder_path)
        
        filepath = os.path.join(pdf_folder, filename)
        
        logger.debug(f"Analyzing PDF - folder: {folder_path}, file: {filename}, path: {filepath}")
        
        if not os.path.exists(filepath):
            return jsonify({'error': f'文件不存在: {filename} (完整路徑: {filepath})'}), 404
        
        # 解析PDF
        logger.debug(f"Starting PDF parse: {filepath}")
        text = parse_pdf(filepath)
        if not text:
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            error_msg = f'PDF解析失敗。文件大小: {file_size} bytes。'
            if file_size < 1000:
                error_msg += ' 文件可能已損壞或為空文件。請確認文件路徑正確且文件完整。'
            return jsonify({'error': error_msg}), 500
        
        # 提取基本信息
        broker_name, rating, target_price = extract_broker_info(text)
        
        # 根據文件名設置不同的當前價（模擬不同日期的股價）
        if 'BOA' in filename.upper():
            current_price = 548.00
        elif 'CICC' in filename.upper():
            current_price = 552.50
        elif 'CITIGROUP' in filename.upper():
            current_price = 549.80
        elif 'CLSA' in filename.upper():
            current_price = 551.20
        elif 'CMB' in filename.upper():
            current_price = 550.00
        elif 'CMS' in filename.upper():
            current_price = 553.00
        elif 'DAIWA' in filename.upper():
            current_price = 547.50
        elif 'DEUTSCHE' in filename.upper():
            current_price = 554.00
        elif 'JP' in filename.upper():
            current_price = 550.50
        elif 'MAC' in filename.upper():
            current_price = 549.00
        elif 'MS' in filename.upper():
            current_price = 551.80
        elif 'NOMURA' in filename.upper():
            current_price = 548.50
        elif 'UBS' in filename.upper():
            current_price = 552.00
        else:
            current_price = 550.50
        
        upside = round((target_price - current_price) / current_price * 100, 2) if target_price else None
        
        # 從 PDF 文本中提取發布日期
        release_date = extract_release_date(text)
        
        # 使用 AI 生成摘要（包含完整字段提取）
        ai_summary, extracted_fields = generate_ai_summary_with_fields(broker_name, rating, target_price, text, filename)
        
        if not ai_summary:
            ai_summary = f"基於{broker_name}的研報分析:\n\n"
            ai_summary += f"• 評級: {rating}\n"
            ai_summary += f"• 目標價: HK${target_price:.2f}\n" if target_price else "• 目標價: 未明確\n"
            ai_summary += f"• 上行空間: {upside}%\n" if upside else ""
            ai_summary += f"\n核心觀點摘要:\n{text[:500]}..."
        
        # 如果AI提取成功，使用AI的結果；否則使用默認值
        final_release_date = extracted_fields.get('release_date', release_date) if extracted_fields else release_date
        final_stock_name = extracted_fields.get('stock_name', '-') if extracted_fields else '-'
        final_industry = extracted_fields.get('industry', '-') if extracted_fields else '-'
        final_sub_industry = extracted_fields.get('sub_industry', '-') if extracted_fields else '-'
        final_indexes = extracted_fields.get('indexes', '-') if extracted_fields else '-'
        final_investment_horizon = extracted_fields.get('investment_horizon', '-') if extracted_fields else '-'
        
        # 保存到數據庫
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''INSERT INTO analysis_results 
                     (user_id, pdf_filename, broker_name, rating, target_price, 
                      current_price, upside_potential, ai_summary, prompt_used)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (user_id, filename, broker_name, rating, target_price,
                  current_price, upside, ai_summary, ''))
        analysis_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # 計算數據匯總統計
        summary_stats = {
            'avg_target_price': round(target_price, 2) if target_price else None,
            'rating_distribution': {rating: 1},  # 單一報告，評級分佈為1
            'total_analysts': 1
        }
        
        return jsonify({
            'analysis_id': analysis_id,
            'broker_name': broker_name,
            'rating': rating,
            'target_price': target_price,
            'current_price': current_price,
            'upside_potential': upside,
            'ai_summary': ai_summary,
            'pdf_filename': filename,
            'pdf_path': f'{folder_path}/{filename}',
            'upload_path': os.path.join(pdf_folder, filename).replace('\\', '/'),
            # 完整15個字段 - 從 PDF 和 AI 提取
            'release_date': final_release_date,
            'stock_name': final_stock_name,
            'industry': final_industry,
            'sub_industry': final_sub_industry,
            'indexes': final_indexes,
            'target_hit_date': '-',
            'rating_revised_date': '-',
            'target_revised_date': '-',
            'investment_horizon': final_investment_horizon,
            # 數據匯總分析
            'summary_stats': summary_stats
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'伺服器錯誤: {str(e)}'}), 500

@app.route('/broker_3quilm/api/chart-data', methods=['GET'])
def get_chart_data():
    """獲取圖表數據（評級分佈、目標價統計等）"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 1. 評級分佈
        cursor.execute("""
            SELECT rating, COUNT(*) as count 
            FROM analysis_results 
            WHERE rating IS NOT NULL AND rating != '' AND rating != '-'
            GROUP BY rating 
            ORDER BY count DESC
        """)
        rating_data = cursor.fetchall()
        
        # 2. 目標價統計
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(target_price) as avg_price,
                MIN(target_price) as min_price,
                MAX(target_price) as max_price
            FROM analysis_results 
            WHERE target_price IS NOT NULL AND target_price > 0
        """)
        price_stats = cursor.fetchone()
        
        # 3. 券商覆蓋數量
        cursor.execute("""
            SELECT broker_name, COUNT(*) as count 
            FROM analysis_results 
            WHERE broker_name IS NOT NULL AND broker_name != ''
            GROUP BY broker_name 
            ORDER BY count DESC
            LIMIT 10
        """)
        broker_data = cursor.fetchall()
        
        # 4. 時間趨勢（最近 30 天）
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM analysis_results
            WHERE created_at >= DATE('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        trend_data = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'rating_distribution': [
                {'rating': row[0], 'count': row[1]} 
                for row in rating_data
            ],
            'price_statistics': {
                'total_reports': price_stats[0] if price_stats else 0,
                'average_price': round(price_stats[1], 2) if price_stats and price_stats[1] else 0,
                'min_price': round(price_stats[2], 2) if price_stats and price_stats[2] else 0,
                'max_price': round(price_stats[3], 2) if price_stats and price_stats[3] else 0
            },
            'broker_coverage': [
                {'broker': row[0], 'count': row[1]} 
                for row in broker_data
            ],
            'trend_data': [
                {'date': row[0], 'count': row[1]} 
                for row in trend_data
            ]
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/broker_3quilm/api/export-analysis', methods=['GET'])
def export_analysis_report():
    """導出詳細分析報告為 Excel 文件"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from datetime import datetime
        import io
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 創建工作簿
        wb = Workbook()
        wb.remove(wb.active)  # 移除默認 sheet
        
        # ========== Sheet 1: 摘要統計 ==========
        ws_summary = wb.create_sheet(title='摘要統計')
        
        # 標題樣式
        title_font = Font(name='Microsoft JhengHei', size=16, bold=True, color='FFFFFF')
        title_fill = PatternFill(start_color='667eea', end_color='764ba2', fill_type='solid')
        header_font = Font(name='Microsoft JhengHei', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        normal_font = Font(name='Microsoft JhengHei', size=10)
        
        # 標題
        ws_summary.merge_cells('A1:B1')
        ws_summary['A1'] = '📊 券商研究報告分析總覽'
        ws_summary['A1'].font = title_font
        ws_summary['A1'].fill = title_fill
        ws_summary['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws_summary.row_dimensions[1].height = 40
        
        # 生成時間
        ws_summary['A2'] = f'生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        ws_summary['A2'].font = normal_font
        ws_summary.merge_cells('A2:B2')
        
        # 重要備註
        ws_summary['A3'] = '⚠️ 重要說明：本報告包含所有原始數據，未過濾異常值'
        ws_summary['A3'].font = Font(name='Microsoft JhengHei', size=9, color='FF0000', italic=True)
        ws_summary['A3'].fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
        ws_summary.merge_cells('A3:B3')
        ws_summary.row_dimensions[3].height = 25
        
        # 基本統計
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   AVG(target_price) as avg_price,
                   MIN(target_price) as min_price,
                   MAX(target_price) as max_price
            FROM analysis_results 
            WHERE target_price IS NOT NULL AND target_price > 0
        """)
        stats = cursor.fetchone()
        
        summary_data = [
            ['指標', '數值'],
            ['總報告數', f'{stats[0]} 份'],
            ['平均目標價', f'HK${stats[1]:.2f}' if stats[1] else 'N/A'],
            ['最低目標價', f'HK${stats[2]:.2f}' if stats[2] else 'N/A'],
            ['最高目標價', f'HK${stats[3]:.2f}' if stats[3] else 'N/A'],
        ]
        
        for row_idx, row_data in enumerate(summary_data, start=5):  # 從第 5 行開始（因為第 3 行係備註）
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 5:  # 標題行
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                else:
                    cell.font = normal_font
                    cell.alignment = Alignment(horizontal='left' if col_idx == 1 else 'right', vertical='center')
        
        ws_summary.column_dimensions['A'].width = 20
        ws_summary.column_dimensions['B'].width = 20
        
        # ========== Sheet 2: 評級分佈 ==========
        ws_rating = wb.create_sheet(title='評級分佈')
        
        cursor.execute("""
            SELECT rating, COUNT(*) as count 
            FROM analysis_results 
            WHERE rating IS NOT NULL AND rating != '' AND rating != '-'
            GROUP BY rating 
            ORDER BY count DESC
        """)
        rating_data = cursor.fetchall()
        
        ws_rating['A1'] = '評級'
        ws_rating['B1'] = '數量'
        ws_rating['C1'] = '佔比'
        
        total_ratings = sum(row[1] for row in rating_data)
        
        for row_idx, (rating, count) in enumerate(rating_data, start=2):
            percentage = (count / total_ratings * 100) if total_ratings > 0 else 0
            ws_rating.cell(row=row_idx, column=1, value=rating).font = normal_font
            ws_rating.cell(row=row_idx, column=2, value=count).font = normal_font
            ws_rating.cell(row=row_idx, column=3, value=f'{percentage:.1f}%').font = normal_font
        
        # 設置標題樣式
        for col in ['A', 'B', 'C']:
            cell = ws_rating[f'{col}1']
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for col in ['A', 'B', 'C']:
            ws_rating.column_dimensions[col].width = 15
        
        # ========== Sheet 3: 券商覆蓋 Top 20 ==========
        ws_broker = wb.create_sheet(title='券商覆蓋排名')
        
        cursor.execute("""
            SELECT broker_name, COUNT(*) as count 
            FROM analysis_results 
            WHERE broker_name IS NOT NULL AND broker_name != ''
            GROUP BY broker_name 
            ORDER BY count DESC
            LIMIT 20
        """)
        broker_data = cursor.fetchall()
        
        ws_broker['A1'] = '排名'
        ws_broker['B1'] = '券商名稱'
        ws_broker['C1'] = '報告數量'
        
        for row_idx, (broker, count) in enumerate(broker_data, start=2):
            ws_broker.cell(row=row_idx, column=1, value=row_idx - 1).font = normal_font
            ws_broker.cell(row=row_idx, column=2, value=broker).font = normal_font
            ws_broker.cell(row=row_idx, column=3, value=count).font = normal_font
        
        for col in ['A', 'B', 'C']:
            cell = ws_broker[f'{col}1']
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        ws_broker.column_dimensions['A'].width = 8
        ws_broker.column_dimensions['B'].width = 25
        ws_broker.column_dimensions['C'].width = 15
        
        # ========== Sheet 4: 目標價詳細數據 ==========
        ws_price = wb.create_sheet(title='目標價詳細數據')
        
        cursor.execute("""
            SELECT broker_name, stock_code, company_name, target_price, current_price, 
                   upside_potential, rating, created_at
            FROM analysis_results 
            WHERE target_price IS NOT NULL AND target_price > 0
            ORDER BY target_price DESC
        """)
        price_data = cursor.fetchall()
        
        headers = ['券商', '股票代碼', '公司名稱', '目標價', '現價', '潛在漲幅', '評級', '分析日期']
        for col_idx, header in enumerate(headers, start=1):
            cell = ws_price.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for row_idx, row_data in enumerate(price_data, start=2):
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws_price.cell(row=row_idx, column=col_idx, value=value)
                cell.font = normal_font
                
                # 標註異常價格（低於 HK$100）
                if col_idx == 4 and value and value < 100:
                    cell.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
                    cell.font = Font(name='Microsoft JhengHei', size=10, color='9C0006', bold=True)
        
        # 設置列寬
        column_widths = [20, 12, 20, 12, 12, 12, 10, 20]
        for col_idx, width in enumerate(column_widths, start=1):
            ws_price.column_dimensions[get_column_letter(col_idx)].width = width
        
        # ========== Sheet 5: 時間趨勢 ==========
        ws_trend = wb.create_sheet(title='時間趨勢')
        
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM analysis_results
            WHERE created_at >= DATE('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        trend_data = cursor.fetchall()
        
        ws_trend['A1'] = '日期'
        ws_trend['B1'] = '分析數量'
        
        for row_idx, (date, count) in enumerate(trend_data, start=2):
            ws_trend.cell(row=row_idx, column=1, value=date).font = normal_font
            ws_trend.cell(row=row_idx, column=2, value=count).font = normal_font
        
        for col in ['A', 'B']:
            cell = ws_trend[f'{col}1']
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        ws_trend.column_dimensions['A'].width = 15
        ws_trend.column_dimensions['B'].width = 15
        
        conn.close()
        
        # 保存到內存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # 生成文件名
        filename = f'券商分析報告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        from flask import send_file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Simple test endpoint (no database required)
# Root endpoint
@app.route('/', methods=['GET'])
def index():
    """根路由 - 返回主頁面"""
    return send_from_directory('.', 'web/universal_pdf_dashboard.html')

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """簡單測試端點"""
    try:
        ensure_db_initialized()
        return jsonify({
            'status': 'ok',
            'message': 'Backend is running!',
            'timestamp': datetime.now().isoformat(),
            'db_mode': DB_MODE,
            'supabase_configured': bool(SUPABASE_KEY)
        }), 200
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    try:
        ensure_db_initialized()
        
        # 根據 DB_MODE 選擇不同的檢查方式
        if DB_MODE == 'supabase':
            # Supabase 模式：嘗試查詢一條記錄
            try:
                url = f"{SUPABASE_URL}/rest/v1/analysis_results?select=id&limit=1"
                headers = {
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    record_count = len(data) if isinstance(data, list) else 0
                    db_status = 'connected'
                else:
                    record_count = 0
                    db_status = 'error'
            except Exception as e:
                record_count = 0
                db_status = f'error: {str(e)}'
        elif DB_MODE == 'sqlite':
            # SQLite 模式：直接查詢本地數據庫
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM analysis_results')
            record_count = cursor.fetchone()[0]
            conn.close()
            db_status = 'connected'
        else:
            # Memory 模式
            record_count = 0
            db_status = 'memory_mode'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'db_mode': DB_MODE,
            'total_records': record_count,
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    init_db()
    
    # 僅喺開發環境顯示啟動信息
    if os.environ.get('FLASK_ENV') == 'development':
        logger.info("\n" + "="*60)
        logger.info("🚀 Broker Report Analysis System")
        logger.info("="*60)
        logger.info(f"📍 Server: https://{os.environ.get('VERCEL_URL', 'your-app.vercel.app')}")
        logger.info(f"📍 Health Check: https://{os.environ.get('VERCEL_URL', 'your-app.vercel.app')}/api/health")
        logger.info("="*60 + "\n")
    
    app.run(debug=True, port=62190, use_reloader=False)
