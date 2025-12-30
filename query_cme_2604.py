import sqlite3
conn = sqlite3.connect('precious_metals.db')
c = conn.cursor()
c.execute("SELECT datetime, cme_usd, pair_name FROM platinum_pairs WHERE cme_contract = 'PLJ2026' ORDER BY datetime DESC LIMIT 5")
print("时间                  | CME价格(USD) | 配对")
print("-" * 50)
for r in c.fetchall():
    print(f"{r[0]:<20} | {r[1]:>12.2f} | {r[2]}")
conn.close()
