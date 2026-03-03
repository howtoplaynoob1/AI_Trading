# 5日均线策略 - 实盘交易
# 基于5日均线的趋势跟踪策略，包含完整的买卖逻辑和风险控制

from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant
from xtquant import xtdata
import random
import datetime
import pandas as pd
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StrategyCallback(XtQuantTraderCallback):
    """策略事件回调类"""
    
    def __init__(self, strategy):
        super().__init__()
        self.strategy = strategy
    
    def on_order_error(self, order_error):
        """订单错误回调"""
        logger.error(f"订单错误: {order_error.error_msg}")
    
    def on_cancel_error(self, cancel_error):
        """撤单错误回调"""
        logger.error(f"撤单错误: {cancel_error}")
    
    def on_connected(self):
        """连接成功回调"""
        logger.info("交易系统连接成功")
    
    def on_disconnected(self):
        """断开连接回调"""
        logger.warning("交易系统连接断开")
    
    def on_stock_order(self, order):
        """订单状态更新回调"""
        logger.info(f"订单更新 - 股票: {order.stock_code}, 状态: {order.order_status}")
        self.strategy.on_order_update(order)
    
    def on_stock_trade(self, trade):
        """成交更新回调"""
        logger.info(f"成交更新 - 股票: {trade.stock_code}, 成交数量: {trade.traded_volume}")
        self.strategy.on_trade_update(trade)


class MA5Strategy:
    """5日均线交易策略"""
    
    def __init__(self, qmt_path, account_id, capital_per_stock=10000):
        """
        初始化策略
        
        参数:
            qmt_path: QMT安装路径
            account_id: 账户ID
            capital_per_stock: 每只股票的资金分配(元)
        """
        self.qmt_path = qmt_path
        self.account_id = account_id
        self.account = StockAccount(account_id)
        self.capital_per_stock = capital_per_stock
        
        self.callback = StrategyCallback(self)
        self.trader = None
        
        # 持仓记录
        self.portfolio = {}
        # 订单状态跟踪
        self.order_status = {}
        # 成交记录
        self.trade_records = {}
    
    def init_trader(self):
        """初始化交易客户端"""
        try:
            session_id = int(random.randint(100000, 999999))
            self.trader = XtQuantTrader(self.qmt_path, session_id, self.callback)
            self.trader.start()
            
            connect_result = self.trader.connect()
            if connect_result != 0:
                logger.error(f"连接失败，错误代码: {connect_result}")
                return False
            
            logger.info("连接成功")
            
            subscribe_result = self.trader.subscribe(self.account)
            if subscribe_result != 0:
                logger.error(f"订阅账户失败，错误代码: {subscribe_result}")
                return False
            
            logger.info("订阅账户成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化交易客户端失败: {e}")
            return False
    
    def get_account_info(self):
        """获取账户基本信息"""
        try:
            account_infos = self.trader.query_account_infos()
            logger.info(f"账户信息: {account_infos}")
            return account_infos
        except Exception as e:
            logger.error(f"查询账户信息失败: {e}")
            return None
    
    def get_account_asset(self):
        """获取账户资产信息"""
        try:
            asset = self.trader.query_stock_asset(self.account)
            if asset:
                logger.info(f"总资产: {asset.m_dTotalAsset}, 可用资金: {asset.m_dAvailable}, 持仓市值: {asset.m_dMarketValue}")
                return asset
            else:
                logger.warning("资产查询结果为None")
                return None
        except Exception as e:
            logger.error(f"查询账户资产失败: {e}")
            return None
    
    def get_positions(self):
        """获取持仓信息"""
        try:
            positions = self.trader.query_stock_positions(self.account)
            return positions if positions else []
        except Exception as e:
            logger.error(f"查询持仓失败: {e}")
            return []
    
    def update_portfolio(self):
        """更新持仓信息"""
        positions = self.get_positions()
        self.portfolio.clear()
        
        for pos in positions:
            self.portfolio[pos.stock_code] = {
                'quantity': pos.quantity,
                'available_quantity': pos.available_quantity,
                'cost_price': pos.cost_price,
                'market_price': pos.m_dMarketValue / pos.quantity if pos.quantity > 0 else 0
            }
        
        logger.info(f"持仓更新完成，当前持仓: {len(self.portfolio)} 只股票")
        return self.portfolio
    
    def get_market_data(self, stock_code):
        """获取实时行情数据"""
        try:
            quote = xtdata.get_market_data_ex(
                stock_list=[stock_code],
                field_list=["lastPrice", "openPrice", "highPrice", "lowPrice", 
                           "bidPrice1", "askPrice1", "askPrice2", "bidVolume1", "askVolume1", "askVolume2"],
                count=1
            )
            return quote
        except Exception as e:
            logger.error(f"获取 {stock_code} 行情数据失败: {e}")
            return None
    
    def get_historical_data(self, stock_code, days=30):
        """获取历史行情数据"""
        try:
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days)
            
            data = xtdata.get_market_data(
                stock_code=[stock_code],
                field_list=['close', 'open', 'high', 'low', 'volume'],
                begin_time=start_date.strftime('%Y%m%d'),
                end_time=end_date.strftime('%Y%m%d'),
                period='1d'
            )
            return data
        except Exception as e:
            logger.error(f"获取 {stock_code} 历史数据失败: {e}")
            return None
    
    def calculate_ma(self, stock_code, period=5):
        """计算移动平均线"""
        try:
            data = self.get_historical_data(stock_code, days=period + 5)
            if data and 'close' in data:
                close_prices = data['close'][stock_code]
                if len(close_prices) >= period:
                    ma = close_prices.rolling(window=period).mean().iloc[-1]
                    return ma
            return None
        except Exception as e:
            logger.error(f"计算 {stock_code} MA{period} 失败: {e}")
            return None
    
    def calculate_buy_fee(self, amount):
        """计算买入费用"""
        whole_parts = int(amount / 10000)
        remainder = amount % 10000
        fee = whole_parts * 3
        if remainder > 0:
            fee += 3
        return fee
    
    def calculate_sell_fee(self, amount):
        """计算卖出费用"""
        whole_parts = int(amount / 10000)
        remainder = amount % 10000
        stamp_tax = whole_parts * 5
        trade_fee = whole_parts * 3
        if remainder > 0:
            stamp_tax += 5
            trade_fee += 3
        return stamp_tax + trade_fee
    
    def select_stocks(self, stock_pool):
        """选股逻辑"""
        selected = []
        logger.info(f"开始选股，股票池大小: {len(stock_pool)}")
        
        for stock_code in stock_pool:
            try:
                # 检查是否已持仓
                if stock_code in self.portfolio:
                    continue
                
                # 获取行情数据
                quote = self.get_market_data(stock_code)
                if not quote or stock_code not in quote:
                    continue
                
                quote_data = quote[stock_code]
                if quote_data.empty:
                    continue
                
                last_price = quote_data.get("lastPrice", [0]).iloc[-1]
                if last_price <= 0:
                    continue
                
                # 获取5日均线
                ma5 = self.calculate_ma(stock_code, 5)
                if ma5 is None or pd.isna(ma5):
                    continue
                
                # 选股条件：股价 > 5日均线
                if last_price > ma5:
                    selected.append(stock_code)
                    logger.info(f"选中 {stock_code}: 价格 {last_price}, MA5 {ma5:.2f}")
                    
                    if len(selected) >= 5:  # 限制选股数量
                        break
                        
            except Exception as e:
                logger.debug(f"处理 {stock_code} 时出错: {e}")
                continue
        
        logger.info(f"选股完成，共选中 {len(selected)} 只股票")
        return selected
    
    def buy_stocks(self, selected_stocks):
        """买入股票"""
        if not selected_stocks:
            logger.info("没有选中的股票，跳过买入")
            return
        
        asset = self.get_account_asset()
        if not asset:
            logger.error("无法获取账户资产，取消买入")
            return
        
        available_capital = asset.m_dAvailable
        logger.info(f"开始买入，可用资金: {available_capital}")
        
        for stock_code in selected_stocks:
            try:
                if stock_code in self.portfolio:
                    continue
                
                quote = self.get_market_data(stock_code)
                if not quote or stock_code not in quote:
                    continue
                
                quote_data = quote[stock_code]
                if quote_data.empty:
                    continue
                
                # 使用买一价作为买入价格
                bid_price = quote_data.get("bidPrice1", [0]).iloc[-1]
                
                if bid_price <= 0:
                    logger.warning(f"{stock_code} 买一价无效，跳过")
                    continue
                
                # 计算购买数量和费用（使用买一价）
                quantity = int(self.capital_per_stock / bid_price / 100) * 100
                buy_cost = bid_price * quantity
                buy_fee = self.calculate_buy_fee(buy_cost)
                total_cost = buy_cost + buy_fee
                
                if total_cost > self.capital_per_stock:
                    # 调整数量确保总成本不超过分配资金
                    for test_quantity in range(quantity, 0, -100):
                        test_cost = bid_price * test_quantity
                        test_fee = self.calculate_buy_fee(test_cost)
                        if test_cost + test_fee <= self.capital_per_stock:
                            quantity = test_quantity
                            buy_cost = test_cost
                            buy_fee = test_fee
                            break
                    else:
                        logger.warning(f"{stock_code} 资金不足，跳过购买")
                        continue
                
                if quantity < 100:
                    logger.warning(f"{stock_code} 购买数量不足100股")
                    continue
                
                # 下单（使用买一价）
                order_id = self.trader.order_stock(
                    account=self.account,
                    stock_code=stock_code,
                    order_type=xtconstant.STOCK_BUY,
                    order_volume=quantity,
                    price_type=xtconstant.FIX_PRICE,
                    price=bid_price
                )
                
                if order_id != -1:
                    logger.info(f"买入委托成功: {stock_code}, 价格(买一): {bid_price}, 数量: {quantity}, 成本: {buy_cost}, 手续费: {buy_fee}")
                    self.order_status[order_id] = 'submitted'
                else:
                    logger.error(f"买入 {stock_code} 失败")
                    
            except Exception as e:
                logger.error(f"买入 {stock_code} 时出错: {e}")
                continue
    
    def sell_stocks(self):
        """检查卖出条件并执行卖出"""
        if not self.portfolio:
            logger.info("没有持仓，无需卖出")
            return
        
        logger.info(f"开始检查卖出条件，当前持仓: {len(self.portfolio)} 只股票")
        
        for stock_code, position_info in list(self.portfolio.items()):
            try:
                quote = self.get_market_data(stock_code)
                if not quote or stock_code not in quote:
                    continue
                
                quote_data = quote[stock_code]
                if quote_data.empty:
                    continue
                
                last_price = quote_data.get("lastPrice", [0]).iloc[-1]
                if last_price <= 0:
                    continue
                
                # 获取5日均线
                ma5 = self.calculate_ma(stock_code, 5)
                if ma5 is None or pd.isna(ma5):
                    continue
                
                # 计算收益率
                cost_price = position_info['cost_price']
                profit_rate = (last_price - cost_price) / cost_price * 100
                
                logger.info(f"{stock_code}: 价格 {last_price}, 成本 {cost_price}, MA5 {ma5:.2f}, 收益 {profit_rate:.2f}%")
                
                # 卖出条件1：跌破5日均线
                if last_price < ma5:
                    logger.info(f"{stock_code} 跌破5日均线，执行卖出")
                    self.execute_sell(stock_code, position_info['available_quantity'])
                    continue
                
                # 卖出条件2：盈利 > 6%
                if profit_rate > 6:
                    logger.info(f"{stock_code} 盈利 {profit_rate:.2f}%，止盈卖出")
                    self.execute_sell(stock_code, position_info['available_quantity'])
                    continue
                
                # 卖出条件3：亏损 > 5%
                if profit_rate < -5:
                    logger.info(f"{stock_code} 亏损 {profit_rate:.2f}%，止损卖出")
                    self.execute_sell(stock_code, position_info['available_quantity'])
                    continue
                    
            except Exception as e:
                logger.error(f"处理 {stock_code} 卖出条件时出错: {e}")
                continue
    
    def execute_sell(self, stock_code, quantity):
        """执行卖出操作"""
        try:
            if quantity < 100:
                logger.warning(f"{stock_code} 数量不足100股，无法卖出")
                return
            
            quote = self.get_market_data(stock_code)
            sell_price = 0
            if quote and stock_code in quote:
                quote_data = quote[stock_code]
                if not quote_data.empty:
                    # 使用卖二价作为卖出价格
                    sell_price = quote_data.get("askPrice2", [0]).iloc[-1]
                    # 如果卖二价无效，尝试使用卖一价
                    if sell_price <= 0:
                        sell_price = quote_data.get("askPrice1", [0]).iloc[-1]
                        logger.warning(f"{stock_code} 卖二价无效，使用卖一价")
            
            # 计算费用
            if sell_price > 0:
                proceeds = sell_price * quantity
                sell_fee = self.calculate_sell_fee(proceeds)
                logger.info(f"卖出 {stock_code}: 价格(卖二): {sell_price}, 数量 {quantity}, 总收入 {proceeds}, 手续费 {sell_fee}")
            
            order_id = self.trader.order_stock(
                account=self.account,
                stock_code=stock_code,
                order_type=xtconstant.STOCK_SELL,
                order_volume=quantity,
                price_type=xtconstant.LATEST_PRICE,
                price=0
            )
            
            if order_id != -1:
                logger.info(f"卖出 {stock_code} 成功，订单ID: {order_id}")
                self.order_status[order_id] = 'submitted'
            else:
                logger.error(f"卖出 {stock_code} 失败")
                
        except Exception as e:
            logger.error(f"卖出 {stock_code} 时出错: {e}")
    
    def on_order_update(self, order):
        """订单更新处理"""
        self.order_status[order.order_id] = order.order_status
    
    def on_trade_update(self, trade):
        """成交更新处理"""
        self.trade_records[trade.trade_id] = trade
    
    def run(self, stock_pool):
        """运行策略"""
        logger.info("=" * 60)
        logger.info("5日均线策略启动")
        logger.info("=" * 60)
        
        if not self.init_trader():
            logger.error("初始化失败，退出")
            return
        
        try:
            # 获取账户信息
            self.get_account_info()
            self.get_account_asset()
            
            # 更新持仓
            self.update_portfolio()
            
            # 选股
            selected_stocks = self.select_stocks(stock_pool)
            
            # 买入
            self.buy_stocks(selected_stocks)
            
            # 卖出
            self.sell_stocks()
            
            # 更新持仓
            self.update_portfolio()
            
            logger.info("策略执行完成")
            
        except KeyboardInterrupt:
            logger.warning("策略被手动停止")
        except Exception as e:
            logger.error(f"策略执行出错: {e}")
        finally:
            if self.trader:
                self.trader.stop()
                logger.info("交易客户端已关闭")
