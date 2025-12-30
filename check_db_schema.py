import sqlite3

conn = sqlite3.connect('precious_metals.db')

# List all tables
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor]
print("Tables in database:", tables)

# Check if there's any GFEX table
for t in tables:
    print(f"\n--- {t} ---")
    cursor = conn.execute(f"PRAGMA table_info({t})")
    cols = [row[1] for row in cursor]
    print(f"Columns: {cols}")
    
    cursor = conn.execute(f"SELECT COUNT(*) FROM {t}")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")

conn.close()
