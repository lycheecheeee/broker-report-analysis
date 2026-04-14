import pandas as pd
from datetime import datetime

# 數據準備
data = [
    {
        'Date of Release': '2026-04-10',
        'Name of Broker': '中金公司 (CICC)',
        'Name of Stock': '騰訊控股 (00700.HK)',
        'Related Industry': '互聯網科技',
        'Related Sub-industry': '社交遊戲/廣告/雲計算',
        'Related Indexes': '恒生指數、恒生科技指數',
        'Investment Grade': '跑贏行業 (Outperform)',
        'Target Price (Adj)': 700.00,
        'Latest Day Close': 508.00,
        'Date of Target Hit': '預計2026年底',
        'Date of Grade Revised': '2026-04-10',
        'Date of Target Revised': '2026-04-10',
        'Source Link': 'https://xueqiu.com/s/00700/346972715',
        'Notes': '基於AI賦能前景，估值切換至2026年20x Non-IFRS P/E，上行空間19%'
    },
    {
        'Date of Release': '2026-03-20',
        'Name of Broker': '招商證券(香港) (CMS)',
        'Name of Stock': '騰訊控股 (00700.HK)',
        'Related Industry': '互聯網科技',
        'Related Sub-industry': '遊戲/廣告/金融科技',
        'Related Indexes': '恒生指數、MSCI中國指數',
        'Investment Grade': '買入 (Buy)',
        'Target Price (Adj)': 750.00,
        'Latest Day Close': 508.00,
        'Date of Target Hit': '預計2027年中',
        'Date of Grade Revised': '',
        'Date of Target Revised': '2026-03-20',
        'Source Link': 'http://c.m.163.com/news/a/KOFG1QFR05198CJN.html',
        'Notes': '核心業務穩健，AI投資強化長期競爭力，SOTP估值具支撐'
    },
    {
        'Date of Release': '2026-03-20',
        'Name of Broker': '摩根大通 (JPMorgan)',
        'Name of Stock': '騰訊控股 (00700.HK)',
        'Related Industry': '互聯網科技',
        'Related Sub-industry': '社交媒體/遊戲/雲服務',
        'Related Indexes': '恒生指數、納斯達克金龍指數',
        'Investment Grade': '增持 (Overweight)',
        'Target Price (Adj)': 750.00,
        'Latest Day Close': 508.00,
        'Date of Target Hit': '預計2027年初',
        'Date of Grade Revised': '',
        'Date of Target Revised': '2026-03-19',
        'Source Link': 'https://finance.sina.cn/hkstock/ggpj/2026-03-19/detail-inhrpfxy1515372.d.html',
        'Notes': 'AI在廣告、遊戲及雲端展現商業價值，現金流韌性強'
    },
    {
        'Date of Release': '2026-03-23',
        'Name of Broker': '美銀證券 (Bank of America)',
        'Name of Stock': '騰訊控股 (00700.HK)',
        'Related Industry': '互聯網科技',
        'Related Sub-industry': '數字內容/AI/金融科技',
        'Related Indexes': '恒生指數、標普中國指數',
        'Investment Grade': '買入 (Buy)',
        'Target Price (Adj)': 780.00,
        'Latest Day Close': 508.00,
        'Date of Target Hit': '預計2027年底',
        'Date of Grade Revised': '',
        'Date of Target Revised': '2026-03-23',
        'Source Link': 'https://m.10jqka.com.cn/20260323/c675486658.html',
        'Notes': '混元3.0模型升級、微信智能體推出將驅動估值重估'
    },
    {
        'Date of Release': '2026-03-30',
        'Name of Broker': '野村證券 (Nomura)',
        'Name of Stock': '騰訊控股 (00700.HK)',
        'Related Industry': '互聯網科技',
        'Related Sub-industry': '遊戲/社交網絡/企業服務',
        'Related Indexes': '恒生指數、日經亞洲指數',
        'Investment Grade': '買入 (Buy)',
        'Target Price (Adj)': 727.00,
        'Latest Day Close': 508.00,
        'Date of Target Hit': '預計2027年中',
        'Date of Grade Revised': '2026-03-30',
        'Date of Target Revised': '2026-03-30',
        'Source Link': 'https://xueqiu.com/9294987065/381791240',
        'Notes': '隱含上行空間+43.1%，對應2026財年21倍預測市盈率'
    },
    {
        'Date of Release': '2026-03-20',
        'Name of Broker': '華泰證券 (Huatai Securities)',
        'Name of Stock': '騰訊控股 (00700.HK)',
        'Related Industry': '互聯網科技',
        'Related Sub-industry': '視頻號/電商佣金/廣告',
        'Related Indexes': '恒生指數、滬深港通指數',
        'Investment Grade': '買入 (Buy)',
        'Target Price (Adj)': 742.19,
        'Latest Day Close': 508.00,
        'Date of Target Hit': '預計2026年底',
        'Date of Grade Revised': '2026-03-20',
        'Date of Target Revised': '2026-03-20',
        'Source Link': 'http://wdatacn.aastocks.com/sc/stocks/news/aafn-con/NOW.1461305/popular-news/AAFN',
        'Notes': 'SOTP估值法，對應2025年24.3倍PE，視頻號impression增長強勁'
    },
    {
        'Date of Release': '2026-03-20',
        'Name of Broker': '招商證券國際 (CMS International)',
        'Name of Stock': '騰訊控股 (00700.HK)',
        'Related Industry': '互聯網科技',
        'Related Sub-industry': '遊戲/廣告/雲計算',
        'Related Indexes': '恒生指數、MSCI新興市場指數',
        'Investment Grade': '增持 (Overweight)',
        'Target Price (Adj)': 700.00,
        'Latest Day Close': 508.00,
        'Date of Target Hit': '預計2026年底',
        'Date of Grade Revised': '2026-03-20',
        'Date of Target Revised': '2026-03-20',
        'Source Link': 'https://m.sohu.com/a/998836856_122123195/',
        'Notes': '由766港元調低8.6%至700港元，反映AI投入考量'
    }
]

# 創建DataFrame
df = pd.DataFrame(data)

# 計算統計數據
avg_target = df['Target Price (Adj)'].mean()
max_target = df['Target Price (Adj)'].max()
min_target = df['Target Price (Adj)'].min()
upside_avg = ((avg_target - 508) / 508 * 100)

# 保存為Excel
output_file = 'data/騰訊控股_券商評級彙總.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # 主要數據表
    df.to_excel(writer, sheet_name='券商評級彙總', index=False)
    
    # 統計摘要表
    summary_data = {
        '指標': [
            '最高目標價',
            '最低目標價',
            '平均目標價',
            '基準價格 (2026-03-20)',
            '平均上行空間',
            '券商總數',
            '買入評級數量',
            '增持評級數量',
            '數據生成日期'
        ],
        '數值': [
            f'HK$ {max_target:.2f}',
            f'HK$ {min_target:.2f}',
            f'HK$ {avg_target:.2f}',
            'HK$ 508.00',
            f'+{upside_avg:.1f}%',
            len(df),
            len(df[df['Investment Grade'].str.contains('Buy|買入')]),
            len(df[df['Investment Grade'].str.contains('Overweight|Outperform|增持|跑贏')]),
            datetime.now().strftime('%Y-%m-%d')
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    df_summary.to_excel(writer, sheet_name='統計摘要', index=False)
    
    # 字段說明表
    fields_data = {
        '#': list(range(1, 16)),
        'Field Name': [
            'Date of Release',
            'Name of Broker',
            'Name of Stock',
            'Related Industry',
            'Related Sub-industry',
            'Related Indexes',
            'Investment Grade',
            'Target Price (Adjusted)',
            'Investment Horizon',
            'Latest Day Close before Release',
            'Date of Target First Hit',
            'Last Transacted Price as of Today',
            "Today's Date",
            'Date of Investment Grade Revised',
            'Date of Target Price Revised'
        ],
        'Chinese Name': [
            '報告發布日期',
            '券商名稱',
            '股票名稱',
            '相關行業',
            '相關子行業',
            '相關指數',
            '投資評級',
            '目標價(調整後)',
            '投資週期',
            '發布前最新收盤價',
            '首次觸及目標價日期',
            '今日最後成交價',
            '今日日期',
            '評級修訂日期',
            '目標價修訂日期'
        ],
        'Data Type': [
            'DATE', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT',
            'TEXT', 'REAL', 'TEXT', 'REAL', 'DATE', 'REAL',
            'DATE', 'DATE', 'DATE'
        ]
    }
    df_fields = pd.DataFrame(fields_data)
    df_fields.to_excel(writer, sheet_name='字段說明', index=False)

print(f"✅ Excel文件已生成: {output_file}")
print(f"📊 包含 {len(df)} 家券商數據")
print(f"📈 平均目標價: HK$ {avg_target:.2f}")
print(f"📉 平均上行空間: +{upside_avg:.1f}%")
