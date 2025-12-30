import sqlite3
conn = sqlite3.connect('precious_metals.db')
c = conn.cursor()
c.execute("SELECT datetime, close, contract FROM cme_platinum_contracts WHERE contract='PLJ2026' ORDER BY datetime DESC LIMIT 5")
print("CME PLJ2026 原始数据（最新5条）:")
print("时间                  | 收盘价(USD) | 合约")
print("-" * 50)
for r in c.fetchall():
    print(f"{r[0]:<20} | {r[1]:>11.2f} | {r[2]}")
conn.close()
