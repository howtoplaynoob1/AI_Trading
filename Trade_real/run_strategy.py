# 5日均线策略运行脚本
# 启动实盘交易

import sys
import os
import time

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ma5_strategy import MA5Strategy
from config import QMT_PATH, ACCOUNT_ID, CAPITAL_PER_STOCK

# 默认股票池（可根据需要自定义）
DEFAULT_STOCK_POOL = [
    "000001.SZ", "000002.SZ", "000858.SZ", "600000.SH", "600036.SH",
    "601318.SH", "601888.SH", "600519.SH", "000333.SZ", "002594.SZ"
]


def main():
    """主函数"""
    print("=" * 70)
    print("5日均线策略 - 实盘交易")
    print("=" * 70)
    print()
    print(f"QMT路径: {QMT_PATH}")
    print(f"账户ID: {ACCOUNT_ID}")
    print(f"每只股票资金分配: {CAPITAL_PER_STOCK}元")
    print(f"股票池数量: {len(DEFAULT_STOCK_POOL)}")
    print()
    
    # 初始化策略
    strategy = MA5Strategy(QMT_PATH, ACCOUNT_ID, CAPITAL_PER_STOCK)
    
    # 运行策略
    strategy.run(DEFAULT_STOCK_POOL)
    
    print()
    print("=" * 70)
    print("策略运行完成")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n程序退出")
