# 测试xtquant数据目录和数据文件

import sys
import os

# 添加xtquant模块的路径到Python搜索路径
xtquant_parent_path = r"e:\TRAE\AI Coding\T_1\AI_Trading"
sys.path.append(xtquant_parent_path)

import xtquant
from xtquant import xtdata

print(f"成功导入xtquant模块: {xtquant.__file__}")

# 尝试连接到xtquant服务
try:
    xtdata.connect()
    print("成功连接到xtquant服务")
except Exception as e:
    print(f"连接xtquant服务失败: {e}")

# 测试获取数据文件路径
test_stock = '000001.SZ'
test_period = '5m'
test_date = '20180101'

print(f"\n测试获取 {test_stock} 的 {test_period} 数据文件路径...")

try:
    # 调用内部函数获取数据文件路径
    from xtquant import xtdata as xt
    path_result = xt._get_data_file_path([test_stock], test_period, test_date)
    print(f"数据文件路径: {path_result}")
    
    # 检查文件是否存在
    for stock_code, file_path in path_result.items():
        print(f"\n股票代码: {stock_code}")
        print(f"文件路径: {file_path}")
        if os.path.exists(file_path):
            print(f"文件存在！")
            file_size = os.path.getsize(file_path)
            print(f"文件大小: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            print(f"文件不存在！")
            
except Exception as e:
    print(f"获取数据文件路径时出错: {e}")
    import traceback
    traceback.print_exc()

# 测试获取实际数据
print(f"\n测试获取 {test_stock} 的 {test_period} 数据...")
try:
    data = xtdata.get_market_data(
        stock_list=[test_stock],
        field_list=['open', 'high', 'low', 'close', 'volume'],
        start_time='20180101093000',
        end_time='20180131150000',
        period=test_period
    )
    
    if data:
        print(f"成功获取数据！")
        print(f"数据字段: {list(data.keys())}")
        for field, df in data.items():
            print(f"\n字段: {field}")
            print(f"DataFrame形状: {df.shape}")
            if not df.empty:
                print(f"数据范围: {df.columns[0]} 到 {df.columns[-1]}")
            else:
                print("DataFrame为空！")
    else:
        print("获取数据失败，data为None或空")
        
except Exception as e:
    print(f"获取数据时出错: {e}")
    import traceback
    traceback.print_exc()

# 尝试断开连接
try:
    xtdata.disconnect()
    print("\n已断开xtquant服务连接")
except:
    pass