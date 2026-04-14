from flask import Flask, request, jsonify, send_from_directory, send_file, Blueprint
from flask_cors import CORS
import sqlite3
import hashlib
import json
import os
import secrets
from datetime import datetime
import jwt
import PyPDF2
import re
from functools import wraps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from gtts import gTTS
import requests
import threading
import queue
import time

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'), static_url_path='')
CORS(app)

# 根路由重定向到登入頁面
@app.route('/')
def root():
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web'), 'login.html')

# 創建帶路由前綴的 Blueprint
broker_bp = Blueprint('broker', __name__, url_prefix='/broker_dev_k7m')

# NVIDIA API配置
NVIDIA_API_KEY = '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'
NVIDIA_TEXT_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
NVIDIA_SPEECH_URL = 'https://integrate.api.nvidia.com/v1/audio/speech'
NVIDIA_IMAGE_URL = 'https://integrate.api.nvidia.com/v1/images/generations'

# 異步處理隊列 (必須喺線程之前定義)
analysis_queue = queue.Queue()
analysis_status = {}  # 追蹤每個分析任務的狀態
default_current_price = 550.50

# 異步處理線程
def process_analysis_queue():
    """背景處理分析隊列"""
    while True:
        try:
            task = analysis_queue.get(timeout=1)
            task_id = task['task_id']
            analysis_id = task['analysis_id']
            
            print(f"\n[隊列處理] 開始處理任務 {task_id}")
            analysis_status[task_id] = {
                'status': 'processing',
                'progress': 10,
                'message': '正在解析PDF...'
            }
            
            # Step 1: 解析PDF
            text = parse_pdf(task['file_path'])
            if not text:
                analysis_status[task_id] = {
                    'status': 'failed',
                    'progress': 0,
                    'message': 'PDF解析失敗'
                }
                update_analysis_status(analysis_id, 'failed', 'PDF解析失敗')
                continue
            
            analysis_status[task_id]['progress'] = 30
            analysis_status[task_id]['message'] = '提取券商信息...'
            
            # Step 2: 提取信息
            broker_name, rating, target_price = extract_broker_info(text)
            current_price = default_current_price
            upside = round((target_price - current_price) / current_price * 100, 2) if target_price else None
            
            analysis_status[task_id]['progress'] = 50
            analysis_status[task_id]['message'] = 'AI智能分析中...'
            
            # Step 3: AI分析
            ai_summary = generate_ai_summary(
                task['company_name'], task['stock_code'], 
                broker_name, rating, target_price, 
                current_price, upside, text
            )
            
            analysis_status[task_id]['progress'] = 90
            analysis_status[task_id]['message'] = '保存結果...'
            
            # Step 4: 更新數據庫
            update_analysis_result(
                analysis_id, broker_name, rating, 
                target_price, current_price, upside, ai_summary
            )
            
            analysis_status[task_id] = {
                'status': 'completed',
                'progress': 100,
                'message': '分析完成'
            }
            
            print(f"[隊列處理] 任務 {task_id} 完成")
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[隊列處理] 錯誤: {e}")
            if 'task_id' in locals():
                analysis_status[task_id] = {
                    'status': 'failed',
                    'progress': 0,
                    'message': f'處理失敗: {str(e)}'
                }

def update_analysis_status(analysis_id, status, message):
    """更新分析狀態"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE analysis_results SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
             (status, analysis_id))
    conn.commit()
    conn.close()

def update_analysis_result(analysis_id, broker_name, rating, target_price, current_price, upside, ai_summary):
    """更新分析結果"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''UPDATE analysis_results 
                 SET broker_name = ?, rating = ?, target_price = ?, 
                     current_price = ?, upside_potential = ?, ai_summary = ?,
                     status = 'completed', updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?''',
             (broker_name, rating, target_price, current_price, upside, ai_summary, analysis_id))
    conn.commit()
    conn.close()

# 啟動背景處理線程
queue_thread = threading.Thread(target=process_analysis_queue, daemon=True)
queue_thread.start()
print("✅ 異步處理隊列已啟動")

# API健康狀態
API_HEALTH_STATUS = {
    'nvidia_text': {'status': 'unknown', 'last_check': None, 'error': None},
    'nvidia_speech': {'status': 'unknown', 'last_check': None, 'error': None}
}

# 配置
SECRET_KEY = 'etnet-broker-analysis-secret-2026'
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'broker_analysis.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CHART_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'charts')
AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio')
REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')

os.makedirs(CHART_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 權限級別定義
ROLES = {
    'admin': {
        'can_edit_prompts': True,
        'can_delete_data': True,
        'can_manage_users': True,
        'can_view_all_data': True,
        'can_export_data': True,
        'can_access_api': True,
        'description': '管理員 - 完全權限'
    },
    'analyst': {
        'can_edit_prompts': True,
        'can_delete_data': False,
        'can_manage_users': False,
        'can_view_all_data': False,
        'can_export_data': True,
        'can_access_api': True,
        'description': '分析師 - 可編輯Prompt,查看自己數據,使用API'
    },
    'viewer': {
        'can_edit_prompts': False,
        'can_delete_data': False,
        'can_manage_users': False,
        'can_view_all_data': False,
        'can_export_data': False,
        'can_access_api': False,
        'description': '檢視者 - 僅可查看'
    }
}

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'viewer',
        api_key TEXT UNIQUE,
        company_access TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_name TEXT NOT NULL,
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
    
    # Migration: 添加缺失字段
    try:
        c.execute("ALTER TABLE analysis_results ADD COLUMN status TEXT DEFAULT 'pending'")
        print("✅ 已添加 status 字段")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE analysis_results ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ 已添加 updated_at 字段")
    except:
        pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        template_name TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        category TEXT,
        is_default BOOLEAN DEFAULT 0,
        is_public BOOLEAN DEFAULT 0,
        usage_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS api_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        api_key TEXT,
        endpoint TEXT,
        method TEXT,
        ip_address TEXT,
        response_status INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 新增：股票表
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
    
    # 新增：券商評級表（完整 15 個字段）
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
    
    c.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if c.fetchone()[0] == 0:
        admin_api_key = f"sk-{secrets.token_hex(24)}"
        c.execute('''INSERT INTO users (username, password_hash, email, role, api_key, company_access)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                 ('admin', hash_password('admin123'), 'admin@etnet.com.hk', 'admin', admin_api_key, '["*"]'))
        print(f"\n{'='*60}")
        print(f"📊 《經濟通》券商研報分析系統已初始化")
        print(f"{'='*60}")
        print(f"✅ 管理員賬戶:")
        print(f"   用戶名: admin")
        print(f"   密碼: admin123")
        print(f"   API Key: {admin_api_key}")
        print(f"💡 請妥善保存API Key!")
        print(f"{'='*60}\n")
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    return hash_password(password) == password_hash

def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow().timestamp() + 86400
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id'], payload['role']
    except:
        return None, None

def verify_api_key(api_key):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, role FROM users WHERE api_key = ?', (api_key,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return None, None

def log_api_call(user_id, api_key, endpoint, method, status, ip=''):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO api_logs (user_id, api_key, endpoint, method, ip_address, response_status)
                 VALUES (?, ?, ?, ?, ?, ?)''',
             (user_id, api_key, endpoint, method, ip, status))
    conn.commit()
    conn.close()

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')
        
        user_id = None
        role = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            user_id, role = verify_token(token)
        elif api_key:
            user_id, role = verify_api_key(api_key)
        
        if not user_id:
            log_api_call(None, api_key, request.path, request.method, 401, request.remote_addr)
            return jsonify({'error': '未授權', 'message': '請提供有效的JWT Token或API Key'}), 401
        
        if not ROLES.get(role, {}).get('can_access_api', False):
            log_api_call(user_id, api_key, request.path, request.method, 403, request.remote_addr)
            return jsonify({'error': '權限不足', 'message': '您的角色無權訪問API'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# API: Health Check (無需認證)
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康檢查 endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Broker Report Analysis API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'queue_status': {
            'pending_tasks': analysis_queue.qsize(),
            'active_tasks': len([s for s in analysis_status.values() if s.get('status') == 'processing'])
        }
    })

def parse_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages[:10]:
                text += page.extract_text() + '\n'
            return text
    except Exception as e:
        return None

def extract_stock_info(text):
    """從 PDF 文本中提取股票信息"""
    # 匹配港股代碼 (例如: 00700.HK, 09988.HK)
    stock_code_pattern = r'(\d{5})\.HK'
    match = re.search(stock_code_pattern, text)
    
    if not match:
        return None
    
    stock_code = match.group(1) + '.HK'
    
    # 常見公司名稱映射
    company_names = {
        '00700': '騰訊控股',
        '09988': '阿里巴巴',
        '03690': '美團',
        '01810': '小米集團',
        '09618': '京東集團',
        '02020': '安踏體育',
        '01299': '友邦保險',
        '00005': '匯豐控股',
        '00941': '中國移動',
        '00388': '香港交易所',
    }
    
    code_only = stock_code.replace('.HK', '')
    company_name = company_names.get(code_only, f'股票 {stock_code}')
    
    return {
        'stock_code': stock_code,
        'company_name': company_name,
        'industry': '待分類',
        'sub_industry': '待分類'
    }

def extract_broker_ratings(text):
    """從 PDF 文本中提取券商評級信息（完整 15 個字段）"""
    ratings = []
    
    # 常見券商名稱
    broker_patterns = [
        r'(摩根士丹利|Morgan Stanley|MS)',
        r'(高盛|Goldman Sachs)',
        r'(摩根大通|JPMorgan|J\.P\. Morgan)',
        r'(瑞銀|UBS)',
        r'(花旗|Citigroup|Citi)',
        r'(美國銀行|Bank of America|BOA)',
        r'(里昂|CLSA)',
        r'(招銀國際|CMB)',
        r'(中金|CICC)',
        r'(大和|Daiwa)',
        r'(野村|Nomura)',
        r'(德意志銀行|Deutsche Bank)',
        r'(麥格理|Macquarie)',
        r'(招商證券|CMS)',
    ]
    
    # 評級關鍵詞
    rating_keywords = {
        'Buy': ['買入', 'Buy', '強烈買入', 'Accumulate'],
        'Overweight': ['增持', 'Overweight', '加倉', 'Outperform'],
        'Neutral': ['中性', 'Neutral', 'Hold', '持有', 'Equal-weight'],
        'Underweight': ['減持', 'Underweight', 'Sell', 'Underperform'],
    }
    
    for broker_pattern in broker_patterns:
        match = re.search(broker_pattern, text)
        if match:
            broker_name = match.group(1)
            
            # 1. Date of Release - 查找報告日期
            date_of_release = None
            date_patterns = [
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
            ]
            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    date_of_release = date_match.group(1)
                    break
            
            # 3. Name of Stock - 從 stock_id 獲取，或從文本提取
            stock_name_match = re.search(r'([\u4e00-\u9fa5]{2,10}|[A-Z]{2,})\s*(?:控股|集團|股份|Stock)', text)
            stock_name = stock_name_match.group(1) if stock_name_match else None
            
            # 4 & 5. Industry & Sub-industry
            related_industry = None
            related_sub_industry = None
            industry_match = re.search(r'(?:行業|Industry)[:：]\s*([^\n]+)', text)
            if industry_match:
                industry_text = industry_match.group(1).strip()
                parts = industry_text.split('/')
                related_industry = parts[0].strip() if len(parts) > 0 else None
                related_sub_industry = parts[1].strip() if len(parts) > 1 else None
            
            # 6. Related Indexes
            related_indexes = None
            index_match = re.search(r'(?:指數|Index)[:：]\s*([^\n]+)', text)
            if index_match:
                related_indexes = index_match.group(1).strip()
            
            # 7. Investment Grade
            investment_grade = 'Neutral'
            for grade, keywords in rating_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        investment_grade = grade
                        break
                if investment_grade != 'Neutral':
                    break
            
            # 8. Target Price (Adjusted)
            target_price_adjusted = None
            tp_patterns = [
                r'(?:目標價|Target Price|TP)[:：\s]*([\d,]+\.?\d*)',
                r'([\d,]+\.?\d*)\s*(?:目標價|Target)',
            ]
            for pattern in tp_patterns:
                tp_match = re.search(pattern, text, re.IGNORECASE)
                if tp_match:
                    try:
                        target_price_adjusted = float(tp_match.group(1).replace(',', ''))
                        break
                    except:
                        continue
            
            # 9. Investment Horizon (default 12 months)
            investment_horizon = '12 months'
            horizon_match = re.search(r'(\d+)\s*(?:個月|months|year|年)', text, re.IGNORECASE)
            if horizon_match:
                investment_horizon = f"{horizon_match.group(1)} months"
            
            # 10. Latest Day Close before Release
            latest_close = None
            close_patterns = [
                r'(?:收市價|Close)[:：\s]*([\d,]+\.?\d*)',
                r'([\d,]+\.?\d*)\s*(?:收市|前收市)',
            ]
            for pattern in close_patterns:
                close_match = re.search(pattern, text, re.IGNORECASE)
                if close_match:
                    try:
                        latest_close = float(close_match.group(1).replace(',', ''))
                        break
                    except:
                        continue
            
            # 12. Last Transacted Price
            last_transacted = latest_close  # 如果冇找到，用 latest_close
            
            # 13. Today's Date
            today_date = datetime.now().strftime('%Y-%m-%d')
            
            ratings.append({
                'date_of_release': date_of_release,
                'broker_name': broker_name,
                'stock_name': stock_name,
                'related_industry': related_industry,
                'related_sub_industry': related_sub_industry,
                'related_indexes': related_indexes,
                'investment_grade': investment_grade,
                'target_price_adjusted': target_price_adjusted,
                'investment_horizon': investment_horizon,
                'latest_close_before_release': latest_close,
                'last_transacted_price': last_transacted,
                'today_date': today_date,
            })
    
    return ratings

def generate_ai_summary(company_name, stock_code, broker_name, rating, target_price, current_price, upside, pdf_text):
    """使用NVIDIA API生成AI總結"""
    prompt = f"""你係一位專業嘅金融分析師,請根據以下券商研報內容,為{company_name} ({stock_code})生成一份簡潔明瞭嘅分析報告:

券商: {broker_name}
評級: {rating}
目標價: HK${target_price if target_price else '未明確'}
現價: HK${current_price}
上行空間: {upside}%

研報內容摘要:
{pdf_text[:1500]}

請用繁體中文,以清晰嘅結構輸出:
1. 核心觀點 (3-5點)
2. 投資亮點
3. 風險因素
4. 操作建議

要求:簡潔、專業、 actionable。"""
    
    try:
        headers = {
            'Authorization': f'Bearer {NVIDIA_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'meta/llama-3.1-405b-instruct',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        response = requests.post(NVIDIA_TEXT_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        ai_summary = result['choices'][0]['message']['content']
        return ai_summary
    except Exception as e:
        print(f"NVIDIA API調用失敗: {e}")
        # 降級到簡單總結
        summary = f"【{company_name} ({stock_code})】券商研報分析\n\n"
        summary += f"📊 券商: {broker_name}\n"
        summary += f"⭐ 評級: {rating}\n"
        summary += f"💰 目標價: HK${target_price:.2f}\n" if target_price else "💰 目標價: 未明確\n"
        summary += f"📈 上行空間: {upside}%\n\n" if upside else ""
        summary += f"🔍 核心觀點:\n{pdf_text[:800]}..."
        return summary

def extract_broker_info(text):
    broker_mapping = {
        'BOA': '美國銀行', 'Bank of America': '美國銀行',
        'CICC': '中金公司', 'Citigroup': '花旗', 'CLSA': '里昂證券',
        'CMB': '招銀國際', 'CMS': '招商證券', 'Daiwa': '大和資本',
        'Deutsche Bank': '德意志銀行', 'JPMorgan': '摩根大通',
        'Macquarie': '麥格理', 'Morgan Stanley': '摩根士丹利',
        'Nomura': '野村證券', 'UBS': '瑞銀', 'Goldman': '高盛',
        'Merrill Lynch': '美林', 'Barclays': '巴克萊'
    }
    
    broker_name = '未知券商'
    for key, value in broker_mapping.items():
        if key.lower() in text.lower():
            broker_name = value
            break
    
    rating = '未明確'
    if any(kw in text.lower() for kw in ['buy', '買入', '強烈買入']):
        rating = '買入'
    elif any(kw in text.lower() for kw in ['overweight', '增持']):
        rating = '增持'
    elif any(kw in text.lower() for kw in ['outperform', '跑贏']):
        rating = '跑贏行業'
    elif any(kw in text.lower() for kw in ['neutral', '中性', 'hold']):
        rating = '中性'
    elif any(kw in text.lower() for kw in ['underweight', '減持']):
        rating = '減持'
    elif any(kw in text.lower() for kw in ['sell', '賣出']):
        rating = '賣出'
    
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
                price = float(matches[0].replace(',', ''))
                if 10 < price < 2000:
                    target_price = price
                    break
            except:
                continue
    
    return broker_name, rating, target_price

def generate_rating_chart(brokers_data, save_path=None):
    """生成評級分佈圖"""
    ratings = {}
    for broker in brokers_data:
        rating = broker.get('rating', '未明確')
        ratings[rating] = ratings.get(rating, 0) + 1
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {'買入': '#92D050', '增持': '#5B9BD5', '跑贏行業': '#FFC000', 
              '中性': '#FFD966', '減持': '#FF6B6B', '賣出': '#C00000'}
    
    bars = ax.bar(ratings.keys(), ratings.values(), 
                  color=[colors.get(r, '#999999') for r in ratings.keys()])
    
    ax.set_title('券商評級分佈', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('評級', fontsize=12)
    ax.set_ylabel('數量', fontsize=12)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=12)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode()

def generate_target_price_chart(brokers_data, current_price, save_path=None):
    """生成目標價對比圖"""
    brokers = [b['broker'] for b in brokers_data]
    targets = [b.get('target_price', 0) for b in brokers_data]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = ['#92D050' if t > current_price * 1.2 else 
              '#5B9BD5' if t > current_price else 
              '#FF6B6B' for t in targets]
    
    bars = ax.barh(brokers, targets, color=colors)
    ax.axvline(x=current_price, color='red', linestyle='--', linewidth=2, label=f'現價 HK${current_price}')
    
    ax.set_title('券商目標價對比', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('目標價 (HK$)', fontsize=12)
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode()

def generate_audio(text, lang='zh-tw', save_path=None):
    """生成語音"""
    tts = gTTS(text=text, lang=lang, slow=False)
    
    if save_path:
        tts.save(save_path)
        return save_path
    
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()

# ==================== API路由 ====================

@broker_bp.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web'), 'login.html')

@broker_bp.route('/dashboard')
def dashboard():
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web'), 'broker_dashboard_v2.html')

# 上傳並解析PDF文件
@broker_bp.route('/api/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '沒有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未選擇文件'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': '只支持PDF文件'}), 400
    
    try:
        # 保存文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 解析PDF內容
        pdf_text = parse_pdf(filepath)
        if not pdf_text:
            return jsonify({'error': 'PDF解析失敗'}), 500
        
        # 提取股票信息
        stock_info = extract_stock_info(pdf_text)
        
        if not stock_info:
            return jsonify({'error': '無法從PDF中提取股票信息'}), 400
        
        # 檢查是否已存在該股票
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM stocks WHERE stock_code = ?', (stock_info['stock_code'],))
        existing = cursor.fetchone()
        
        if not existing:
            # 添加新股票到數據庫
            cursor.execute('''
                INSERT INTO stocks (company_name, stock_code, industry, sub_industry, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                stock_info.get('company_name', ''),
                stock_info['stock_code'],
                stock_info.get('industry', ''),
                stock_info.get('sub_industry', ''),
                datetime.now().isoformat()
            ))
            conn.commit()
            stock_id = cursor.lastrowid
        else:
            stock_id = existing[0]
        
        # 提取券商評級信息
        broker_ratings = extract_broker_ratings(pdf_text)
        
        # 保存評級數據（完整 15 個字段）
        saved_count = 0
        for rating_data in broker_ratings:
            cursor.execute('''
                INSERT INTO broker_ratings 
                (stock_id, date_of_release, broker_name, stock_name, related_industry,
                 related_sub_industry, related_indexes, investment_grade, target_price_adjusted,
                 investment_horizon, latest_close_before_release, last_transacted_price,
                 today_date, source_link, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock_id,
                rating_data.get('date_of_release'),
                rating_data.get('broker_name', '未知'),
                rating_data.get('stock_name'),
                rating_data.get('related_industry'),
                rating_data.get('related_sub_industry'),
                rating_data.get('related_indexes'),
                rating_data.get('investment_grade', 'Neutral'),
                rating_data.get('target_price_adjusted'),
                rating_data.get('investment_horizon', '12 months'),
                rating_data.get('latest_close_before_release'),
                rating_data.get('last_transacted_price'),
                rating_data.get('today_date', datetime.now().strftime('%Y-%m-%d')),
                rating_data.get('source_link', ''),
                rating_data.get('notes', '從PDF自動提取'),
                datetime.now().isoformat()
            ))
            saved_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'成功解析 {saved_count} 條評級記錄',
            'stock_info': stock_info,
            'ratings_count': saved_count
        })
        
    except Exception as e:
        print(f"上傳錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'處理失敗: {str(e)}'}), 500

# 從本地路徑批量導入PDF
@broker_bp.route('/api/import-from-path', methods=['POST'])
def import_from_path():
    """從本地文件夾路徑批量導入PDF文件"""
    data = request.json
    folder_path = data.get('folder_path')
    
    if not folder_path:
        return jsonify({'error': '請提供文件夾路徑'}), 400
    
    if not os.path.exists(folder_path):
        return jsonify({'error': f'路徑不存在: {folder_path}'}), 404
    
    try:
        # 查找所有PDF文件
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            return jsonify({'error': '該文件夾中沒有PDF文件', 'count': 0}), 400
        
        results = []
        success_count = 0
        error_count = 0
        
        for pdf_filename in pdf_files:
            try:
                pdf_path = os.path.join(folder_path, pdf_filename)
                
                # 解析PDF
                pdf_text = parse_pdf(pdf_path)
                if not pdf_text:
                    error_count += 1
                    results.append({'file': pdf_filename, 'status': 'error', 'message': '解析失敗'})
                    continue
                
                # 提取股票信息（優先從 PDF 內容，其次從文件名）
                stock_info = extract_stock_info(pdf_text)
                
                # 如果 PDF 中找不到，嘗試從文件名提取
                if not stock_info:
                    # 只匹配文件名末尾的純數字（例如：BOA-700.pdf -> 700）
                    filename_base = pdf_filename.replace('.pdf', '')
                    # 使用更嚴格的匹配：只匹配連字符或下劃線後面的數字
                    filename_code_match = re.search(r'[-_](\d{3,5})$', filename_base)
                    if filename_code_match:
                        code_num = filename_code_match.group(1)
                        # 確保是有效的港股代碼（00001-09999）
                        if len(code_num) <= 5:
                            # 補零到 5 位
                            code_padded = code_num.zfill(5)
                            company_names = {
                                '00700': '騰訊控股',
                                '09988': '阿里巴巴',
                                '03690': '美團',
                                '01810': '小米集團',
                                '09618': '京東集團',
                                '02020': '安踏體育',
                                '01299': '友邦保險',
                                '00005': '匯豐控股',
                                '00941': '中國移動',
                                '00388': '香港交易所',
                            }
                            company_name = company_names.get(code_padded, f'股票 {code_padded}')
                            stock_info = {
                                'stock_code': f'{code_padded}.HK',
                                'company_name': company_name,
                                'industry': '未知',
                                'sub_industry': '未知'
                            }
                
                if not stock_info:
                    error_count += 1
                    results.append({'file': pdf_filename, 'status': 'error', 'message': '無法識別股票'})
                    continue
                
                # 檢查或創建股票記錄
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM stocks WHERE stock_code = ?', (stock_info['stock_code'],))
                existing = cursor.fetchone()
                
                if not existing:
                    cursor.execute('''
                        INSERT INTO stocks (company_name, stock_code, industry, sub_industry, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        stock_info.get('company_name', ''),
                        stock_info['stock_code'],
                        stock_info.get('industry', ''),
                        stock_info.get('sub_industry', ''),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    stock_id = cursor.lastrowid
                else:
                    stock_id = existing[0]
                
                # 提取券商評級
                broker_ratings = extract_broker_ratings(pdf_text)
                
                # 保存評級（完整 15 個字段）
                saved = 0
                for rating_data in broker_ratings:
                    cursor.execute('''
                        INSERT INTO broker_ratings 
                        (stock_id, date_of_release, broker_name, stock_name, related_industry,
                         related_sub_industry, related_indexes, investment_grade, target_price_adjusted,
                         investment_horizon, latest_close_before_release, last_transacted_price,
                         today_date, source_link, notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        stock_id,
                        rating_data.get('date_of_release'),
                        rating_data.get('broker_name', '未知'),
                        rating_data.get('stock_name'),
                        rating_data.get('related_industry'),
                        rating_data.get('related_sub_industry'),
                        rating_data.get('related_indexes'),
                        rating_data.get('investment_grade', 'Neutral'),
                        rating_data.get('target_price_adjusted'),
                        rating_data.get('investment_horizon', '12 months'),
                        rating_data.get('latest_close_before_release'),
                        rating_data.get('last_transacted_price'),
                        rating_data.get('today_date', datetime.now().strftime('%Y-%m-%d')),
                        rating_data.get('source_link', ''),
                        rating_data.get('notes', f'從 {pdf_filename} 自動提取'),
                        datetime.now().isoformat()
                    ))
                    saved += 1
                
                conn.commit()
                conn.close()
                
                success_count += 1
                results.append({
                    'file': pdf_filename,
                    'status': 'success',
                    'stock': stock_info,
                    'ratings_saved': saved
                })
                
            except Exception as e:
                error_count += 1
                results.append({'file': pdf_filename, 'status': 'error', 'message': str(e)})
        
        return jsonify({
            'success': True,
            'total_files': len(pdf_files),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        })
        
    except Exception as e:
        print(f"批量導入錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'處理失敗: {str(e)}'}), 500

# 獲取所有股票列表
@broker_bp.route('/api/stocks', methods=['GET'])
def get_stocks():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, company_name, stock_code, industry, sub_industry, created_at
            FROM stocks
            ORDER BY created_at DESC
        ''')
        stocks = cursor.fetchall()
        conn.close()
        
        result = []
        for stock in stocks:
            result.append({
                'id': stock[0],
                'company_name': stock[1],
                'stock_code': stock[2],
                'industry': stock[3],
                'sub_industry': stock[4],
                'created_at': stock[5]
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 獲取特定股票的券商評級
@broker_bp.route('/api/stocks/<int:stock_id>/ratings', methods=['GET'])
def get_stock_ratings(stock_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT br.id, br.broker_name, br.investment_grade, br.target_price_adjusted, 
                   br.latest_close_before_release, br.last_transacted_price, br.date_of_release,
                   br.source_link, br.notes, br.created_at,
                   s.company_name, s.stock_code
            FROM broker_ratings br
            JOIN stocks s ON br.stock_id = s.id
            WHERE br.stock_id = ?
            ORDER BY br.date_of_release DESC
        ''', (stock_id,))
        ratings = cursor.fetchall()
        conn.close()
        
        result = []
        for rating in ratings:
            result.append({
                'id': rating[0],
                'broker_name': rating[1],
                'rating': rating[2],  # investment_grade
                'target_price': rating[3],  # target_price_adjusted
                'current_price': rating[4],  # latest_close_before_release
                'upside_potential': None,  # calculated if needed
                'report_date': rating[6],  # date_of_release
                'source_link': rating[7],
                'notes': rating[8],
                'created_at': rating[9],
                'company_name': rating[10],
                'stock_code': rating[11]
            })
        
        # 計算統計數據
        target_prices = [r['target_price'] for r in result if r['target_price']]
        stats = {
            'total_ratings': len(result),
            'avg_target_price': sum(target_prices) / len(target_prices) if target_prices else None,
            'max_target_price': max(target_prices) if target_prices else None,
            'min_target_price': min(target_prices) if target_prices else None,
            'rating_distribution': {}
        }
        
        # 評級分佈
        for r in result:
            rating_type = r['rating']
            stats['rating_distribution'][rating_type] = stats['rating_distribution'].get(rating_type, 0) + 1
        
        return jsonify({
            'ratings': result,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@broker_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    
    if not username or not password:
        return jsonify({'error': '用戶名和密碼不能為空'}), 400
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        api_key = f"sk-{secrets.token_hex(24)}"
        c.execute('INSERT INTO users (username, password_hash, email, role, api_key) VALUES (?, ?, ?, ?, ?)',
                 (username, hash_password(password), email, 'viewer', api_key))
        conn.commit()
        user_id = c.lastrowid
        return jsonify({
            'success': True,
            'message': '註冊成功'
        })
    except sqlite3.IntegrityError:
        return jsonify({'error': '用戶名已存在'}), 409
    finally:
        conn.close()

@broker_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, username, role, api_key, password_hash FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user and verify_password(password, user[4]):
        token = generate_token(user[0], user[2])
        return jsonify({
            'message': '登入成功',
            'token': token,
            'api_key': user[3],
            'user': {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            }
        })
    else:
        return jsonify({'error': '用戶名或密碼錯誤'}), 401

# API 1: 文字分析
@app.route('/api/v1/analyze/text', methods=['POST'])
@require_auth
def analyze_text():
    """文字分析API - 解析PDF並生成AI總結"""
    if 'file' not in request.files:
        return jsonify({'error': '沒有文件'}), 400
    
    file = request.files['file']
    company_name = request.form.get('company_name', '未知公司')
    stock_code = request.form.get('stock_code', '')
    prompt = request.form.get('prompt', '')
    
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    text = parse_pdf(filepath)
    if not text:
        return jsonify({'error': 'PDF解析失敗'}), 500
    
    broker_name, rating, target_price = extract_broker_info(text)
    current_price = 550.50
    upside = round((target_price - current_price) / current_price * 100, 2) if target_price else None
    
    # 使用NVIDIA API生成AI總結
    ai_summary = generate_ai_summary(company_name, stock_code, broker_name, rating, target_price, current_price, upside, text)
    
    auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
    api_key = request.headers.get('X-API-Key', '')
    user_id, _ = verify_token(auth_header) if auth_header else verify_api_key(api_key)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO analysis_results 
                 (user_id, company_name, stock_code, pdf_filename, broker_name, rating, 
                  target_price, current_price, upside_potential, ai_summary, prompt_used)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (user_id, company_name, stock_code, filename, broker_name, rating,
              target_price, current_price, upside, ai_summary, prompt))
    analysis_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'analysis_id': analysis_id,
        'company_name': company_name,
        'stock_code': stock_code,
        'broker_name': broker_name,
        'rating': rating,
        'target_price': target_price,
        'current_price': current_price,
        'upside_potential': upside,
        'ai_summary': ai_summary,
        'created_at': datetime.now().isoformat()
    })

# API 1.5: 從路徑分析 (加入隊列)
@app.route('/api/v1/analyze/path', methods=['POST'])
@require_auth
def analyze_from_path():
    """從本地路徑分析PDF - 加入異步隊列"""
    file_path = request.form.get('file_path')
    company_name = request.form.get('company_name', '未知公司')
    stock_code = request.form.get('stock_code', '')
    prompt = request.form.get('prompt', '')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': '文件路徑不存在'}), 400
    
    auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
    api_key = request.headers.get('X-API-Key', '')
    user_id, _ = verify_token(auth_header) if auth_header else verify_api_key(api_key)
    
    filename = os.path.basename(file_path)
    task_id = f"task_{int(time.time() * 1000)}"
    
    # 創建待處理記錄
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO analysis_results 
                 (user_id, company_name, stock_code, pdf_filename, broker_name, rating, 
                  target_price, current_price, upside_potential, ai_summary, prompt_used, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (user_id, company_name, stock_code, filename, '', None,
              default_current_price, None, '', '等待處理...', prompt, 'queued'))
    analysis_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # 加入隊列
    analysis_queue.put({
        'task_id': task_id,
        'analysis_id': analysis_id,
        'file_path': file_path,
        'company_name': company_name,
        'stock_code': stock_code,
        'prompt': prompt,
        'user_id': user_id
    })
    
    analysis_status[task_id] = {
        'status': 'queued',
        'progress': 0,
        'message': '已加入處理隊列'
    }
    
    return jsonify({
        'task_id': task_id,
        'analysis_id': analysis_id,
        'status': 'queued',
        'message': '已加入處理隊列,請稍後查看結果'
    })

# API 1.6: 掃描資料夾
@app.route('/api/v1/scan/folder', methods=['POST'])
@require_auth
def scan_folder():
    """掃描資料夾中的PDF文件"""
    data = request.json
    folder_path = data.get('folder_path')
    
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({'error': '資料夾路徑不存在'}), 400
    
    pdf_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                pdf_files.append({
                    'filename': file,
                    'path': full_path
                })
    
    return jsonify({
        'pdf_count': len(pdf_files),
        'pdf_files': pdf_files
    })

# API 2: 圖表生成
@app.route('/api/v1/generate/chart', methods=['POST'])
@require_auth
def generate_chart():
    """圖表生成API - 生成評級分佈圖或目標價對比圖"""
    data = request.json
    chart_type = data.get('chart_type', 'rating')  # rating 或 target_price
    brokers_data = data.get('brokers_data', [])
    current_price = data.get('current_price', 550.50)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if chart_type == 'rating':
        chart_path = os.path.join(CHART_FOLDER, f'rating_{timestamp}.png')
        chart_data = generate_rating_chart(brokers_data, chart_path)
        chart_url = f'/charts/rating_{timestamp}.png'
    else:
        chart_path = os.path.join(CHART_FOLDER, f'target_{timestamp}.png')
        chart_data = generate_target_price_chart(brokers_data, current_price, chart_path)
        chart_url = f'/charts/target_{timestamp}.png'
    
    return jsonify({
        'chart_url': chart_url,
        'chart_type': chart_type,
        'download_url': f'http://localhost:5000{chart_url}',
        'message': '圖表生成成功'
    })

# API 3: 語音播報
@app.route('/api/v1/generate/audio', methods=['POST'])
@require_auth
def generate_audio_api():
    """語音播報API - 將分析結果轉成語音"""
    data = request.json
    text = data.get('text', '')
    lang = data.get('lang', 'zh-tw')
    
    if not text:
        return jsonify({'error': '請提供文本內容'}), 400
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    audio_path = os.path.join(AUDIO_FOLDER, f'audio_{timestamp}.mp3')
    generate_audio(text, lang, audio_path)
    
    audio_url = f'/audio/audio_{timestamp}.mp3'
    
    return jsonify({
        'audio_url': audio_url,
        'download_url': f'http://localhost:5000{audio_url}',
        'duration_estimate': f'{len(text) // 20}秒',
        'message': '語音生成成功'
    })

# API 4: 圖片生成 (NVIDIA NIM)
@app.route('/api/v1/generate/image', methods=['POST'])
@require_auth
def generate_image():
    """使用NVIDIA NIM生成文章封面圖"""
    data = request.json
    prompt = data.get('prompt', '')
    company_name = data.get('company_name', '')
    broker_name = data.get('broker_name', '')
    rating = data.get('rating', '')
    
    if not prompt:
        # 自動生成prompt
        prompt = f"Professional financial analysis cover image for {company_name}, stock market research report by {broker_name}, rating: {rating}, modern minimalist business style, clean design, blue and purple gradient, 1:1 square format, high quality, professional"
    
    try:
        headers = {
            'Authorization': f'Bearer {NVIDIA_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'stabilityai/stable-diffusion-3-medium',
            'prompt': prompt,
            'width': 1024,
            'height': 1024,
            'steps': 30,
            'cfg_scale': 7.0
        }
        
        response = requests.post(NVIDIA_IMAGE_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # 保存圖片
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_filename = f'cover_{timestamp}.png'
        image_path = os.path.join(CHART_FOLDER, image_filename)
        
        # 解碼base64圖片
        import base64
        image_data = base64.b64decode(result['data'][0]['b64_json'])
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        image_url = f'/charts/{image_filename}'
        
        return jsonify({
            'image_url': image_url,
            'download_url': f'http://localhost:5000{image_url}',
            'message': '圖片生成成功'
        })
    except Exception as e:
        print(f"NVIDIA生圖API調用失敗: {e}")
        return jsonify({'error': f'圖片生成失敗: {str(e)}'}), 500

# API 5: 查詢任務狀態
@app.route('/api/v1/task/status/<task_id>', methods=['GET'])
@require_auth
def get_task_status(task_id):
    """查詢異步任務狀態"""
    if task_id in analysis_status:
        return jsonify(analysis_status[task_id])
    else:
        return jsonify({'status': 'not_found', 'message': '任務不存在'}), 404

# API 6: 獲取所有待處理任務
@app.route('/api/v1/tasks/pending', methods=['GET'])
@require_auth
def get_pending_tasks():
    """獲取所有待處理/處理中的任務"""
    auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
    api_key = request.headers.get('X-API-Key', '')
    user_id, _ = verify_token(auth_header) if auth_header else verify_api_key(api_key)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT id, company_name, stock_code, pdf_filename, status, created_at, updated_at
                 FROM analysis_results 
                 WHERE user_id = ? AND status IN ('queued', 'processing')
                 ORDER BY created_at DESC''', (user_id,))
    
    tasks = []
    for row in c.fetchall():
        task_id = f"task_{row[0]}"
        status_info = analysis_status.get(task_id, {})
        tasks.append({
            'analysis_id': row[0],
            'task_id': task_id,
            'company_name': row[1],
            'stock_code': row[2],
            'pdf_filename': row[3],
            'status': row[4],
            'progress': status_info.get('progress', 0),
            'message': status_info.get('message', ''),
            'created_at': row[5],
            'updated_at': row[6]
        })
    
    conn.close()
    return jsonify({'tasks': tasks, 'total': len(tasks)})

@app.route('/api/results', methods=['GET'])
@require_auth
def get_results():
    """獲取歷史分析結果"""
    auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
    api_key = request.headers.get('X-API-Key', '')
    user_id, role = verify_token(auth_header) if auth_header else verify_api_key(api_key)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if ROLES.get(role, {}).get('can_view_all_data', False):
        c.execute('''SELECT id, company_name, stock_code, pdf_filename, broker_name, rating, 
                            target_price, current_price, upside_potential, ai_summary, 
                            chart_path, audio_path, created_at
                     FROM analysis_results 
                     ORDER BY created_at DESC''')
    else:
        c.execute('''SELECT id, company_name, stock_code, pdf_filename, broker_name, rating, 
                            target_price, current_price, upside_potential, ai_summary, 
                            chart_path, audio_path, created_at
                     FROM analysis_results 
                     WHERE user_id = ?
                     ORDER BY created_at DESC''', (user_id,))
    
    results = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': r[0],
        'company_name': r[1],
        'stock_code': r[2],
        'pdf_filename': r[3],
        'broker_name': r[4],
        'rating': r[5],
        'target_price': r[6],
        'current_price': r[7],
        'upside_potential': r[8],
        'ai_summary': r[9],
        'chart_path': r[10],
        'audio_path': r[11],
        'created_at': r[12]
    } for r in results])

@app.route('/api/prompts', methods=['GET'])
@require_auth
def get_prompts():
    auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
    api_key = request.headers.get('X-API-Key', '')
    user_id, role = verify_token(auth_header) if auth_header else verify_api_key(api_key)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if ROLES.get(role, {}).get('can_edit_prompts', False):
        c.execute('''SELECT id, template_name, prompt_text, category, is_default, is_public
                     FROM prompt_templates
                     WHERE user_id = ? OR is_default = 1 OR is_public = 1
                     ORDER BY is_default DESC, created_at DESC''', (user_id,))
    else:
        c.execute('''SELECT id, template_name, prompt_text, category, is_default, is_public
                     FROM prompt_templates
                     WHERE is_default = 1 OR is_public = 1
                     ORDER BY is_default DESC''')
    
    prompts = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': p[0],
        'template_name': p[1],
        'prompt_text': p[2],
        'category': p[3],
        'is_default': p[4],
        'is_public': p[5]
    } for p in prompts])

@app.route('/api/prompts', methods=['POST'])
@require_auth
def save_prompt():
    auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
    api_key = request.headers.get('X-API-Key', '')
    user_id, role = verify_token(auth_header) if auth_header else verify_api_key(api_key)
    
    if not ROLES.get(role, {}).get('can_edit_prompts', False):
        return jsonify({'error': '權限不足'}), 403
    
    data = request.json
    template_name = data.get('template_name')
    prompt_text = data.get('prompt_text')
    category = data.get('category', '通用')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO prompt_templates (user_id, template_name, prompt_text, category)
                 VALUES (?, ?, ?, ?)''',
             (user_id, template_name, prompt_text, category))
    conn.commit()
    prompt_id = c.lastrowid
    conn.close()
    
    return jsonify({'id': prompt_id, 'message': 'Prompt已保存'})

@app.route('/api/feedback', methods=['POST'])
@require_auth
def submit_feedback():
    auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
    api_key = request.headers.get('X-API-Key', '')
    user_id, _ = verify_token(auth_header) if auth_header else verify_api_key(api_key)
    
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

if __name__ == '__main__':
    init_db()
    # 註冊帶路由前綴的 Blueprint
    app.register_blueprint(broker_bp)
    app.run(debug=True, port=54892)
