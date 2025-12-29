import sqlite3
from database import DB_FILE

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
try:
    print("Checking PT2610-PLV2610...")
    c.execute("SELECT count(*), min(datetime), max(datetime) FROM platinum_pairs WHERE pair_name='2610-2610'")
    print(c.fetchall())
    
    print("\nChecking PT2610-PLN2607...")
    c.execute("SELECT count(*), min(datetime), max(datetime) FROM platinum_pairs WHERE pair_name='2610-2607'")
    print(c.fetchall())
    
    print("\nSample records for 2610-2607 (limit 5):")
    c.execute("SELECT * FROM platinum_pairs WHERE pair_name='2610-2607' ORDER BY datetime ASC LIMIT 5")
    for r in c.fetchall():
        print(r)
except Exception as e:
    print(e)
finally:
    conn.close()
