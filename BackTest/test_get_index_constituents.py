# 测试get_index_constituents方法
# 用于测试获取指数成分股的功能

import sys
import os

# 添加AI_Trading目录到路径
aitrading_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(aitrading_dir)
print(f"添加AI_Trading目录到路径: {aitrading_dir}")

# 导入Backtester类
from backtest import Backtester
from backtest_config import START_DATE, END_DATE, INITIAL_CAPITAL, CAPITAL_PER_STOCK

# 创建Backtester实例
backtester = Backtester(START_DATE, END_DATE, INITIAL_CAPITAL, CAPITAL_PER_STOCK)

# 测试获取中证500成分股
print("\n===== 测试获取中证500成分股 =====")
zz500_stocks = backtester.get_index_constituents('000905.SH')
print(f"中证500成分股数量: {len(zz500_stocks)}")
print(f"中证500成分股: {zz500_stocks}")

# 测试获取沪深300成分股
print("\n===== 测试获取沪深300成分股 =====")
hs300_stocks = backtester.get_index_constituents('000300.SH')
print(f"沪深300成分股数量: {len(hs300_stocks)}")
print(f"沪深300成分股: {hs300_stocks}")

# 测试获取上证50成分股
print("\n===== 测试获取上证50成分股 =====")
sz50_stocks = backtester.get_index_constituents('000016.SH')
print(f"上证50成分股数量: {len(sz50_stocks)}")
print(f"上证50成分股: {sz50_stocks}")

print("\n测试完成")
