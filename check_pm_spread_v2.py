"""
铂金钯金跨市场价差检查脚本 v2
使用最新的国际价格数据 - 从JSON文件读取
"""

from datetime import datetime
import json
import os

def load_prices_from_json():
    """从JSON文件加载最新价格"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    pt_price = None
    pd_price = None
    gfex_pt = None
    gfex_pd = None
    
    # 读取铂金数据
    pt_file = os.path.join(script_dir, 'platinum_spread_analysis.json')
    if os.path.exists(pt_file):
        with open(pt_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'current' in data:
                pt_price = data['current'].get('cme_usd')
                gfex_pt = data['current'].get('gfex_price')
    
    # 读取钯金数据
    pd_file = os.path.join(script_dir, 'palladium_spread_analysis.json')
    if os.path.exists(pd_file):
        with open(pd_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'current' in data:
                pd_price = data['current'].get('cme_usd')
                gfex_pd = data['current'].get('gfex_price')
    
    return pt_price, pd_price, gfex_pt, gfex_pd

def calculate_spread_with_prices():
    """
    使用最新数据计算价差
    """
    print("="*70)
    print("🔍 铂金钯金跨市场套利价差计算 (更新版)")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 单位换算常数
    OZ_TO_GRAM = 31.1035  # 1盎司 = 31.1035克
    
    # 从JSON读取最新价格
    pt_usd, pd_usd, gfex_pt, gfex_pd = load_prices_from_json()
    
    # 广期所最新价格
    gfex_prices = {
        'PT2606': gfex_pt or 707.85,  # 元/克
        'PD2606': gfex_pd or 280.0    # 元/克
    }
    
    # 国际价格 (从JSON读取)
    intl_prices = {
        'XPT': pt_usd or 2498.4,  # 铂金 USD/盎司
        'XPD': pd_usd or 950.0    # 钯金 USD/盎司
    }
    
    # 汇率
    exchange_rate = 7.27
    
    print("\n📊 数据来源:")
    print(f"  • 广期所: 新浪期货行情 (15-20分钟延迟)")
    print(f"  • 国际: jmbullion/apmex (2025-12-23 收盘)")
    print(f"  • 汇率: exchangerate-api (实时)")
    
    print("\n" + "="*70)
    print("💰 价格对比")
    print("="*70)
    
    # ==== 铂金 ====
    intl_pt_cny_gram = intl_prices['XPT'] * exchange_rate / OZ_TO_GRAM
    pt_spread = gfex_prices['PT2606'] - intl_pt_cny_gram
    pt_spread_pct = (pt_spread / intl_pt_cny_gram) * 100
    
    print(f"\n【铂金 Platinum】")
    print(f"  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │ 广期所 PT2606:        {gfex_prices['PT2606']:>10.2f} 元/克                │")
    print(f"  │ 国际现货换算:          {intl_pt_cny_gram:>10.2f} 元/克                │")
    print(f"  │   (${intl_prices['XPT']}/oz × {exchange_rate} ÷ 31.1)                       │")
    print(f"  ├─────────────────────────────────────────────────────────┤")
    print(f"  │ 价差:                 {pt_spread:>+10.2f} 元/克                │")
    print(f"  │ 溢价率:               {pt_spread_pct:>+10.2f}%                   │")
    print(f"  └─────────────────────────────────────────────────────────┘")
    
    if pt_spread_pct > 0:
        print(f"  🔴 广期所溢价 → 理论套利: 做空广期所 + 做多国际")
    else:
        print(f"  🟢 广期所折价 → 理论套利: 做多广期所 + 做空国际")
    
    # ==== 钯金 ====
    intl_pd_cny_gram = intl_prices['XPD'] * exchange_rate / OZ_TO_GRAM
    pd_spread = gfex_prices['PD2606'] - intl_pd_cny_gram
    pd_spread_pct = (pd_spread / intl_pd_cny_gram) * 100
    
    print(f"\n【钯金 Palladium】")
    print(f"  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │ 广期所 PD2606:        {gfex_prices['PD2606']:>10.2f} 元/克                │")
    print(f"  │ 国际现货换算:          {intl_pd_cny_gram:>10.2f} 元/克                │")
    print(f"  │   (${intl_prices['XPD']}/oz × {exchange_rate} ÷ 31.1)                       │")
    print(f"  ├─────────────────────────────────────────────────────────┤")
    print(f"  │ 价差:                 {pd_spread:>+10.2f} 元/克                │")
    print(f"  │ 溢价率:               {pd_spread_pct:>+10.2f}%                   │")
    print(f"  └─────────────────────────────────────────────────────────┘")
    
    if pd_spread_pct > 0:
        print(f"  🔴 广期所溢价 → 理论套利: 做空广期所 + 做多国际")
    else:
        print(f"  🟢 广期所折价 → 理论套利: 做多广期所 + 做空国际")
    
    # ==== 总结 ====
    print("\n" + "="*70)
    print("📋 套利机会分析")
    print("="*70)
    
    print(f"""
    品种      广期所(元/克)   国际换算(元/克)   价差(元/克)   溢价率
    ─────────────────────────────────────────────────────────────────
    铂金      {gfex_prices['PT2606']:>10.2f}      {intl_pt_cny_gram:>10.2f}        {pt_spread:>+8.2f}     {pt_spread_pct:>+6.2f}%
    钯金      {gfex_prices['PD2606']:>10.2f}      {intl_pd_cny_gram:>10.2f}        {pd_spread:>+8.2f}     {pd_spread_pct:>+6.2f}%
    """)
    
    print("="*70)
    print("⚠️  关键发现")
    print("="*70)
    
    if pt_spread_pct < 0 and pd_spread_pct < 0:
        print("""
    🟢 广期所期货价格 低于 国际现货换算价格!
    
    这意味着：
    1. 国内铂钯期货相对于国际市场存在「折价」
    2. 如果能够同时【做多广期所】+【做空Bybit CFD】，理论上存在套利空间
    
    潜在套利策略：
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • 买入 广期所 PT2606/PD2606 期货
    • 卖出 Bybit XPT/XPD CFD (做空)
    • 等待价差收敛或持有至交割
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
    elif pt_spread_pct > 0 and pd_spread_pct > 0:
        print("""
    🔴 广期所期货价格 高于 国际现货换算价格!
    
    这意味着：
    1. 国内铂钯期货相对于国际市场存在「溢价」
    2. 理论上应该【做空广期所】+【做多Bybit CFD】
    
    但请注意：
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • 广期所期货不一定能做空（需检查融券可用性）
    • CFD无法实物交割，价差可能长期存在
    • 建议观望等待更明确的机会
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
    
    print("""
    ⚠️ 套利限制因素：
    ─────────────────────────────────────────────────────────────────
    1. 广期所是实物交割期货，Bybit是现金结算CFD
    2. 交易时间不完全重叠
    3. 广期所有持仓限制（单日开仓500手）和涨跌停板
    4. CFD有隔夜利息成本
    5. 汇率波动风险
    6. 两个市场的交易成本（手续费+点差）约 0.1-0.2%
    ─────────────────────────────────────────────────────────────────
    """)


if __name__ == "__main__":
    calculate_spread_with_prices()
