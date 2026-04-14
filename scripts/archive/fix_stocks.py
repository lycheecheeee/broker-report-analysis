import sqlite3

conn = sqlite3.connect('data/broker_analysis.db')
c = conn.cursor()

# 顯示所有股票
print('Current stocks:')
c.execute('SELECT id, stock_code, company_name FROM stocks')
for row in c.fetchall():
    print(f'  ID={row[0]}, Code={row[1]}, Name={row[2]}')

# 刪除 20700 股票
c.execute("DELETE FROM stocks WHERE stock_code LIKE '%20700%'")
conn.commit()
print(f'\nDeleted {c.rowcount} stock(s) with 20700')

# 顯示剩餘股票
c.execute('SELECT COUNT(*) FROM stocks')
print(f'Remaining stocks: {c.fetchone()[0]}')

conn.close()
