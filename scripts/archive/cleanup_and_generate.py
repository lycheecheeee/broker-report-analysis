import sqlite3

conn = sqlite3.connect('data/broker_analysis.db')
c = conn.cursor()

# 刪除 20700 股票
c.execute("DELETE FROM stocks WHERE stock_code LIKE '%20700%'")
print(f'Deleted {c.rowcount} invalid stock(s)')

# 刪除孤立的評級記錄
c.execute("DELETE FROM broker_ratings WHERE stock_id NOT IN (SELECT id FROM stocks)")
print(f'Deleted {c.rowcount} orphaned rating(s)')

conn.commit()

# 顯示統計
c.execute('SELECT COUNT(*) FROM broker_ratings')
print(f'Total ratings: {c.fetchone()[0]}')

c.execute('SELECT DISTINCT s.stock_code, s.company_name FROM broker_ratings br JOIN stocks s ON br.stock_id = s.id')
print('\nStocks in database:')
for row in c.fetchall():
    print(f'  {row[0]} - {row[1]}')

conn.close()
