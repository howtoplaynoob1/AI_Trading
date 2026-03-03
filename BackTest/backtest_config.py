# 回测配置文件

# 回测时间范围（包含时分秒的格式，用于分时数据）
# 2025 全年回测
START_DATE = '20250101093000'
END_DATE = '20251231150000'

# 回测资金配置
INITIAL_CAPITAL = 1000000  # 初始资金（100万）
CAPITAL_PER_STOCK = 300000  # 每只股票的资金分配（30万）

# 指数配置
INDEX_CONFIG = {
    "hs300": {
        "code": "000300.SH",  # 沪深300指数代码
        "name": "沪深300"
    },
    "zz500": {
        "code": "000905.SH",  # 中证500指数代码
        "name": "中证500"
    },
    "sz50": {
        "code": "000016.SH",  # 上证50指数代码
        "name": "上证50"
    }
}

# 策略配置
STRATEGY_CONFIG = {
    "use_index_constituents": True,  # 使用指数成分股
    "target_index": "zz500",  # 目标指数
    "max_stocks": 300,  # 最大股票数量
    "force_download": True,  # 是否强制下载数据（False=使用缓存，True=重新下载）
    "min_daily_volume": 1000000  # 成交量过滤阈值：100万股
}

# 5分钟级别交易策略配置
SIMPLE_MA_STRATEGY_CONFIG = {
    # 买入规则参数（5分钟级别交易）
    "buy_rules": {
        "price_breakout": True,  # 价格突破：当前股价 >= 前10日最高股价
        "volume_confirm": True,  # 成交量确认：当前在当日的累计成交量 >= 上一日同时间成交量
        "trend_confirm": True,  # 趋势确认：当前股价 >= 近5日均线股价
        "strength_confirm": True,  # 强度确认：前8日累计涨幅 > 10%
        "market_filter": True  # 大盘环境：当日上证指数需在5日均线上方
    },
    
    # 卖出规则参数
    "sell_rules": {
        "price_below_ma5": True,  # 趋势反转：股价跌破5日均线
        "profit_target": 0.06,  # 盈利大于6%止盈卖出（按比例配置，例如6%写为0.06）
        "loss_cut": 0.06,  # 单只股票亏损大于6%卖出（按比例配置，例如6%写为0.06）
        "price_below_3d_low": True,  # 短期反转：股价低于前三日最低价格卖出
        "max_holding_days_excl_buy": 2  # 持仓时间：持仓时间1-2天（不含买入当天）
    }
}

# 测试股票列表（备用）
TEST_STOCKS = [
    "000001.SZ",  # 平安银行
    "000002.SZ",  # 万科A
    "000008.SZ",  # 五粮液
    "000009.SZ",  # 浦发银行
    "000010.SZ",  # 招商银行
    "600000.SH",  # 中国平安
    "600036.SH",  # 中国中免
    "601318.SH",  # 贵州茅台
    "601888.SH",  # 美的集团
    "600519.SH",  # 比亚迪
    "000333.SZ"   # 其他
]
