"""测试获取广期所具体合约数据"""
import akshare as ak

print("=" * 60)
print("测试获取广期所具体合约数据")
print("=" * 60)

# 尝试获取PT2610具体合约日线数据
print("\n【方法1: futures_zh_daily_sina - 尝试PT2610】")
try:
    df = ak.futures_zh_daily_sina(symbol='PT2610')
    print(f"获取到 {len(df)} 条数据")
    print(df.tail(5))
except Exception as e:
    print(f"失败: {e}")

# 尝试获取PD2606具体合约日线数据
print("\n【方法2: futures_zh_daily_sina - 尝试PD2606】")
try:
    df = ak.futures_zh_daily_sina(symbol='PD2606')
    print(f"获取到 {len(df)} 条数据")
    print(df.tail(5))
except Exception as e:
    print(f"失败: {e}")

# 尝试获取广期所期货实时行情
print("\n【方法3: futures_gfex_quote - 广期所实时行情】")
try:
    df = ak.futures_gfex_quote()
    print(df)
except Exception as e:
    print(f"失败: {e}")

# 尝试其他接口
print("\n【方法4: option_cffex_pt_quote - 检查是否有类似接口】")
try:
    # 列出包含 gfex 或 PT 的函数
    funcs = [f for f in dir(ak) if 'gfex' in f.lower() or ('futures' in f.lower() and 'pt' in f.lower())]
    print("相关函数:", funcs[:10])
except Exception as e:
    print(f"失败: {e}")
