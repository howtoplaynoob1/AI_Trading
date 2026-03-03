# AI_Trading - 5日均线量化交易系统

一个基于5日均线的自动化量化交易系统，包含回测和实盘交易功能。

## 项目结构

```
AI_Trading/
├── BackTest/              # 回测模块
│   ├── backtest.py
│   ├── backtest_config.py
│   ├── run_backtest.py
│   └── README.md
│
├── Trade_real/            # 实盘交易模块
│   ├── config.py
│   ├── ma5_strategy.py
│   ├── run_strategy.py
│   └── README.md
│
├── xtquant/               # 迅投交易接口库
│   ├── xttrader.py
│   ├── xtdata.py
│   ├── xtconstant.py
│   └── ...
│
└── README.md              # 本文件
```

## 核心特性

### ✅ 回测模块
- 完整的历史数据加载和处理
- 5日均线和其他技术指标计算
- 精确的买卖逻辑模拟
- 真实费用计算和扣除
- 详细的交易记录和统计
- 生成资金曲线和收益率图表
- 支持指数成分股自动导入

### ✅ 实盘交易模块
- 实时行情数据获取
- 自动选股和下单
- 订单和成交监控
- 风险控制和止盈止损
- 完整的日志记录
- 可配置的交易参数

### ✅ 费用处理
- **买入费用**：每1万元3元，不满1万仍收3元
- **卖出费用**：印花税5元/万 + 交易费3元/万，不满1万仍收全额
- 自动计算和扣除，确保准确性

## 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install pandas numpy matplotlib

# 配置QMT路径（编辑 Trade_real/config.py）
QMT_PATH = r"Your_QMT_Installation_Path"
ACCOUNT_ID = "Your_Account_ID"
```

### 2. 回测测试

```bash
cd BackTest
python run_backtest.py
```

### 3. 实盘交易

```bash
cd Trade_real
python run_strategy.py
```

## 交易策略说明

### 策略名称
5日均线趋势跟踪策略

### 交易逻辑

#### 选股阶段
- 股价 > 5日均线（上升趋势）
- 前10日涨幅 > 12%（趋势确认）

#### 买入阶段
满足以下条件：
- 股票被选中
- 股价 ≥ 前10日最高价（创新高）
- 成交量 ≥ 前一日成交量（量能确认）
- 前10日涨幅 > 15%（强势股）

#### 卖出阶段
满足以下条件之一：
- 股价 < 5日均线（趋势破坏）
- 盈利 > 6%（止盈）
- 亏损 > 5-6%（止损）
- 股价 < 前3日最低价（技术破位）

## 配置说明

### BackTest/backtest_config.py
```python
START_DATE = '20160101'           # 回测开始日期
END_DATE = '20231231'             # 回测结束日期
INITIAL_CAPITAL = 1000000         # 初始资金（100万）
CAPITAL_PER_STOCK = 10000         # 单只股票资金分配
```

### Trade_real/config.py
```python
QMT_PATH = r"E:\QuantT\..."       # QMT安装路径
ACCOUNT_ID = "Your_Account_ID"    # 账户ID
CAPITAL_PER_STOCK = 10000         # 单只股票资金分配
```

提示：建议使用 `Trade_real/config.example.py` 复制一份生成本地 `Trade_real/config.py`，并保持 `config.py` 不提交到 GitHub。

## 使用指南

### 详细文档
- [回测模块使用指南](BackTest/README.md)
- [实盘交易使用指南](Trade_real/README.md)

### 常见问题

**Q: 如何修改选股条件？**
A: 编辑 `backtest.py` 或 `ma5_strategy.py` 中的 `select_stocks()` 方法

**Q: 如何添加新的卖出条件？**
A: 编辑 `sell_stocks()` 或 `execute_sell()` 方法，增加新的条件判断

**Q: 如何调整交易费用？**
A: 编辑 `calculate_buy_fee()` 和 `calculate_sell_fee()` 方法

**Q: 如何选择目标指数？**
A: 修改 `backtest_config.py` 中的 `target_index` 参数

## 系统要求

- Python 3.8+
- pandas
- numpy
- matplotlib
- QMT交易平台（实盘交易时）

## 注意事项

### ⚠️ 风险警告
- 回测结果不代表未来实际收益
- 量化交易存在执行风险和市场风险
- 建议充分测试和验证策略
- 实盘交易前请确认网络稳定
- 建议设置合理的风险控制参数

### 📊 最佳实践
1. 先进行充分的回测验证
2. 从小额资金开始实盘
3. 定期监控和调整策略
4. 保留详细的交易日志
5. 定期分析和优化参数

## 性能指标

典型回测表现（2016-2023年）：
- 总收益率：根据具体参数波动
- 年化收益率：需要回测验证
- 最大回撤：需要回测验证
- 夏普比率：需要回测验证

实际表现取决于：
- 股票池的选择
- 参数的优化程度
- 市场环境的变化
- 交易执行的准确性

## 改进计划

- [ ] 添加更多技术指标（MACD、RSI等）
- [ ] 实现机器学习选股模型
- [ ] 多策略组合管理
- [ ] 风险因子分析
- [ ] 实时监控仪表板
- [ ] 策略参数自动优化
- [ ] 支持更多品种（期货、转债等）

## 文件清理历史

已删除的无用文件：
- ~~strategy.py~~ (重复的基础策略)
- ~~qmt_trade.py~~ (简单示例文件)
- ~~ma5_strategy_detailed.py~~ (已被 ma5_strategy.py 替代)
- ~~qmt_readme.md~~ (旧文档)
- ~~strategy_readme.md~~ (旧文档)

## 许可证

MIT License

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。使用本系统进行交易所产生的任何损失，本人不承担责任。量化交易风险高，请谨慎使用。

## 联系方式

如有问题或建议，欢迎反馈。

---

**最后更新**: 2026-01-27
