# 策略配置文件（示例）
#
# 使用方法：
# 1) 复制本文件为 config.py
# 2) 按你的本机环境填写 QMT_PATH / ACCOUNT_ID

# QMT安装路径（示例）
QMT_PATH = r"Your_QMT_Installation_Path"

# 账户ID（示例）
ACCOUNT_ID = "Your_Account_ID"

# 每只股票的资金分配
CAPITAL_PER_STOCK = 10000

# 选股参数
SELECTION_PARAMS = {
    "min_market_cap": 200,  # 最小市值（亿）
    "max_market_cap": 3000,  # 最大市值（亿）
    "min_15day_return": 12,  # 最小15日涨幅（%）
    "max_daily_change": 5,  # 最大当日涨跌幅（%）
    "min_daily_change": -3,  # 最小当日涨跌幅（%）
    "ma_period": 5,  # 移动平均线周期
}

# 卖出参数
SELL_PARAMS = {
    "max_loss": -6,  # 最大亏损（%）
    "ma_period": 5,  # 移动平均线周期
}

# 交易参数
TRADE_PARAMS = {
    "order_volume_min": 100,  # 最小下单数量
    "order_volume_step": 100,  # 下单数量步长
}
