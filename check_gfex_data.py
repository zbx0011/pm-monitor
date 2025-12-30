import sqlite3

conn = sqlite3.connect('precious_metals.db')

# Check gfex_platinum_contracts schema
print("=== gfex_platinum_contracts schema ===")
cursor = conn.execute("PRAGMA table_info(gfex_platinum_contracts)")
for row in cursor:
    print(row)

# Check latest data
print("\n=== Latest 10 records ===")
cursor = conn.execute("SELECT * FROM gfex_platinum_contracts ORDER BY datetime DESC LIMIT 10")
for row in cursor:
    print(row)

# Check today's data
print("\n=== Today's data count ===")
cursor = conn.execute("SELECT contract, COUNT(*) FROM gfex_platinum_contracts WHERE datetime LIKE '2025-12-29%' GROUP BY contract")
for row in cursor:
    print(row)

# Check first record of today
print("\n=== First record of today per contract ===")
cursor = conn.execute("""
    SELECT contract, MIN(datetime), close FROM gfex_platinum_contracts 
    WHERE datetime LIKE '2025-12-29%' 
    GROUP BY contract
""")
for row in cursor:
    print(row)

conn.close()
