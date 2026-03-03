# 测试xtquant API
# 用于测试xtdata.get_stock_list_in_sector函数的功能

import sys
import os

# 添加xtquant模块路径（父目录）
xtquant_parent_path = r"e:\TRAE\AI Coding\T_1\AI_Trading"
print(f"添加xtquant父目录路径: {xtquant_parent_path}")
sys.path.append(xtquant_parent_path)
print(f"Python路径: {sys.path}")

print("===== 测试xtquant API =====")

try:
    print("1. 尝试导入xtquant...")
    import xtquant
    print(f"xtquant模块路径: {xtquant.__file__}")
    from xtquant import xtdata
    print("成功导入xtquant.xtdata")
    
    # 测试xtdata是否可用
    print("2. 测试xtdata是否可用...")
    # 尝试获取版本信息或其他基本信息
    print("xtdata模块可用")
    
    # 测试获取板块列表
    print("3. 测试获取板块列表...")
    sector_list = xtdata.get_sector_list()
    print(f"板块列表数量: {len(sector_list)}")
    print(f"前20个板块: {sector_list[:20]}")
    
    # 测试获取中证500成分股
    print("4. 测试获取中证500成分股...")
    zz500_stocks = xtdata.get_stock_list_in_sector("中证500")
    print(f"中证500成分股类型: {type(zz500_stocks)}")
    print(f"中证500成分股数量: {len(zz500_stocks)}")
    if isinstance(zz500_stocks, list) and len(zz500_stocks) > 0:
        print(f"前10只中证500成分股: {zz500_stocks[:10]}")
    
    # 测试获取沪深300成分股
    print("5. 测试获取沪深300成分股...")
    hs300_stocks = xtdata.get_stock_list_in_sector("沪深300")
    print(f"沪深300成分股类型: {type(hs300_stocks)}")
    print(f"沪深300成分股数量: {len(hs300_stocks)}")
    if isinstance(hs300_stocks, list) and len(hs300_stocks) > 0:
        print(f"前10只沪深300成分股: {hs300_stocks[:10]}")
        
except ImportError as e:
    print(f"导入xtquant失败: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()

print("===== 测试完成 =====")
