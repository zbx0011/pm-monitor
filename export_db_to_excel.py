import sqlite3
import pandas as pd
import os

DB_FILE = 'precious_metals.db'
OUTPUT_FILE = 'precious_metals_data.xlsx'

def export_to_excel():
    print(f"Reading database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    
    # 我们关注这两个新表
    target_tables = ['platinum_pairs', 'palladium_pairs']
    
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        for table in target_tables:
            print(f"Exporting table: {table}")
            
            try:
                # 获取该表中的所有 pair_name
                query_pairs = f"SELECT DISTINCT pair_name FROM {table}"
                df_pairs = pd.read_sql_query(query_pairs, conn)
                
                pairs = df_pairs['pair_name'].tolist()
                print(f"  Found pairs: {pairs}")
                
                for pair in pairs:
                    # 读取每个配对的数据
                    query = f"SELECT * FROM {table} WHERE pair_name = '{pair}' ORDER BY datetime DESC"
                    df = pd.read_sql_query(query, conn)
                    
                    # Sheet name naming: Pt_2610-2601 or Pd_2606-2604
                    # Pt/Pd prefix
                    prefix = "Pt" if "platinum" in table else "Pd"
                    sheet_name = f"{prefix}_{pair}"
                    
                    # Ensure valid sheet name length (max 31)
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                        
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  Saved sheet: {sheet_name} ({len(df)} rows)")
            except Exception as e:
                print(f"  Error exporting {table}: {e}")

    conn.close()
    print(f"\nCreated: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    export_to_excel()
