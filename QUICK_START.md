# 快速参考指南

## 📂 项目结构速览

```
AI_Trading/
├── BackTest/                  # 回测模块
│   ├── backtest.py           # 回测核心程序
│   ├── backtest_config.py    # 回测配置
│   └── run_backtest.py       # 回测启动
│
├── Trade_real/               # 实盘交易模块
│   ├── config.py             # 配置文件
│   ├── ma5_strategy.py       # 交易策略（核心）
│   └── run_strategy.py       # 启动脚本
│
├── xtquant/                  # 交易接口库
├── README.md                 # 项目总体说明
└── UPDATE_2026-01-27.md      # 本次更新说明
```

## 🚀 快速开始

### 步骤1: 配置
```python
# 编辑 Trade_real/config.py
QMT_PATH = r"Your_QMT_Installation_Path"
ACCOUNT_ID = "Your_Account_ID"
CAPITAL_PER_STOCK = 10000
```

### 步骤2: 运行实盘
```bash
cd Trade_real
python run_strategy.py
```

### 步骤3: 运行回测
```bash
cd BackTest
python run_backtest.py
```

## 📊 关键配置参数

### Trade_real/config.py
```python
QMT_PATH = r"E:\QuantT\..."           # QMT安装路径
ACCOUNT_ID = "Your_Account_ID"          # 账户ID
CAPITAL_PER_STOCK = 10000              # 单只股票资金(元)
```

建议：用 `Trade_real/config.example.py` 复制生成本地 `Trade_real/config.py`，并保持 `config.py` 不提交到 GitHub。

### BackTest/backtest_config.py
```python
START_DATE = '20160101'                # 回测开始日期
END_DATE = '20231231'                  # 回测结束日期
INITIAL_CAPITAL = 1000000              # 初始资金(元)
CAPITAL_PER_STOCK = 10000              # 单只股票资金(元)
```

## 💰 费用计算公式

### 买入费用
```
数量 = amount / 10000
余数 = amount % 10000
费用 = 数量 × 3 + (余数 > 0 ? 3 : 0)

示例：
- 买入 10,000元 → 费用 = 3元
- 买入 15,000元 → 费用 = 6元（3 + 3）
- 买入 50,000元 → 费用 = 15元（3 × 5）
```

### 卖出费用
```
数量 = amount / 10000
余数 = amount % 10000
印花税 = 数量 × 5 + (余数 > 0 ? 5 : 0)
交易费 = 数量 × 3 + (余数 > 0 ? 3 : 0)
总费用 = 印花税 + 交易费

示例：
- 卖出 10,000元 → 费用 = 8元（5 + 3）
- 卖出 15,000元 → 费用 = 16元（8 + 8）
- 卖出 50,000元 → 费用 = 40元（8 × 5）
```

## 📈 交易策略

### 选股规则
✅ 股价 > 5日均线

### 买入规则
✅ 股票被选中  
✅ 未持仓过该股票  
✅ 资金充足

### 卖出规则
❌ 股价 < 5日均线（跌破均线）  
❌ 收益率 > 6%（止盈）  
❌ 亏损 > 5%（止损）

## 🔄 主要方法

### MA5Strategy类
```python
# 初始化
strategy = MA5Strategy(qmt_path, account_id, capital_per_stock)

# 核心方法
strategy.init_trader()                  # 初始化连接
strategy.get_account_asset()            # 查询资产
strategy.select_stocks(stock_pool)      # 选股
strategy.buy_stocks(selected_stocks)    # 买入
strategy.sell_stocks()                  # 卖出
strategy.run(stock_pool)                # 完整运行

# 查询方法
strategy.get_positions()                # 查询持仓
strategy.get_market_data(code)          # 实时行情
strategy.get_historical_data(code, days) # 历史数据

# 计算方法
strategy.calculate_ma(code, period)     # 移动平均线
strategy.calculate_buy_fee(amount)      # 买入费用
strategy.calculate_sell_fee(amount)     # 卖出费用
```

## 🐛 常见问题

### Q: 如何修改选股条件？
A: 编辑 `ma5_strategy.py` 中的 `select_stocks()` 方法

### Q: 如何修改卖出条件？
A: 编辑 `ma5_strategy.py` 中的 `sell_stocks()` 和 `execute_sell()` 方法

### Q: 如何添加新的股票池？
A: 在 `run_strategy.py` 中修改 `DEFAULT_STOCK_POOL` 或传入自定义列表

### Q: 如何调整资金配置？
A: 修改 `config.py` 中的 `CAPITAL_PER_STOCK` 参数

### Q: 回测结果在哪里？
A: `BackTest/` 目录中的 CSV 文件和 PNG 图表

### Q: 如何查看交易日志？
A: 查看控制台输出（已集成日志系统）

## 📋 检查清单

使用前确认：
- [ ] QMT平台已安装
- [ ] 账户ID已配置
- [ ] QMT路径正确
- [ ] Python版本 >= 3.8
- [ ] 已安装依赖包（pandas、numpy、matplotlib）
- [ ] 网络连接正常

## ⚡ 快速调试

### 测试连接
```python
from ma5_strategy import MA5Strategy
from config import QMT_PATH, ACCOUNT_ID, CAPITAL_PER_STOCK

strategy = MA5Strategy(QMT_PATH, ACCOUNT_ID, CAPITAL_PER_STOCK)
if strategy.init_trader():
    print("✅ 连接成功")
    strategy.get_account_info()
else:
    print("❌ 连接失败")
```

### 测试行情数据
```python
quote = strategy.get_market_data("000001.SZ")
if quote:
    print("✅ 可以获取行情数据")
else:
    print("❌ 无法获取行情数据")
```

### 测试策略选股
```python
stock_pool = ["000001.SZ", "000002.SZ", "600000.SH"]
selected = strategy.select_stocks(stock_pool)
print(f"选中 {len(selected)} 只股票: {selected}")
```

## 📞 需要帮助？

1. 查看详细文档：
   - `README.md` - 项目总体说明
   - `Trade_real/README.md` - 实盘模块指南
   - `BackTest/README.md` - 回测模块指南

2. 查看更新说明：
   - `UPDATE_2026-01-27.md` - 最新更新内容

3. 查看代码注释：
   - `ma5_strategy.py` - 每个方法都有完整注释

## 🎯 优化建议

1. **参数优化** - 尝试不同的MA周期
2. **选股改进** - 添加更多技术指标
3. **风险控制** - 调整止盈止损参数
4. **回测验证** - 充分测试新策略
5. **记录分析** - 保留交易日志，定期复盘

---

**快速参考完成！祝交易顺利！🚀**

*最后更新: 2026-01-27*
