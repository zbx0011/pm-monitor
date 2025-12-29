import sqlite3

def check_structure():
    conn = sqlite3.connect('precious_metals.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_name in tables:
        table = table_name[0]
        print(f"\n--- Table: {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
    conn.close()

if __name__ == "__main__":
    check_structure()
