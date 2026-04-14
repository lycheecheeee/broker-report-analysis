from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
import json
import os
from datetime import datetime
import jwt
import PyPDF2
import re
import requests

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大上傳 50MB

# 添加請求日誌中間件
@app.before_request
def log_request():
    print(f"\n[REQUEST] {request.method} {request.path}")
    if request.form:
        print(f"[REQUEST FORM] {dict(request.form)}")


# 配置
SECRET_KEY = 'tencent-broker-analysis-secret-key-2026'
DATABASE = 'broker_analysis.db'
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '700')
OPENROUTER_API_KEY = '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'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# 確保上傳文件夾存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
            print(f"✅ 已添加 {col_name} 字段")
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

def hash_password(password):
    """密碼哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id):
    """生成JWT token"""
    from datetime import timezone
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc).timestamp() + 86400  # 24小時過期
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """驗證JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

def token_required(f):
    """Token驗證裝飾器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token is invalid'}), 401
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT id, username FROM users WHERE id=?', (user_id,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        current_user = {'id': user[0], 'username': user[1]}
        return f(current_user, *args, **kwargs)
    return decorated

def parse_pdf(pdf_path):
    """解析PDF文件"""
    try:
        print(f"[PDF PARSE] 開始解析: {pdf_path}")
        file_size = os.path.getsize(pdf_path)
        print(f"[PDF PARSE] 文件大小: {file_size} bytes")
        
        # 檢查文件大小，如果太小則跳過
        if file_size < 1000:
            print(f"[PDF PARSE WARNING] 文件太小 ({file_size} bytes)，可能是損壞文件")
            return None
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file, strict=False)  # 設置strict=False以容忍一些錯誤
            print(f"[PDF PARSE] PDF頁數: {len(pdf_reader.pages)}")
            
            text = ''
            for i, page in enumerate(pdf_reader.pages[:5]):  # 只讀前5頁
                try:
                    page_text = page.extract_text()
                    if page_text:
                        print(f"[PDF PARSE] 第{i+1}頁提取成功，長度: {len(page_text)}")
                        text += page_text + '\n'
                    else:
                        print(f"[PDF PARSE] 第{i+1}頁無文本內容")
                except Exception as page_error:
                    print(f"[PDF PARSE] 第{i+1}頁提取失敗: {page_error}")
                    continue
            
            print(f"[PDF PARSE] 總文本長度: {len(text)}")
            return text if text.strip() else None
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[PDF PARSE ERROR] {e}")
        print(f"[PDF PARSE ERROR DETAIL]\n{error_detail}")
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
            print(f"[DATE EXTRACT] 找到日期字符串: {date_str}")
            
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
                print(f"[DATE EXTRACT] 解析失敗: {e}")
                continue
    
    print("[DATE EXTRACT] 未找到有效日期")
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
            'HTTP-Referer': 'http://localhost:62190',
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
        
        print(f"[AI] 正在調用 OpenRouter API...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            print(f"[AI] 成功生成摘要")
            return ai_content.strip()
        else:
            print(f"[AI] API 錯誤: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[AI] 分析失敗: {str(e)}")
        return None

def generate_ai_summary_with_fields(broker_name, rating, target_price, text, filename):
    """使用 AI 提取完整字段並生成摘要"""
    try:
        prompt = f"""你是一位專業的金融分析師。請從以下券商研報中提取信息並生成摘要。

文件名: {filename}
券商: {broker_name}
評級: {rating}
目標價: HK${target_price if target_price else '未明確'}

研報內容:
{text[:3000]}

請完成以下任務:
1. 提取發布日期（格式: YYYY-MM-DD，如果找不到則返回 '-'）
2. 提取股票名稱（例如：騰訊控股、阿里巴巴等）
3. 提取行業（例如：互聯網、科技、金融等）
4. 提取子行業（例如：社交媒體、電子商務、遊戲等）
5. 提取指數成分（例如：恒生指數、恆生科技指數等）
6. 提取投資期限（例如：12個月、6個月等）
7. 生成簡潔的AI分析摘要（包含核心觀點、風險提示、操作策略）

請以JSON格式返回，結構如下:
{{
  "release_date": "YYYY-MM-DD 或 -",
  "stock_name": "股票名稱，盡量從PDF中提取",
  "industry": "行業分類",
  "sub_industry": "子行業分類",
  "indexes": "相關指數",
  "investment_horizon": "投資期限",
  "ai_summary": "你的分析摘要文本，用繁體中文，包含核心觀點、風險、策略"
}}

重要提醒：
- 請仔細閱讀PDF內容，盡可能提取所有字段
- 如果某字段真的找不到，才使用 '-'
- stock_name 通常是報告標題或公司名稱
- industry/sub_industry 可以從業務描述中推斷
- indexes 通常會在報告開頭提到
- investment_horizon 可能在目標價說明中提到
- ai_summary 要用繁體中文，簡潔專業
- 只返回JSON，不要其他文字"""

        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost:62190',
            'X-Title': 'Broker Report Analysis'
        }
        
        payload = {
            'model': 'qwen/qwen-2.5-72b-instruct',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 800,
            'temperature': 0.3
        }
        
        print(f"[AI FIELDS] 正在調用 OpenRouter API 提取字段...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content'].strip()
            print(f"[AI FIELDS] 原始返回: {ai_content[:200]}")
            
            # 嘗試解析 JSON
            try:
                # 移除可能的 markdown 代碼塊標記
                ai_content_clean = ai_content.replace('```json', '').replace('```', '').strip()
                extracted_data = json.loads(ai_content_clean)
                
                print(f"[AI FIELDS] 成功提取字段")
                return extracted_data.get('ai_summary', ''), extracted_data
            except json.JSONDecodeError as e:
                print(f"[AI FIELDS] JSON解析失敗: {e}")
                # 回退到舊方法
                return ai_content, {}
        else:
            print(f"[AI FIELDS] API 錯誤: {response.status_code}")
            return None, {}
    except Exception as e:
        print(f"[AI FIELDS] 分析失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, {}

# ==================== API路由 ====================

@app.route('/broker_3quilm/api/register', methods=['POST'])
def register():
    """用戶註冊"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    
    if not username or not password:
        return jsonify({'error': '用戶名和密碼不能為空'}), 400
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                 (username, hash_password(password), email))
        conn.commit()
        user_id = c.lastrowid
        token = generate_token(user_id)
        return jsonify({
            'message': '註冊成功',
            'token': token,
            'user_id': user_id
        })
    except sqlite3.IntegrityError:
        return jsonify({'error': '用戶名已存在'}), 409
    finally:
        conn.close()

@app.route('/broker_3quilm/api/login', methods=['POST'])
def login():
    """用戶登入"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user and user[1] == hash_password(password):
        token = generate_token(user[0])
        return jsonify({
            'message': '登入成功',
            'token': token,
            'user_id': user[0]
        })
    else:
        return jsonify({'error': '用戶名或密碼錯誤'}), 401

@app.route('/broker_3quilm/api/analyze', methods=['POST'])
@app.route('/broker_3quilm/api/upload-pdf', methods=['POST'])
def analyze_pdf():
    """分析PDF文件"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # 如果是測試token或沒有token，使用默認用戶ID 1
        if not token or token == 'test-token':
            user_id = 1
            # 確保用戶ID 1存在
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE id = 1")
            if not c.fetchone():
                password_hash = hashlib.sha256('admin'.encode()).hexdigest()
                c.execute("INSERT INTO users (id, username, password_hash) VALUES (1, 'admin', ?)", (password_hash,))
                conn.commit()
            conn.close()
        else:
            user_id = verify_token(token)
        
        if not user_id:
            print("[ERROR] 未授權訪問")
            return jsonify({'error': '未授權,請先登入'}), 401
        
        if 'file' not in request.files:
            print("[ERROR] 沒有文件上傳")
            return jsonify({'error': '沒有文件'}), 400
        
        file = request.files['file']
        prompt = request.form.get('prompt', '')
        
        print(f"[UPLOAD] 收到文件: {file.filename}")
        
        # 保存文件
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        print(f"[UPLOAD] 文件已保存: {filepath}")
        
        # 解析PDF
        text = parse_pdf(filepath)
        if not text:
            print("[ERROR] PDF解析失敗")
            return jsonify({'error': 'PDF解析失敗'}), 500
        
        print(f"[PARSE] PDF解析成功,文本長度: {len(text)}")
        
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
        
        print(f"[EXTRACT] 券商:{broker_name}, 評級:{rating}, 目標價:{target_price}")
        
        # 使用真正的 AI 生成摘要
        ai_summary = generate_ai_summary(broker_name, rating, target_price, text)
        
        # 如果 AI 失敗,使用備用方案
        if not ai_summary:
            print("[WARNING] AI 分析失敗,使用備用方案")
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
                      current_price, upside_potential, ai_summary, prompt_used)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (user_id, filename, broker_name, rating, target_price,
                  current_price, upside, ai_summary, prompt))
        analysis_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"[SUCCESS] 分析完成, ID: {analysis_id}")
        
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
            # 完整15個字段 - 默認使用PDF數據，唔上網搜尋
            'release_date': datetime.now().strftime('%Y-%m-%d') if enable_web_search else '-',
            'stock_name': '騰訊控股' if enable_web_search else '-',
            'industry': '互聯網' if enable_web_search else '-',
            'sub_industry': '社交媒體/遊戲' if enable_web_search else '-',
            'indexes': '恒生指數' if enable_web_search else '-',
            'target_hit_date': '-',
            'rating_revised_date': '-',
            'target_revised_date': '-',
            'investment_horizon': '12個月' if enable_web_search else '-'
        })
    except Exception as e:
        print(f"[ERROR] 分析過程出錯: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'伺服器錯誤: {str(e)}'}), 500

@app.route('/broker_3quilm/api/results', methods=['GET'])
def get_results():
    """獲取分析結果"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    
    if not user_id:
        return jsonify({'error': '未授權'}), 401
    
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
    """提交反饋"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    
    if not user_id:
        return jsonify({'error': '未授權'}), 401
    
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
    """獲取Prompt模板"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    
    if not user_id:
        return jsonify({'error': '未授權'}), 401
    
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
    """保存Prompt模板"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    
    if not user_id:
        return jsonify({'error': '未授權'}), 401
    
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

@app.route('/broker_3quilm/')
def root():
    return app.send_static_file('web/login.html')


@app.route('/broker_3quilm/api/charts', methods=['GET'])
@token_required
def get_charts(current_user):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT broker_name, rating, target_price, current_price, upside_potential FROM analysis_results WHERE user_id=? ORDER BY created_at DESC LIMIT 10', (current_user['id'],))
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
@token_required
def scan_folder(current_user):
    """掃描文件夾中的PDF文件"""
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
    for pdf_file in pdf_files:
        try:
            filepath = os.path.join(folder_path, pdf_file)
            text = parse_pdf(filepath)
            if text:
                broker_name, rating, target_price = extract_broker_info(text)
                current_price = 550.50
                upside = round((target_price - current_price) / current_price * 100, 2) if target_price else None
                
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
                              current_price, upside_potential, ai_summary, prompt_used)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (current_user['id'], pdf_file, broker_name, rating, target_price,
                          current_price, upside, ai_summary, ''))
                conn.commit()
                conn.close()
                analyzed_count += 1
        except Exception as e:
            print(f"分析 {pdf_file} 失敗: {e}")
            continue
    
    return jsonify({
        'message': '掃描完成',
        'total_files': len(pdf_files),
        'analyzed_files': analyzed_count
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
    """分析已存在的PDF文件（不需要上傳）"""
    try:
        # 簡化驗證：允許測試token或直接跳過
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # 如果是測試token或沒有token，使用默認用戶ID 1
        if not token or token == 'test-token':
            user_id = 1
            # 確保用戶ID 1存在
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE id = 1")
            if not c.fetchone():
                # 創建默認用戶
                password_hash = hashlib.sha256('admin'.encode()).hexdigest()
                c.execute("INSERT INTO users (id, username, password_hash) VALUES (1, 'admin', ?)", (password_hash,))
                conn.commit()
            conn.close()
        else:
            user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'error': '未授權'}), 401
        
        filename = request.form.get('filename')
        folder_path = request.form.get('folder_path', 'reports')  # 獲取自定義文件夾路徑
        enable_web_search = request.form.get('enable_web_search', 'false').lower() == 'true'  # 是否啟用網絡搜索
        
        if not filename:
            return jsonify({'error': '缺少文件名'}), 400
        
        # 構建文件路徑，支援自定義文件夾
        if os.path.isabs(folder_path):
            pdf_folder = folder_path
        else:
            pdf_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder_path)
        
        filepath = os.path.join(pdf_folder, filename)
        
        print(f"[DEBUG] folder_path: {folder_path}")
        print(f"[DEBUG] pdf_folder: {pdf_folder}")
        print(f"[DEBUG] filename: {filename}")
        print(f"[DEBUG] filepath: {filepath}")
        print(f"[DEBUG] file exists: {os.path.exists(filepath)}")
        
        if not os.path.exists(filepath):
            return jsonify({'error': f'文件不存在: {filename} (完整路徑: {filepath})'}), 404
        
        # 解析PDF
        print(f"[PARSE] 開始解析文件: {filepath}")
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
            'investment_horizon': final_investment_horizon
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'伺服器錯誤: {str(e)}'}), 500

if __name__ == '__main__':
    init_db()
    
    print("\n" + "="*60)
    print("🚀 Broker Report Analysis System")
    print("="*60)
    print(f"📍 Server: http://localhost:62190")
    print(f"📍 Login: http://localhost:62190/broker_3quilm/")
    print(f"📍 Dashboard: http://localhost:62190/broker_3quilm/dashboard")
    print("="*60 + "\n")
    
    app.run(debug=True, port=62190, use_reloader=False)
