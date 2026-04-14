#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
從本地PDF研報生成騰訊控股券商評級Excel表格
"""

import os
import re
import pandas as pd
from datetime import datetime
from PyPDF2 import PdfReader

class TencentBrokerReportGenerator:
    def __init__(self, pdf_folder, enable_web_search=False):
        self.pdf_folder = pdf_folder
        self.data_rows = []
        self.enable_web_search = enable_web_search  # 預設關閉上網功能
        
    def extract_broker_name(self, filename):
        """從文件名提取券商名稱"""
        broker_mapping = {
            'BOA': '美國銀行',
            'CICC': '中金公司',
            'CITIGROUP': '花旗集團',
            'CLSA': '里昂證券',
            'CMB': '招銀國際',
            'CMS': '招商證券',
            'DAIWA': '大和資本',
            'DEUTSCHE': '德意志銀行',
            'JP': '摩根大通',
            'MAC': '麥格理',
            'MS': '摩根士丹利',
            'NOMURA': '野村證券',
            'UBS': '瑞銀集團',
            'GOLDMAN': '高盛',
        }
        
        for key, value in broker_mapping.items():
            if key in filename.upper():
                return value
        
        return '未知券商'
    
    def extract_info_from_pdf(self, pdf_path):
        """從PDF提取關鍵信息"""
        try:
            reader = PdfReader(pdf_path)
            text = ''
            
            # 讀取前10頁
            for page_num in range(min(10, len(reader.pages))):
                text += reader.pages[page_num].extract_text() + '\n'
            
            return text
        except Exception as e:
            print(f"讀取PDF失敗 {pdf_path}: {e}")
            return ''
    
    def extract_target_price(self, text):
        """提取目標價"""
        patterns = [
            r'[Tt]arget [Pp]rice.*?([\d,]+\.?\d*)',
            r'目標價.*?([\d,]+\.?\d*)',
            r'TP.*?([\d,]+\.?\d*)',
            r'目标价.*?([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    price = float(matches[0].replace(',', ''))
                    if 100 < price < 1000:
                        return price
                except:
                    continue
        
        return None
    
    def extract_rating(self, text):
        """提取投資評級"""
        rating_map = {
            '買入': ['buy', '買入', '強烈買入', 'strong buy'],
            '增持': ['overweight', '增持', '加倉', 'outperform'],
            '跑贏': ['outperform', '跑贏', '優於大市'],
            '中性': ['neutral', '中性', 'hold', '持有', 'market perform'],
            '減持': ['underweight', '減持', 'sell', 'underperform'],
        }
        
        text_lower = text.lower()
        
        for rating, keywords in rating_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return rating
        
        return '未明確'
    
    def extract_date_from_filename(self, filename):
        """從文件名提取日期"""
        # 嘗試匹配 YYYYMMDD 或 YYYY-MM-DD 格式
        patterns = [
            r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    year, month, day = match.groups()
                    return f"{year}-{month}-{day}"
                except:
                    continue
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def fetch_realtime_price(self, stock_code='00700.HK'):
        """獲取實時股價 (需開啟上網功能)"""
        if not self.enable_web_search:
            print(f"  ⚠️  上網功能已關閉,使用預設股價 HK$ 550.50")
            print(f"  💡 如需獲取實時股價,請設置 ENABLE_WEB_SEARCH = True")
            return 550.50
        
        # TODO: 這裡可以加入真實的API調用
        # 例如: Yahoo Finance, Alpha Vantage, 或其他金融API
        try:
            import yfinance as yf
            stock = yf.Ticker(stock_code)
            current_price = stock.history(period='1d')['Close'].iloc[-1]
            return float(current_price)
        except Exception as e:
            print(f"  ⚠️  獲取股價失敗: {e}, 使用預設值")
            return 550.50
    
    def process_pdfs(self):
        """處理所有PDF文件"""
        print("=" * 80)
        print("開始處理騰訊控股券商研報PDF...")
        print(f"上網功能: {'✅ 已開啟' if self.enable_web_search else '❌ 已關閉'}")
        print("=" * 80)
        
        pdf_files = [f for f in os.listdir(self.pdf_folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"在 {self.pdf_folder} 中未找到PDF文件")
            return
        
        print(f"找到 {len(pdf_files)} 個PDF文件\n")
        
        # 獲取實時股價
        current_price = self.fetch_realtime_price()
        
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"[{idx}/{len(pdf_files)}] 處理: {pdf_file}")
            
            pdf_path = os.path.join(self.pdf_folder, pdf_file)
            broker = self.extract_broker_name(pdf_file)
            date_str = self.extract_date_from_filename(pdf_file)
            
            # 提取PDF內容
            text = self.extract_info_from_pdf(pdf_path)
            
            if text:
                target_price = self.extract_target_price(text)
                rating = self.extract_rating(text)
                
                # 只保留目標價 >= 700 的記錄
                if target_price and target_price >= 700:
                    row = {
                        'Date of Release': date_str,
                        'Name of Broker': broker,
                        'Name of Stock': '騰訊控股',
                        'Stock Code': '00700.HK',
                        'Related Industry': '互聯網科技',
                        'Related Sub-industry': '遊戲/社交網絡/AI應用/雲計算/金融科技',
                        'Related Indexes': '恒生指數/恆生科技指數/MSCI中國指數',
                        'Investment Grade': rating,
                        'Target Price (Adj)': target_price,
                        'Latest Day Close': current_price,
                        'Date of Target Hit': '',  # 需要根據歷史數據推算
                        'Date of Grade Revised': date_str,
                        'Date of Target Revised': date_str,
                        'Source Link': f'file:///{pdf_path.replace(chr(92), "/")}',
                        'Notes': f'目標價>=700港元 | 來源: {pdf_file}'
                    }
                    self.data_rows.append(row)
                    print(f"  ✓ 目標價: HK$ {target_price:.2f}, 評級: {rating}")
                else:
                    print(f"  ✗ 目標價不符合條件或不明確")
            else:
                print(f"  ✗ PDF解析失敗")
            
            print()
    
    def generate_excel(self):
        """生成Excel文件"""
        if not self.data_rows:
            print("\n❌ 未找到符合條件的數據")
            return None
        
        df = pd.DataFrame(self.data_rows)
        
        # 統計分析
        avg_target = df['Target Price (Adj)'].mean()
        max_target = df['Target Price (Adj)'].max()
        min_target = df['Target Price (Adj)'].min()
        current_price = df['Latest Day Close'].iloc[0]  # 使用實際股價
        avg_upside = ((avg_target - current_price) / current_price * 100)
        
        rating_dist = df['Investment Grade'].value_counts()
        
        print("\n" + "=" * 80)
        print("📊 數據汇总分析")
        print("=" * 80)
        print(f"有效記錄數: {len(df)} 家券商")
        print(f"平均目標價: HK$ {avg_target:.2f}")
        print(f"最高目標價: HK$ {max_target:.2f}")
        print(f"最低目標價: HK$ {min_target:.2f}")
        print(f"現價: HK$ {current_price:.2f}")
        print(f"平均上行空間: {avg_upside:.2f}%")
        print(f"\n📈 評級分佈:")
        for rating, count in rating_dist.items():
            percentage = (count / len(df) * 100)
            print(f"  {rating}: {count} 家 ({percentage:.1f}%)")
        
        # 保存Excel
        output_file = f"騰訊控股_券商評級彙總_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 主數據表
            df.to_excel(writer, sheet_name='券商評級數據', index=False)
            
            # 調整列寬
            worksheet = writer.sheets['券商評級數據']
            for column_cells in worksheet.columns:
                max_length = 0
                column = column_cells[0].column_letter
                for cell in column_cells:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column].width = adjusted_width
            
            # 統計摘要表
            summary_data = {
                '指標': [
                    '有效券商數量',
                    '平均目標價',
                    '最高目標價',
                    '最低目標價',
                    '現價',
                    '平均上行空間',
                    '目標價標準差',
                    '中位數目標價',
                    '數據來源'
                ],
                '數值': [
                    f"{len(df)} 家",
                    f"HK$ {avg_target:.2f}",
                    f"HK$ {max_target:.2f}",
                    f"HK$ {min_target:.2f}",
                    f"HK$ {current_price:.2f}",
                    f"{avg_upside:.2f}%",
                    f"HK$ {df['Target Price (Adj)'].std():.2f}",
                    f"HK$ {df['Target Price (Adj)'].median():.2f}",
                    '本地PDF研報' + (' + 網上數據' if self.enable_web_search else '')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='統計摘要', index=False)
            
            # 評級分佈表
            rating_df = rating_dist.reset_index()
            rating_df.columns = ['評級', '券商數量']
            rating_df['佔比'] = (rating_df['券商數量'] / len(df) * 100).round(1).astype(str) + '%'
            rating_df.to_excel(writer, sheet_name='評級分佈', index=False)
            
            # 券商明細表
            broker_detail = df[['Name of Broker', 'Investment Grade', 'Target Price (Adj)', 'Date of Release']].copy()
            broker_detail = broker_detail.sort_values('Target Price (Adj)', ascending=False)
            broker_detail.to_excel(writer, sheet_name='券商明細', index=False)
        
        print(f"\n✅ Excel文件已生成: {output_file}")
        print(f"📁 文件位置: {os.path.abspath(output_file)}")
        
        return output_file

if __name__ == '__main__':
    # 設置PDF資料夾路徑
    pdf_folder = r'C:\Users\user\Desktop\Broker report 分析\700'
    
    # ⚠️ 上網功能預設關閉,如需開啟請改為 True
    ENABLE_WEB_SEARCH = False
    
    generator = TencentBrokerReportGenerator(pdf_folder, enable_web_search=ENABLE_WEB_SEARCH)
    generator.process_pdfs()
    generator.generate_excel()
