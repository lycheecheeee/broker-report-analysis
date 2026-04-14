import PyPDF2
import json
import os
import re
from datetime import datetime

# PDF文件清單
pdf_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

# 券商對應
broker_mapping = {
    'BOA-700.pdf': '美國銀行 (Bank of America)',
    'CICC-700.pdf': '中金公司 (CICC)',
    'CITIGROUP-700.pdf': '花旗 (Citigroup)',
    'CLSA-700.pdf': '里昂證券 (CLSA)',
    'CMB-700.pdf': '招銀國際 (CMB International)',
    'CMS-700.pdf': '招商證券 (CMS)',
    'DAIWA-700.pdf': '大和資本 (Daiwa)',
    'DEUTSCHE-700.pdf': '德意志銀行 (Deutsche Bank)',
    'JP-700.pdf': '摩根大通 (JPMorgan)',
    'MAC-700.pdf': '麥格理 (Macquarie)',
    'MS-700.pdf': '摩根士丹利 (Morgan Stanley)',
    'NOMURA-700.pdf': '野村證券 (Nomura)',
    'UBS-700.pdf': '瑞銀 (UBS)'
}

def extract_text_from_pdf(pdf_path):
    """從PDF提取文本"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
            return text
    except Exception as e:
        print(f"讀取 {pdf_path} 失敗: {e}")
        return None

def extract_rating(text):
    """提取投資評級"""
    ratings = {
        '買入': ['買入', 'BUY', 'Buy', 'buy'],
        '增持': ['增持', 'OVERWEIGHT', 'Overweight', 'Over-weight'],
        '跑贏行業': ['跑贏行業', '跑贏大市', 'OUTPERFORM', 'Outperform'],
        '中性': ['中性', 'NEUTRAL', 'Neutral', 'HOLD', 'Hold'],
        '減持': ['減持', 'UNDERWEIGHT', 'Underweight'],
        '賣出': ['賣出', 'SELL', 'Sell']
    }
    
    for rating, keywords in ratings.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return rating
    return '未明確'

def extract_target_price(text):
    """提取目標價"""
    # 匹配 HK$ 數字 或 目標價 數字
    patterns = [
        r'[Tt]arget [Pp]rice.*?([\d,]+\.?\d*)',
        r'目標價.*?([\d,]+\.?\d*)',
        r'TP.*?([\d,]+\.?\d*)',
        r'HK\$\s*([\d,]+\.?\d*)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            # 清理數字
            price_str = matches[0].replace(',', '')
            try:
                return float(price_str)
            except:
                continue
    return None

def extract_date_from_filename(filename):
    """從文件名或文件屬性提取日期"""
    # 嘗試從文件名提取
    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', filename)
    if date_match:
        return date_match.group(1).replace('/', '-')
    
    # 如果沒有,使用文件修改日期
    return None

def parse_pdf_data(pdf_filename):
    """解析單個PDF文件"""
    pdf_path = os.path.join(pdf_folder, pdf_filename)
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return None
    
    broker_name = broker_mapping.get(pdf_filename, pdf_filename)
    rating = extract_rating(text)
    target_price = extract_target_price(text)
    
    # 計算上行空間
    current_price = 550.50  # 最新收盤價
    upside = None
    if target_price:
        upside = round((target_price - current_price) / current_price * 100, 2)
    
    return {
        'broker': broker_name,
        'filename': pdf_filename,
        'rating': rating,
        'target_price': target_price,
        'current_price': current_price,
        'upside_potential': upside,
        'pdf_text_sample': text[:500] if text else ''  # 前500字符用於調試
    }

# 解析所有PDF
results = []
for pdf_file in pdf_files:
    print(f"正在解析: {pdf_file}")
    data = parse_pdf_data(pdf_file)
    if data:
        results.append(data)

# 保存結果
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'broker_data.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✅ 成功解析 {len(results)} 份PDF文件")
print(f"📄 數據已保存到: {output_file}")

# 打印摘要
print("\n=== 解析結果摘要 ===")
for r in results:
    print(f"{r['broker']}: {r['rating']} | 目標價 HK${r['target_price']} | 上行空間 {r['upside_potential']}%")
