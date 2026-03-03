# BackTest - 回测模块

## 项目结构

```
BackTest/
├── backtest.py                  # 回测主程序
├── backtest_config.py           # 回测配置
├── backtest_daily_values.csv    # 回测每日价值记录
├── backtest_trades.csv          # 回测交易记录
├── run_backtest.py              # 回测启动脚本
├── test_get_index_constituents.py # 指数成分股获取测试
├── test_xtquant.py              # xtquant库测试
└── README.md                    # 本文件
```

## 文件说明

### backtest.py
回测核心程序，包含 `Backtester` 类实现：
- 数据加载（历史行情数据）
- 股票数据处理和技术指标计算
- 选股逻辑实现
- 买卖信号生成和执行
- 费用计算和扣除
- 回测结果统计和可视化

### backtest_config.py
回测配置文件，包含：
- 回测时间范围（START_DATE, END_DATE）
- 初始资金和单只股票资金分配
- 指数配置（沪深300、中证500等）
- 策略配置参数
- 测试股票列表

### run_backtest.py
回测启动脚本，用于：
- 导入配置和回测器
- 设置回测参数
- 执行回测程序
- 输出回测结果

## 使用方法

### 基本使用

```python
from backtest import Backtester
from backtest_config import START_DATE, END_DATE, INITIAL_CAPITAL, CAPITAL_PER_STOCK

# 创建回测器
backtester = Backtester(START_DATE, END_DATE, INITIAL_CAPITAL, CAPITAL_PER_STOCK)

# 定义股票池
stock_list = ["000001.SZ", "000002.SZ", "600000.SH", ...]

# 运行回测
backtester.run_backtest(stock_list)
```

### 命令行运行

```bash
python run_backtest.py
```

## 回测结果

回测完成后会生成以下文件：

### CSV文件
- `backtest_daily_values.csv` - 每日资产价值
  - date: 交易日期
  - capital: 现金
  - portfolio_value: 持仓价值
  - total_value: 总资产
  - return: 累计收益率(%)

- `backtest_trades.csv` - 交易记录
  - date: 交易日期
  - stock_code: 股票代码
  - action: 买入/卖出
  - price: 交易价格
  - quantity: 交易数量
  - amount: 交易金额
  - fee: 手续费
  - reason: 卖出原因

### 图表文件
- `backtest_combined_result.png` - 综合结果图（资金曲线 + 收益率 + 报告）
- `backtest_equity_curve.png` - 资金曲线图
- `backtest_return_curve.png` - 收益率曲线图

## 费用计算

### 买入费用
每1万元收取3元，不满1万仍收3元
```
buy_cost = 股价 × 数量
buy_fee = calculate_buy_fee(buy_cost)
total_cost = buy_cost + buy_fee
```

### 卖出费用
印花税（5元/万）+ 交易费（3元/万），不满1万仍收全额
```
proceeds = 股价 × 数量
sell_fee = calculate_sell_fee(proceeds)
net_proceeds = proceeds - sell_fee
```

## 策略逻辑

### 选股条件
- 股价 ≥ 5日均线
- 前10日涨幅 > 12%

### 买入条件
- 股票被选中
- 前10日最高价 ≤ 当前价格
- 当日成交量 ≥ 前一日成交量
- 前10日涨幅 > 15%

### 卖出条件
1. 股价 < 5日均线（跌破均线）
2. 收益率 > 6%（止盈）
3. 亏损 > 6%（止损）
4. 股价 < 前3日最低价
5. 持仓时间1~3天（早退）

## 回测报告

回测完成时会输出统计报告，包括：
- 初始资金
- 最终资金
- 总收益率(%)
- 年化收益率(%)
- 最大回撤(%)
- 交易次数（买入/卖出）
- 回测时间范围

## 配置调整

编辑 `backtest_config.py` 可以调整：
- 回测时间范围
- 初始资金
- 单只股票资金分配
- 目标指数（沪深300/中证500等）
- 选股和卖出参数

## 注意事项

1. 回测需要完整的历史行情数据
2. 首次运行可能需要下载较大的数据文件
3. 回测结果不代表未来实际收益
4. 建议多次测试不同参数组合
5. 关注回测周期长度和数据完整性

## 改进建议

1. 添加更多技术指标
2. 实现多因子选股
3. 添加滑点和部分成交模拟
4. 优化参数搜索
5. 支持更多输出格式
6. 添加对比基准指数功能
