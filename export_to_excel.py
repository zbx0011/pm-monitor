"""
导出铂金钯金价差数据到Excel
"""
import json
import pandas as pd
from datetime import datetime
import os

def export_to_excel():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 读取铂金数据
    pt_file = os.path.join(script_dir, 'platinum_spread_analysis.json')
    pd_file = os.path.join(script_dir, 'palladium_spread_analysis.json')
    
    with pd.ExcelWriter(os.path.join(script_dir, 'precious_metals_data.xlsx'), engine='openpyxl') as writer:
        
        # 导出铂金数据
        if os.path.exists(pt_file):
            with open(pt_file, 'r', encoding='utf-8') as f:
                pt_data = json.load(f)
            
            # 历史数据
            pt_history = pd.DataFrame(pt_data['history'])
            pt_history.to_excel(writer, sheet_name='铂金历史', index=False)
            
            # 当前数据
            pt_current = pd.DataFrame([pt_data['current']])
            pt_current.insert(0, 'update_time', pt_data['update_time'])
            pt_current.insert(1, 'gfex_contract', pt_data['contracts']['gfex'])
            pt_current.insert(2, 'cme_contract', pt_data['contracts']['cme'])
            pt_current.to_excel(writer, sheet_name='铂金当前', index=False)
            
            print(f"✓ 铂金数据已导出 ({len(pt_history)} 条历史记录)")
        
        # 导出钯金数据
        if os.path.exists(pd_file):
            with open(pd_file, 'r', encoding='utf-8') as f:
                pd_data = json.load(f)
            
            # 历史数据
            pd_history = pd.DataFrame(pd_data['history'])
            pd_history.to_excel(writer, sheet_name='钯金历史', index=False)
            
            # 当前数据
            pd_current = pd.DataFrame([pd_data['current']])
            pd_current.insert(0, 'update_time', pd_data['update_time'])
            pd_current.insert(1, 'gfex_contract', pd_data['contracts']['gfex'])
            pd_current.insert(2, 'cme_contract', pd_data['contracts']['cme'])
            pd_current.to_excel(writer, sheet_name='钯金当前', index=False)
            
            print(f"✓ 钯金数据已导出 ({len(pd_history)} 条历史记录)")
        
        # 导出all_pairs数据
        pt_pairs_file = os.path.join(script_dir, 'platinum_all_pairs.json')
        if os.path.exists(pt_pairs_file):
            with open(pt_pairs_file, 'r', encoding='utf-8') as f:
                pairs_data = json.load(f)
            
            for pair_name, pair_info in pairs_data['pairs'].items():
                df = pd.DataFrame(pair_info['history'])
                df.insert(0, 'gfex_contract', pair_info['gfex_contract'])
                df.insert(1, 'cme_contract', pair_info['cme_contract'])
                sheet_name = f'铂金_{pair_name}'[:31]  # Excel sheet名称最长31字符
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"✓ {sheet_name} 已导出 ({len(df)} 条)")
        
        pd_pairs_file = os.path.join(script_dir, 'palladium_all_pairs.json')
        if os.path.exists(pd_pairs_file):
            with open(pd_pairs_file, 'r', encoding='utf-8') as f:
                pairs_data = json.load(f)
            
            for pair_name, pair_info in pairs_data['pairs'].items():
                df = pd.DataFrame(pair_info['history'])
                df.insert(0, 'gfex_contract', pair_info['gfex_contract'])
                df.insert(1, 'cme_contract', pair_info['cme_contract'])
                sheet_name = f'钯金_{pair_name}'[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"✓ {sheet_name} 已导出 ({len(df)} 条)")
    
    print(f"\n✓ 数据已保存到 precious_metals_data.xlsx")

if __name__ == "__main__":
    export_to_excel()
