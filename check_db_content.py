
import sqlite3

def check_data():
    conn = sqlite3.connect('precious_metals.db')
    cursor = conn.cursor()
    
    # We found columns: id, datetime, pt_gfex, pt_cme_usd, ...
    print("\nRecent entries (Top 5):")
    try:
        cursor.execute("SELECT datetime, pt_cme_usd, pd_cme_usd, exchange_rate FROM price_snapshots ORDER BY datetime DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_data()
