# 运行回测脚本
# 用于启动策略回测

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtest import Backtester
from backtest_config import START_DATE, END_DATE, INITIAL_CAPITAL, CAPITAL_PER_STOCK, STRATEGY_CONFIG, INDEX_CONFIG, TEST_STOCKS

# 移除了硬编码的股票列表，现在使用API通过板块名称获取指数成分股

def run_backtest():
    """运行回测"""
    print("===== 5日均线策略回测运行脚本 =====")
    print("正在启动回测...")
    print()
    
    # 添加详细的Python路径输出
    import sys
    print("当前Python路径:")
    for path in sys.path:
        print(f"  - {path}")
    print()
    
    try:
        # 获取目标指数配置
        target_index = STRATEGY_CONFIG.get('target_index', 'zz500')
        index_config = INDEX_CONFIG.get(target_index, {'code': '000905.SH', 'name': '中证500'})
        index_code = index_config['code']
        index_name = index_config['name']
        
        print(f"目标指数: {index_name} ({index_code})")
        
        # 创建回测器
        print("创建回测器...")
        backtester = Backtester(START_DATE, END_DATE, INITIAL_CAPITAL, CAPITAL_PER_STOCK)
        
        # 尝试使用API获取指数成分股
        print(f"\n===== 尝试使用API获取{index_name}成分股 ======")
        print(f"目标指数代码: {index_code}")
        print(f"目标指数名称: {index_name}")
        
        print("调用backtester.get_index_constituents()方法...")
        api_stocks = backtester.get_index_constituents(index_code)
        
        print(f"\nAPI返回的成分股数量: {len(api_stocks)}")
        print(f"API返回的成分股类型: {type(api_stocks)}")
        
        if len(api_stocks) > 0:
            print(f"API获取成功！获取到 {len(api_stocks)} 只{index_name}成分股")
            print(f"前10只成分股: {api_stocks[:10]}")
            print(f"最后10只成分股: {api_stocks[-10:]}")
            max_stocks = STRATEGY_CONFIG.get('max_stocks', 500)
            print(f"配置的最大股票数量: {max_stocks}")
            test_stocks = api_stocks[:max_stocks]  # 使用配置的最大股票数量
            print(f"实际使用的股票数量: {len(test_stocks)}")
        else:
            print(f"API获取失败或返回空列表，使用备用股票列表")
            print(f"备用股票列表: {TEST_STOCKS}")
            test_stocks = TEST_STOCKS
        
        print(f"\n最终使用的测试股票数量: {len(test_stocks)}")
        print(f"最终使用的测试股票列表: {test_stocks}")
        
        # 运行回测
        print("\n开始运行回测...")
        backtester.run_backtest(test_stocks)
        
        print("\n回测运行完成")
    except Exception as e:
        print(f"回测运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_backtest()
