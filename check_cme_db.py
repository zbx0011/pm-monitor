
import sqlite3

def check_data():
    conn = sqlite3.connect('precious_metals.db')
    cursor = conn.cursor()
    
    # Check PLJ2026
    print("\nRecent PLJ2026 data in cme_platinum_contracts:")
    try:
        cursor.execute("SELECT datetime, close, contract FROM cme_platinum_contracts WHERE contract='PLJ2026' ORDER BY datetime DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error querying PLJ2026: {e}")

    # Check PLF2026
    print("\nRecent PLF2026 data in cme_platinum_contracts:")
    try:
        cursor.execute("SELECT datetime, close, contract FROM cme_platinum_contracts WHERE contract='PLF2026' ORDER BY datetime DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error querying PLF2026: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_data()
