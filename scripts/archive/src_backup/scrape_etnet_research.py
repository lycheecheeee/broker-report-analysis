#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
經濟通券商研報數據抓取工具
從 etnet.com.hk 抓取腾讯控股(00700.HK)的券商評級數據
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time
import os

class ETNetScraper:
    def __init__(self):
        self.base_url = "https://www.etnet.com.hk/www/tc/news/categorized_news_list.php?category=research"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_page(self, page=1):
        """抓取指定頁數"""
        params = {'page': page}
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"抓取失敗: {e}")
            return None
    
    def parse_articles(self, html):
        """解析文章列表"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # 查找文章項目 (需要根據實際HTML結構調整)
        article_items = soup.find_all('div', class_=lambda x: x and 'news' in x.lower()) or \
                       soup.find_all('li', class_=lambda x: x and 'item' in x.lower()) or \
                       soup.find_all('a', href=lambda x: x and 'stocks' in str(x))
        
        for item in article_items:
            try:
                # 提取標題
                title_elem = item.find('a') or item.find('h3') or item.find('h4')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # 只處理包含"騰訊"或"00700"的文章
                if '騰訊' not in title and '00700' not in title and 'Tencent' not in title:
                    continue
                
                # 提取連結
                link = title_elem.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://www.etnet.com.hk{link}"
                
                # 提取日期
                date_elem = item.find(class_=lambda x: x and 'date' in str(x).lower()) or \
                           item.find('span', string=re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}'))
                date_str = date_elem.get_text(strip=True) if date_elem else ''
                
                articles.append({
                    'title': title,
                    'link': link,
                    'date': date_str
                })
                
            except Exception as e:
                continue
        
        return articles
    
    def extract_broker_info(self, title):
        """從標題提取券商名稱"""
        broker_patterns = [
            r'(摩根士丹利|Morgan Stanley|MS)',
            r'(高盛|Goldman Sachs)',
            r'(摩根大通|JPMorgan|J.P. Morgan)',
            r'(瑞銀|UBS)',
            r'(花旗|Citigroup|Citi)',
            r'(美銀|Bank of America|BOA)',
            r'(里昂|CLSA)',
            r'(招銀國際|CMB)',
            r'(中金|CICC)',
            r'(大和|Daiwa)',
            r'(野村|Nomura)',
            r'(德銀|Deutsche Bank)',
            r'(麥格理|Macquarie)',
            r'(招商證券|CMS)',
        ]
        
        for pattern in broker_patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)
        
        return '未知券商'
    
    def extract_target_price(self, text):
        """從文本提取目標價"""
        patterns = [
            r'目標價.*?([\d,]+\.?\d*)',
            r'Target Price.*?([\d,]+\.?\d*)',
            r'TP.*?([\d,]+\.?\d*)',
            r'評級.*?([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    price = float(matches[0].replace(',', ''))
                    if 100 < price < 1000:  # 合理範圍
                        return price
                except:
                    continue
        
        return None
    
    def extract_rating(self, text):
        """提取投資評級"""
        rating_map = {
            '買入': ['買入', 'Buy', '強烈買入'],
            '增持': ['增持', 'Overweight', '加倉'],
            '跑贏': ['跑贏', 'Outperform', '優於大市'],
            '中性': ['中性', 'Neutral', 'Hold', '持有'],
            '減持': ['減持', 'Underweight', 'Sell'],
        }
        
        for rating, keywords in rating_map.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    return rating
        
        return '未明確'
    
    def scrape_detailed_article(self, url):
        """抓取文章詳細內容"""
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取全文
            content_div = soup.find('div', class_='article-content') or \
                         soup.find('div', id='content') or \
                         soup.find('article')
            
            if content_div:
                return content_div.get_text(strip=False)[:3000]  # 限制長度
            
            return ''
        except Exception as e:
            print(f"抓取詳情失敗 {url}: {e}")
            return ''
    
    def run(self, max_pages=5):
        """執行抓取"""
        print("=" * 60)
        print("開始抓取經濟通券商研報數據...")
        print("=" * 60)
        
        all_articles = []
        
        for page in range(1, max_pages + 1):
            print(f"\n正在抓取第 {page} 頁...")
            html = self.fetch_page(page)
            if not html:
                break
            
            articles = self.parse_articles(html)
            if not articles:
                print(f"第 {page} 頁無數據")
                break
            
            all_articles.extend(articles)
            print(f"找到 {len(articles)} 篇相關文章")
            
            time.sleep(1)  # 避免請求過快
        
        print(f"\n總共找到 {len(all_articles)} 篇文章")
        
        # 處理每篇文章
        data_rows = []
        for idx, article in enumerate(all_articles, 1):
            print(f"\n處理 [{idx}/{len(all_articles)}]: {article['title'][:50]}...")
            
            broker = self.extract_broker_info(article['title'])
            
            # 抓取詳細內容
            if article['link']:
                detail_text = self.scrape_detailed_article(article['link'])
                target_price = self.extract_target_price(detail_text)
                rating = self.extract_rating(detail_text)
            else:
                detail_text = ''
                target_price = None
                rating = '未明確'
            
            # 只保留目標價 >= 700 的記錄
            if target_price and target_price >= 700:
                row = {
                    'Date of Release': article['date'] or datetime.now().strftime('%Y-%m-%d'),
                    'Name of Broker': broker,
                    'Name of Stock': '騰訊控股',
                    'Stock Code': '00700.HK',
                    'Related Industry': '互聯網科技',
                    'Related Sub-industry': '遊戲/社交/AI/雲服務',
                    'Related Indexes': '恒生指數/恆生科技指數',
                    'Investment Grade': rating,
                    'Target Price (Adj)': target_price,
                    'Latest Day Close': 550.50,  # 需要從API獲取實時股價
                    'Date of Target Hit': '',  # 需要推算
                    'Date of Grade Revised': article['date'],
                    'Date of Target Revised': article['date'],
                    'Source Link': article['link'],
                    'Notes': '目標價>=700港元'
                }
                data_rows.append(row)
        
        # 創建DataFrame
        if data_rows:
            df = pd.DataFrame(data_rows)
            
            # 計算統計數據
            avg_target = df['Target Price (Adj)'].mean()
            rating_dist = df['Investment Grade'].value_counts()
            
            print("\n" + "=" * 60)
            print("數據汇总分析")
            print("=" * 60)
            print(f"有效記錄數: {len(df)}")
            print(f"平均目標價: HK$ {avg_target:.2f}")
            print(f"最高目標價: HK$ {df['Target Price (Adj)'].max():.2f}")
            print(f"最低目標價: HK$ {df['Target Price (Adj)'].min():.2f}")
            print(f"\n評級分佈:\n{rating_dist}")
            
            # 保存Excel
            output_file = f"騰訊控股_券商評級彙總_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 主數據表
                df.to_excel(writer, sheet_name='券商評級數據', index=False)
                
                # 統計摘要
                summary_data = {
                    '指標': ['有效記錄數', '平均目標價', '最高目標價', '最低目標價', '現價', '平均上行空間'],
                    '數值': [
                        len(df),
                        f"HK$ {avg_target:.2f}",
                        f"HK$ {df['Target Price (Adj)'].max():.2f}",
                        f"HK$ {df['Target Price (Adj)'].min():.2f}",
                        "HK$ 550.50",
                        f"{((avg_target - 550.50) / 550.50 * 100):.2f}%"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='統計摘要', index=False)
                
                # 評級分佈
                rating_df = rating_dist.reset_index()
                rating_df.columns = ['評級', '數量']
                rating_df.to_excel(writer, sheet_name='評級分佈', index=False)
            
            print(f"\n✅ Excel文件已保存: {output_file}")
            return output_file
        else:
            print("\n❌ 未找到符合條件的數據")
            return None

if __name__ == '__main__':
    scraper = ETNetScraper()
    scraper.run(max_pages=10)
