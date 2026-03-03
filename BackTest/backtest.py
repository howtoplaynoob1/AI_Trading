# 策略回测脚本
# 使用历史数据测试5日均线策略的表现

import sys
import os

# 添加xtquant模块的路径到Python搜索路径
# 使用绝对路径确保正确性
# 注意：需要添加的是包含xtquant目录的父目录，而不是xtquant目录本身
xtquant_parent_path = r"e:\TRAE\AI Coding\T_1\AI_Trading"
sys.path.append(xtquant_parent_path)
print(f"已添加xtquant父路径: {xtquant_parent_path}")
print(f"当前Python搜索路径: {sys.path}")

import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 导入回测配置
from backtest_config import (
    START_DATE,
    END_DATE,
    INITIAL_CAPITAL,
    CAPITAL_PER_STOCK,
    STRATEGY_CONFIG,
    INDEX_CONFIG,
    TEST_STOCKS,
    SIMPLE_MA_STRATEGY_CONFIG
)


class Backtester:
    """策略回测器"""

    def __init__(self, start_date, end_date, initial_capital, capital_per_stock):
        """初始化回测器"""
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital_per_stock = capital_per_stock
        self.capital = initial_capital
        self.portfolio = {}  # 持仓
        self.trades = []      # 交易记录
        self.daily_values = []  # 每日价值
        self.stock_data = {}    # 股票数据

    @staticmethod
    def _parse_xt_time_index(index_like):
        """
        xtquant 常见时间戳格式：
        - 日线：YYYYMMDD（8位）
        - 分钟线：YYYYMMDDHHMM（12位）或 YYYYMMDDHHMMSS（14位）
        """
        idx = pd.Index(index_like)
        if len(idx) == 0:
            return idx

        # xt 返回可能是 int/np.int64；直接 pd.to_datetime(int) 会被当成 ns 时间戳 -> 1970 年
        s = idx.astype(str)
        first = s[0]
        fmt = {8: "%Y%m%d", 12: "%Y%m%d%H%M", 14: "%Y%m%d%H%M%S"}.get(len(first))
        if fmt:
            parsed = pd.to_datetime(s, format=fmt, errors="coerce")
        else:
            parsed = pd.to_datetime(s, errors="coerce")
        return parsed

    @staticmethod
    def _normalize_start_end_for_period(start_time: str, end_time: str, period: str):
        """
        日线/周线通常使用 YYYYMMDD；分钟线使用 YYYYMMDDHHMM 或 YYYYMMDDHHMMSS。
        配置里即使写了带时分秒的字符串，这里也会按周期做兼容。
        """
        if not isinstance(start_time, str) or not isinstance(end_time, str):
            return start_time, end_time

        # 常见日线：1d；也兼容 'Xd' / '1w'
        is_daily_like = False
        try:
            p = str(period).lower()
            is_daily_like = p.endswith("d") or p.endswith("w") or p.endswith("m") and p in ("1mo", "1mon", "1month")
            is_daily_like = is_daily_like or p in ("1d", "1w")
        except Exception:
            is_daily_like = False

        if is_daily_like:
            return start_time[:8], end_time[:8]
        return start_time, end_time

    @staticmethod
    def _is_sh_stock(stock_code: str) -> bool:
        try:
            return isinstance(stock_code, str) and stock_code.upper().endswith(".SH")
        except Exception:
            return False

    def get_index_constituents(self, index_code, force_download=False):
        """获取指数成分股"""
        print(f"\n===== 开始获取指数成分股 =====")
        print(f"指数代码: {index_code}")

        try:
            # 导入xtquant模块
            import xtquant
            from xtquant import xtdata
            print(f"成功导入xtquant模块: {xtquant.__file__}")

            # 尝试连接到xtquant服务
            print("尝试连接到xtquant服务...")
            try:
                xtdata.connect()
                print("成功连接到xtquant服务")
            except Exception as conn_e:
                print(f"连接xtquant服务失败: {conn_e}")
                raise

            # 仅在force_download为True时执行下载操作
            if force_download:
                # 尝试下载指数成分权重信息
                print("尝试下载指数成分权重信息...")
                xtdata.download_index_weight()
                print("成功下载指数成分权重信息")

            # 根据指数代码确定板块名称
            sector_name_map = {
                '000905.SH': '中证500',
                '000300.SH': '沪深300',
                '000016.SH': '上证50'
            }

            sector_name = sector_name_map.get(index_code, index_code)
            print(f"使用板块名称: {sector_name}")

            # 尝试使用xtdata.get_index_weight获取指数成分股
            print(f"调用xtdata.get_index_weight({index_code})...")
            index_weight = xtdata.get_index_weight(index_code)
            print(f"指数权重数据类型: {type(index_weight)}")

            # 如果获取到了指数权重数据，从中提取成分股列表
            if isinstance(index_weight, dict) and len(index_weight) > 0:
                print(f"指数权重数据包含 {len(index_weight)} 只成分股")
                # 尝试从指数权重数据中提取成分股列表
                constituents = list(index_weight.keys())
            else:
                # 仅在force_download为True时执行下载操作
                if force_download:
                    # 尝试下载板块分类信息
                    print("尝试下载板块分类信息...")
                    xtdata.download_sector_data()
                    print("成功下载板块分类信息")

                # 如果没有获取到指数权重数据，尝试使用xtdata.get_stock_list_in_sector获取成分股列表
                print(f"调用xtdata.get_stock_list_in_sector({sector_name})...")
                constituents = xtdata.get_stock_list_in_sector(sector_name)

                # 如果仍然没有获取到成分股，使用硬编码的中证500成分股列表
                if not isinstance(constituents, list) or len(constituents) == 0:
                    print("使用硬编码的中证500成分股列表...")
                    # 硬编码的中证500成分股列表（示例）
                    constituents = [
                        '000001.SZ', '000002.SZ', '000008.SZ', '000009.SZ', '000010.SZ',
                        '000012.SZ', '000021.SZ', '000024.SZ', '000027.SZ', '000028.SZ',
                        '000030.SZ', '000031.SZ', '000036.SZ', '000039.SZ', '000046.SZ',
                        '000050.SZ', '000056.SZ', '000059.SZ', '000060.SZ', '000061.SZ',
                        '000063.SZ', '000066.SZ', '000069.SZ', '000070.SZ', '000072.SZ',
                        '000078.SZ', '000088.SZ', '000090.SZ', '000099.SZ', '000100.SZ',
                        '000104.SZ', '000107.SZ', '000113.SZ', '000116.SZ', '000118.SZ',
                        '000123.SZ', '000126.SZ', '000133.SZ', '000153.SZ', '000155.SZ',
                        '000156.SZ', '000157.SZ', '000158.SZ', '000166.SZ', '000170.SZ',
                        '000171.SZ', '000172.SZ', '000177.SZ', '000178.SZ', '000183.SZ'
                    ]

            # 验证返回结果
            if isinstance(constituents, list):
                print(f"成功获取 {len(constituents)} 只成分股")
                if len(constituents) > 0:
                    print(f"前5只成分股: {constituents[:5]}")
                return constituents
            else:
                print("获取成分股失败，返回空列表（结果类型不是列表）")
                return []

        except ImportError as e:
            print(f"导入xtquant失败: {e}")
            return []
        except Exception as e:
            print(f"获取指数成分股失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_stock_data(self, stock_code, force_download=False, period='1d'):
        """
        获取股票历史数据
        参考xtquant.xtdata.get_market_data的返回格式：
        - 对于K线数据(1d/1w等)：返回 {field: pd.DataFrame(index=stock_list, columns=time_list)}
        :param stock_code: 股票代码
        :param force_download: 是否强制下载（默认False，使用缓存）
        :param period: 数据周期，支持'1d'（日线）、'1m'（1分钟线）等
        """
        try:
            # 先导入xtquant模块，确保它可以被找到
            import xtquant
            from xtquant import xtdata
            print(f"成功导入xtquant模块: {xtquant.__file__}")

            # 尝试连接到xtquant服务（如果尚未连接）
            # 根据xtquant源码，connect()如果已经连接会直接返回，不会抛出异常
            # 只有在无法连接时才会抛出异常
            try:
                xtdata.connect()
            except Exception as conn_e:
                print(f"连接xtquant服务失败: {conn_e}")
                raise

            # 仅在强制下载时才下载，否则使用xtquant的本地缓存
            if force_download:
                print(f"下载 {stock_code} 历史数据...")
                start_time, end_time = self._normalize_start_end_for_period(self.start_date, self.end_date, period)
                # 根据xtquant文档，download_history_data的参数顺序是：
                # download_history_data(stock_code, period, start_time='', end_time='', incrementally=None)
                xtdata.download_history_data(
                    stock_code,
                    period,
                    start_time,
                    end_time
                )

            # 获取历史K线数据
            # 根据xtdata文档，K线数据返回格式: {field: pd.DataFrame(index=stock_list, columns=time_list)}
            # DataFrame的行是股票代码，列是时间戳（日期）
            start_time, end_time = self._normalize_start_end_for_period(self.start_date, self.end_date, period)
            data = xtdata.get_market_data(
                field_list=['open', 'high', 'low', 'close', 'volume'],
                stock_list=[stock_code],
                period=period,
                start_time=start_time,
                end_time=end_time
            )

            if not data:
                print(f"获取 {stock_code} 数据失败或为空，data为None或空")
                return None

            print(f"获取 {stock_code} 数据，data的keys: {list(data.keys())}")

            if 'close' not in data:
                print(f"获取 {stock_code} 数据失败，缺少close字段")
                return None

            # 提取数据：data[field] 是 DataFrame(index=stock_list, columns=time_list)
            # 对于单个股票，第一行（也是唯一一行）包含所有日期的数据
            # pd.DataFrame with index=[stock_code], columns=[dates]
            close_data = data['close']

            print(f"close_data类型: {type(close_data)}, 形状: {close_data.shape if hasattr(close_data, 'shape') else 'N/A'}")

            if not isinstance(close_data, pd.DataFrame):
                print(f"数据格式错误，期望DataFrame，实际类型: {type(close_data)}")
                return None

            if close_data.empty:
                print(f"数据为空（可能是本地无缓存/下载失败/时间范围不匹配/无分钟数据权限）")
                # 兜底：如果当前是缓存模式且为空，尝试下载一次后重试
                if not force_download:
                    try:
                        print(f"尝试下载后重试获取 {stock_code} 数据，周期：{period}...")
                        start_time, end_time = self._normalize_start_end_for_period(self.start_date, self.end_date, period)
                        xtdata.download_history_data(stock_code, period, start_time, end_time)
                        data = xtdata.get_market_data(
                            field_list=['open', 'high', 'low', 'close', 'volume'],
                            stock_list=[stock_code],
                            period=period,
                            start_time=start_time,
                            end_time=end_time
                        )
                        close_data = data.get('close') if isinstance(data, dict) else None
                        if isinstance(close_data, pd.DataFrame) and not close_data.empty:
                            print("重试后获取到数据")
                        else:
                            return None
                    except Exception as retry_e:
                        print(f"下载重试失败: {retry_e}")
                        return None
                else:
                    return None

            # xtquant返回的时间戳在columns中，每列是一个日期
            # 获取单只股票（第一行）的数据：Series(index=dates, values=close价格)
            stock_series = close_data.iloc[0]  # 获取第一行（唯一的股票）

            # 转置：从 {date: value} 转换为时间索引的DataFrame
            timestamps = stock_series.index  # 时间戳列表

            # 为每个字段提取数据
            open_series = data['open'].iloc[0] if 'open' in data else None
            high_series = data['high'].iloc[0] if 'high' in data else None
            low_series = data['low'].iloc[0] if 'low' in data else None
            volume_series = data['volume'].iloc[0] if 'volume' in data else None

            # 创建DataFrame，index为时间戳
            df_dict = {}
            if open_series is not None:
                df_dict['open'] = open_series.values
            if high_series is not None:
                df_dict['high'] = high_series.values
            if low_series is not None:
                df_dict['low'] = low_series.values
            df_dict['close'] = stock_series.values
            if volume_series is not None:
                df_dict['volume'] = volume_series.values

            df = pd.DataFrame(df_dict, index=timestamps)

            # 确保index是datetime格式（时间戳可能是int格式如20230101）
            if len(df.index) > 0:
                parsed = self._parse_xt_time_index(df.index)
                # 如果解析失败导致全是 NaT，则退回 pandas 的默认解析
                if isinstance(parsed, (pd.DatetimeIndex, pd.Index)) and getattr(parsed, "isna", lambda: pd.Series([]))().all():
                    df.index = pd.to_datetime(df.index, errors="coerce")
                else:
                    df.index = parsed
                # 丢弃无法解析的时间戳
                if isinstance(df.index, pd.DatetimeIndex):
                    df = df[~df.index.isna()]
                    # 指标/切片依赖时间顺序：确保排序 & 去重
                    df = df[~df.index.duplicated(keep='last')].sort_index()

            # 计算5日均线
            df['ma5'] = df['close'].rolling(window=5).mean()

            # 计算收益率（涨幅）
            df['pct_change'] = df['close'].pct_change() * 100

            print(f"成功获取 {stock_code}，周期：{period}，数据形状：{df.shape}，时间范围：{df.index[0] if len(
                df) > 0 else 'N/A'} 到 {df.index[-1] if len(df) > 0 else 'N/A'}")

            return df

        except ImportError as e:
            print(f"导入xtquant失败: {e}")
            return None
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_stock_data(self, stock_list, force_download=False, period='1d'):
        """
        加载股票数据
        :param stock_list: 股票代码列表
        :param force_download: 是否强制下载（默认False，使用缓存）
        :param period: 数据周期，支持'1d'（日线）、'1m'（1分钟线）等
        """
        print(f"正在加载 {len(stock_list)} 只股票的历史数据，周期：{period}...")
        if force_download:
            print("强制下载模式已启用，将重新下载所有数据")
        else:
            print("使用缓存模式，优先使用本地缓存数据")

        for stock_code in stock_list:
            data = self.get_stock_data(stock_code, force_download, period)
            if data is not None:
                self.stock_data[stock_code] = data
                print(f"已加载 {stock_code} 的历史数据")
            else:
                print(f"无法加载 {stock_code} 的历史数据")

        # 加载上证指数数据
        print("\n正在加载上证指数数据...")
        sh_index_data = self.get_stock_data('000001.SH', force_download, period)
        if sh_index_data is not None:
            self.stock_data['000001.SH'] = sh_index_data
            print("已加载上证指数(000001.SH)的历史数据")
        else:
            print("无法加载上证指数数据")

    def select_stocks(self, date):
        """选股逻辑 - 简单均线策略"""
        selected = []
        print(f"\n开始选股（简单均线策略），日期: {date}")

        # 获取策略配置参数
        sell_config = SIMPLE_MA_STRATEGY_CONFIG['sell_rules']
        max_holding_days_excl_buy = sell_config.get(
            'max_holding_days_excl_buy', 2)

        # 股票池（当前数据中的股票）
        # 注意：指数数据(000001.SH)仅用于大盘过滤，不参与交易
        stock_pool = [c for c in self.stock_data.keys() if c != '000001.SH']
        print(f"股票池数量: {len(stock_pool)}")

        for stock_code in stock_pool:
            data = self.stock_data[stock_code]
            try:
                print(f"检查股票: {stock_code}")
                # 为避免未来函数：选股与买入信号统一使用“前一交易日”数据做决策
                if date not in data.index:
                    print(f"  日期 {date} 不在数据范围内")
                    continue

                date_idx = data.index.get_loc(date)
                if date_idx < 1:
                    print(f"  第一天数据，无前一日数据，跳过")
                    continue

                prev_date = data.index[date_idx - 1]
                prev_day_data = data.loc[prev_date]

                prev_close = prev_day_data.get('close')
                prev_ma5 = prev_day_data.get('ma5')
                if pd.isna(prev_close) or pd.isna(prev_ma5):
                    print(f"  前一日价格或ma5缺失，跳过")
                    continue

                # 这里不做额外的“简化选股”，直接返回满足买入所需的基础数据可用的股票。
                # 具体买入条件在 buy_stocks 中统一判断，避免选股与买入条件不一致导致偏差。
                selected.append(stock_code)
                print(f"  通过基础数据检查: {stock_code} (prev_close={
                      prev_close}, prev_ma5={prev_ma5})")

                # 移除选股数量限制，确保对所有股票实施策略

            except Exception as e:
                print(f"处理股票 {stock_code} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"选股完成，共选中 {len(selected)} 只股票")
        return selected

    def simulate_trade(self, date):
        """模拟交易日"""
        # 卖出逻辑
        self.sell_stocks(date)

        # 选股
        selected_stocks = self.select_stocks(date)

        # 买入逻辑
        self.buy_stocks(date, selected_stocks)

        # 计算当日资产价值
        self.calculate_daily_value(date)

    def buy_stocks(self, date, selected_stocks):
        """模拟买入股票 - 简单均线策略"""
        print(f"\n开始买入股票（简单均线策略），日期: {date}")

        # 获取策略配置参数
        buy_config = SIMPLE_MA_STRATEGY_CONFIG['buy_rules']

        for stock_code in selected_stocks:
            try:
                # 检查是否已持仓
                if stock_code in self.portfolio:
                    print(f"  已持有 {stock_code}，跳过")
                    continue

                # 获取股票数据
                data = self.stock_data.get(stock_code)
                if data is None:
                    print(f"  未找到 {stock_code} 的数据，跳过")
                    continue

                if not isinstance(data, pd.DataFrame):
                    print(f"  数据类型错误，期望DataFrame，实际类型: {type(data)}")
                    continue

                # 获取上证指数数据
                index_code = '000001.SH'  # 上证指数
                index_data = self.stock_data.get(index_code)
                if index_data is None:
                    print(f"  未找到上证指数数据，跳过")
                    continue

                # 检查数据周期
                # 假设data.index的频率可以判断数据周期
                # 对于分时数据，我们需要处理每个时间点
                if len(data) == 0:
                    print(f"  股票数据为空，跳过")
                    continue

                # 获取数据频率
                if isinstance(data.index, pd.DatetimeIndex):
                    # 计算时间差
                    time_diff = data.index[1] - data.index[0]
                    if time_diff.total_seconds() < 3600:  # 小于1小时，认为是分时数据
                        is_intraday = True
                    else:
                        is_intraday = False
                else:
                    is_intraday = False

                print(f"  数据类型: {'分时数据' if is_intraday else '日线数据'}")

                if is_intraday:
                    # 处理分时数据
                    # 筛选出当天的数据
                    today_data = data[data.index.date == pd.to_datetime(date).date()]
                    if today_data.empty:
                        print(f"  当日无分时数据，跳过")
                        continue

                    # 筛选出前一天的数据
                    prev_date = pd.to_datetime(date) - pd.Timedelta(days=1)
                    prev_day_data = data[data.index.date == prev_date.date()]
                    if prev_day_data.empty:
                        print(f"  前一日无分时数据，跳过")
                        continue

                    # 计算前10日最高股价（使用日线数据计算）
                    # 提取日线数据
                    daily_data = data.resample('D').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    })
                    daily_data['ma5'] = daily_data['close'].rolling(window=5).mean()

                    if len(daily_data) < 10:
                        print(f"  数据不足10天，无前10日最高股价数据，跳过")
                        continue

                    # 前10日最高价（不含当日）
                    max_high_10d = daily_data.iloc[-11:-1]['high'].max()

                    # 计算前8日累计涨幅
                    if len(daily_data) >= 9:
                        eight_day_change = (daily_data.iloc[-2]['close'] - daily_data.iloc[-10]['close']) / daily_data.iloc[-10]['close']
                    else:
                        eight_day_change = -999

                    # 计算当日累计成交量
                    today_data['cum_volume'] = today_data['volume'].cumsum()

                    # 遍历当天的每个时间点
                    for time_idx, time_row in today_data.iterrows():
                        # 获取当前时间
                        current_time = time_row.name.time()
                        
                        # 找到前一天同时间的数据
                        prev_time_data = prev_day_data[prev_day_data.index.time == current_time]
                        if prev_time_data.empty:
                            continue

                        # 获取当前价格和成交量
                        current_price = time_row['close']
                        current_cum_volume = time_row['cum_volume']
                        prev_cum_volume = prev_time_data.iloc[0]['volume']

                        # 计算5日均线（使用分时数据计算）
                        # 获取最近5天的分时数据
                        recent_data = data[(data.index >= pd.to_datetime(date) - pd.Timedelta(days=4)) & (data.index <= time_idx)]
                        if len(recent_data) < 5:
                            continue
                        # 计算5日移动平均
                        ma5 = recent_data['close'].mean()

                        # 检查大盘环境
                        # 获取当前时间的上证指数数据
                        today_index_data = index_data[index_data.index.date == pd.to_datetime(date).date()]
                        current_index_data = today_index_data[today_index_data.index.time == current_time]
                        if current_index_data.empty:
                            continue
                        current_index_price = current_index_data.iloc[0]['close']
                        # 计算上证指数5日均线
                        recent_index_data = index_data[(index_data.index >= pd.to_datetime(date) - pd.Timedelta(days=4)) & (index_data.index <= time_idx)]
                        if len(recent_index_data) < 5:
                            continue
                        index_ma5 = recent_index_data['close'].mean()

                        # 成交量过滤
                        min_daily_volume = STRATEGY_CONFIG.get('min_daily_volume', 1000000)
                        if daily_data.iloc[-2]['volume'] < min_daily_volume:
                            print(f"  成交量不足，跳过买入")
                            continue

                        # 检查买入条件
                        breakout_ok = current_price >= max_high_10d
                        volume_ok = current_cum_volume >= prev_cum_volume
                        trend_ok = current_price >= ma5
                        strength_ok = eight_day_change > 0.05  # 强度确认：前8日累计涨幅 > 5%
                        index_ok = current_index_price >= index_ma5

                        if breakout_ok and volume_ok and trend_ok and strength_ok and index_ok:
                            print(f"  买入信号触发时间: {current_time}")
                            print(f"  价格突破: 当前价格 {current_price:.2f} >= 前10日最高 {max_high_10d:.2f}")
                            print(f"  成交量确认: 当前累计成交量 {current_cum_volume} >= 前一日同时间成交量 {prev_cum_volume}")
                            print(f"  趋势确认: 当前价格 {current_price:.2f} >= 5日均线 {ma5:.2f}")
                            print(f"  强度确认: 前8日累计涨幅 {eight_day_change:.2%} > 5%")
                            print(f"  大盘环境: 上证指数 {current_index_price:.2f} >= 5日均线 {index_ma5:.2f}")

                            # 买入价格：5分钟内最高价 + 滑点
                            buy_price = time_row['high'] * 1.001  # 0.1%滑点

                            # 资金管理：
                            # 1) 默认每次用总资金的30%
                            # 2) 如果剩余资金不足30%或30%资金不足100股，则使用全部剩余资金
                            buy_amount = self.capital * 0.3
                            # 计算30%资金可购买的股数
                            test_quantity = int(buy_amount / buy_price / 100) * 100
                            if test_quantity < 100:
                                # 30%资金不足100股，使用全部剩余资金
                                buy_amount = self.capital

                            quantity = int(buy_amount / buy_price / 100) * 100

                            # 检查购买数量是否足够
                            if quantity < 100:
                                # 如果资金不足100股，尝试使用全部剩余资金
                                full_quantity = int(
                                    self.capital / buy_price / 100) * 100
                                if full_quantity >= 100:
                                    quantity = full_quantity
                                    print(f"  资金不足100股，使用全部剩余资金购买")
                                else:
                                    print(f"  购买数量不足100股（{full_quantity}），跳过")
                                    continue

                            # 执行买入
                            cost = buy_price * quantity
                            buy_fee = self.calculate_buy_fee(cost, stock_code=stock_code)
                            total_cost = cost + buy_fee

                            self.capital -= total_cost
                            self.portfolio[stock_code] = {
                                'quantity': quantity,
                                'cost_price': buy_price,
                                'buy_date': date
                            }

                            # 记录交易
                            self.trades.append({
                                'date': date,
                                'time': current_time,
                                'stock_code': stock_code,
                                'action': 'buy',
                                'price': buy_price,
                                'quantity': quantity,
                                'amount': cost,
                                'fee': buy_fee,
                                'total_cost': total_cost
                            })

                            print(f"  买入成功 {stock_code}，价格: {buy_price:.2f}, 数量: {quantity}, 成本: {
                                  cost:.2f}, 手续费: {buy_fee:.2f}, 总成本: {total_cost:.2f}")
                            print(f"  剩余资金: {self.capital}")
                            break  # 当天只买一次
                else:
                    # 处理日线数据
                    if date not in data.index:
                        print(f"  日期 {date} 不在 {stock_code} 的数据范围内，跳过")
                        continue

                    # 获取价格和5日均线
                    try:
                        date_idx = data.index.get_loc(date)
                        if date_idx < 2:
                            print(f"  数据不足3天，无法计算买入条件，跳过")
                            continue

                        # 获取前一日、前二日数据
                        prev_date = data.index[date_idx - 1]
                        prev2_date = data.index[date_idx - 2]
                        prev_day_data = data.loc[prev_date]
                        prev2_day_data = data.loc[prev2_date]
                        prev_close = prev_day_data['close']
                        prev_volume = prev_day_data['volume']
                        prev2_volume = prev2_day_data['volume']
                        prev_ma5 = prev_day_data.get('ma5')  # 前一日MA5
                    except Exception as e:
                        print(f"  获取数据时出错: {e}")
                        continue

                    if pd.isna(prev_close) or pd.isna(prev_ma5):
                        print(f"  前一日价格或5日均线数据缺失，跳过")
                        continue

                    print(f"  准备买入 {stock_code}，prev_close: {prev_close}, prev_ma5: {prev_ma5}")

                    # 检查成交量数据
                    if 'volume' not in data.columns:
                        print(f"  成交量数据缺失，跳过")
                        continue

                    # 计算前10日最高股价（截至前一交易日的最近10日最高价）
                    try:
                        if date_idx < 10:
                            print(f"  数据不足10天，无前10日最高股价数据，跳过")
                            continue
                        # 最近10日(含前一日)区间为 [date_idx-10, date_idx)
                        ten_days_high = data.iloc[date_idx - 10:date_idx]['high']
                        max_high_10d = ten_days_high.max()
                    except Exception as e:
                        print(f"  计算前10日最高股价时出错: {e}")
                        continue

                    # 计算前8日累计涨幅（使用前一日的收盘价）
                    try:
                        if date_idx >= 9:
                            prev_close_for_change = data.iloc[date_idx - 1]['close']
                            nine_days_ago_close = data.iloc[date_idx - 9]['close']
                            eight_day_change = (
                                prev_close_for_change - nine_days_ago_close) / nine_days_ago_close
                        else:
                            eight_day_change = -999  # 数据不足，设为一个很小的值
                    except Exception as e:
                        print(f"  计算前8日累计涨幅时出错: {e}")
                        eight_day_change = -999

                    # 成交量确认：上一日成交量 >= 上二日成交量
                    try:
                        if date_idx < 2:
                            print(f"  数据不足2天，无历史成交量对比，跳过")
                            continue
                        # 获取上一日成交量和上二日成交量
                        prev_volume = data.iloc[date_idx - 1]['volume']
                        prev2_volume = data.iloc[date_idx - 2]['volume']
                    except Exception as e:
                        print(f"  获取成交量数据时出错: {e}")
                        continue

                    if pd.isna(prev_close) or pd.isna(prev_ma5) or pd.isna(max_high_10d) or pd.isna(prev_volume) or pd.isna(prev2_volume):
                        print(f"  信号关键字段缺失，跳过")
                        continue

                    # 市场过滤：上证指数在5日均线上方（使用前一日数据避免未来函数）
                    index_ok = True
                    if index_code in self.stock_data and date in self.stock_data[index_code].index:
                        idx_df = self.stock_data[index_code]
                        idx_idx = idx_df.index.get_loc(date)
                        # 使用前一日指数数据避免未来函数
                        if idx_idx > 0:
                            prev_idx_idx = idx_idx - 1
                            prev_idx_date = idx_df.index[prev_idx_idx]
                            prev_idx_close = idx_df.iloc[prev_idx_idx]['close'] if 'close' in idx_df.columns else None
                            prev_idx_ma5 = idx_df.iloc[prev_idx_idx]['ma5'] if 'ma5' in idx_df.columns else None
                            if pd.notna(prev_idx_close) and pd.notna(prev_idx_ma5) and prev_idx_close < prev_idx_ma5:
                                index_ok = False
                        else:
                            # 第一天数据，无法获取前一日数据，默认通过
                            pass

                    # 买入条件检查
                    price_breakout_ok = prev_close >= max_high_10d
                    volume_ok = prev_volume >= prev2_volume
                    trend_ok = prev_close >= prev_ma5
                    strength_ok = eight_day_change > 0.05  # 强度确认：前8日累计涨幅 > 5%

                    if price_breakout_ok and volume_ok and trend_ok and strength_ok and index_ok:
                        print(f"  价格突破: 昨日收盘价 {prev_close:.2f} >= 前10日最高 {max_high_10d:.2f}")
                        print(f"  成交量确认: 昨日量 {prev_volume} >= 前二日量 {prev2_volume}")
                        print(f"  趋势确认: 昨日收盘价 {prev_close:.2f} >= 昨日MA5 {prev_ma5:.2f}")
                        print(f"  强度确认: 前8日累计涨幅 {eight_day_change:.2%} > 5%")

                        # 成交价：使用当日开盘价
                        today_data = data.loc[date]
                        today_open = today_data.get('open')
                        if pd.isna(today_open):
                            print(f"  当日开盘价缺失，跳过")
                            continue

                        buy_price = today_open * 1.001

                        # 资金管理：
                        # 1) 默认每次用总资金的30%
                        # 2) 如果剩余资金不足30%或30%资金不足100股，则使用全部剩余资金
                        buy_amount = self.capital * 0.3
                        # 计算30%资金可购买的股数
                        test_quantity = int(buy_amount / buy_price / 100) * 100
                        if test_quantity < 100:
                            # 30%资金不足100股，使用全部剩余资金
                            buy_amount = self.capital

                        quantity = int(buy_amount / buy_price / 100) * 100

                        # 检查购买数量是否足够
                        if quantity < 100:
                            # 如果资金不足100股，尝试使用全部剩余资金
                            full_quantity = int(
                                self.capital / buy_price / 100) * 100
                            if full_quantity >= 100:
                                quantity = full_quantity
                                print(f"  资金不足100股，使用全部剩余资金购买")
                            else:
                                print(f"  购买数量不足100股（{full_quantity}），跳过")
                                continue

                        # 执行买入（使用当日开盘价附近买入）
                        # buy_price 已经在前面计算好了
                        cost = buy_price * quantity
                        buy_fee = self.calculate_buy_fee(cost, stock_code=stock_code)
                        total_cost = cost + buy_fee

                        self.capital -= total_cost
                        self.portfolio[stock_code] = {
                            'quantity': quantity,
                            'cost_price': buy_price,
                            'buy_date': date
                        }

                        # 记录交易
                        self.trades.append({
                            'date': date,
                            'stock_code': stock_code,
                            'action': 'buy',
                            'price': buy_price,
                            'quantity': quantity,
                            'amount': cost,
                            'fee': buy_fee,
                            'total_cost': total_cost
                        })

                        print(f"  买入成功 {stock_code}，价格(买一): {buy_price:.2f}, 数量: {quantity}, 成本: {
                              cost:.2f}, 手续费: {buy_fee:.2f}, 总成本: {total_cost:.2f}")
                        print(f"  剩余资金: {self.capital}")
                    else:
                        if not price_breakout_ok:
                            print(f"  价格突破不满足: 昨日收盘价 {prev_close:.2f} < 前10日最高价 {
                                  max_high_10d:.2f}，跳过买入")
                        if not volume_ok:
                            print(f"  成交量条件不满足: 昨日成交量 {
                                  prev_volume} < 前二日成交量 {prev2_volume}，跳过买入")
                        if not trend_ok:
                            print(f"  趋势条件不满足: 昨日收盘价 {prev_close:.2f} < 昨日MA5 {
                                  prev_ma5:.2f}，跳过买入")
                        if not strength_ok:
                            print(f"  强度条件不满足: 前8日累计涨幅 {
                                  eight_day_change:.2%} <= 12%，跳过买入")
                        if not index_ok:
                            print(f"  大盘环境不满足: 上证指数低于5日均线，跳过买入")

            except Exception as e:
                print(f"买入 {stock_code} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue

    def sell_stocks(self, date):
        """模拟卖出股票 - 简单均线策略"""
        print(f"\n开始卖出股票（简单均线策略），日期: {date}")
        sell_list = []

        # 获取策略配置参数
        sell_config = SIMPLE_MA_STRATEGY_CONFIG['sell_rules']
        max_holding_days_excl_buy = sell_config.get(
            'max_holding_days_excl_buy', None)

        for stock_code, info in list(self.portfolio.items()):
            try:
                print(f"  检查持仓 {stock_code}")

                # T+1交易制度：买入当天不能卖出（按“交易日”判断，而不是按K线条数）
                buy_date = info.get('buy_date')
                if buy_date is not None:
                    try:
                        buy_day = pd.to_datetime(buy_date).date()
                        current_day = pd.to_datetime(date).date()
                    except Exception:
                        buy_day = buy_date
                        current_day = date
                    if buy_day == current_day:
                        print(f"  今日买入，T+1不能卖出，跳过")
                        continue

                # 获取数据
                data = self.stock_data.get(stock_code)
                if data is None:
                    print(f"  未找到 {stock_code} 的数据，跳过")
                    continue

                if not isinstance(data, pd.DataFrame):
                    print(f"  数据类型错误，期望DataFrame，实际类型: {type(data)}")
                    continue

                if date not in data.index:
                    print(f"  日期 {date} 不在 {stock_code} 的数据范围内，跳过")
                    continue

                # 使用当日数据做卖出决策
                try:
                    date_idx = data.index.get_loc(date)
                    if date_idx < 1:
                        print(f"  第一天数据，无前一日数据，跳过")
                        continue

                    # 计算持仓天数（不含买入当天，以“交易日”计数）
                    try:
                        trading_days = data.index.normalize().unique()
                        buy_day = pd.to_datetime(
                            buy_date).normalize() if buy_date is not None else None
                        current_day = pd.to_datetime(date).normalize()
                        if buy_day is not None and buy_day in trading_days and current_day in trading_days:
                            buy_day_idx = trading_days.get_loc(buy_day)
                            current_day_idx = trading_days.get_loc(
                                current_day)
                            holding_days_excl_buy = current_day_idx - buy_day_idx
                        else:
                            holding_days_excl_buy = None
                    except Exception as e:
                        print(f"  计算持仓天数失败: {e}")
                        holding_days_excl_buy = None

                    # 获取前一日数据用于卖出判断（避免未来函数）
                    prev_idx = date_idx - 1
                    prev_date = data.index[prev_idx]
                    prev_day_data = data.loc[prev_date]
                    prev_close = prev_day_data.get('close')
                    prev_ma5 = prev_day_data.get('ma5')

                    # 获取当日数据（仅用于获取开盘价作为卖出价格）
                    today_data = data.loc[date]
                    today_open = today_data.get('open')

                    # 当日卖出价格（用当日开盘价附近）
                    sell_price = today_open * 1.005 if pd.notna(today_open) else prev_close * 1.005
                except Exception as e:
                    print(f"  获取数据失败: {e}")
                    continue

                # 持仓规则：持仓时间<=2天(不含买入当天)，T+3必须卖出
                if max_holding_days_excl_buy is not None and holding_days_excl_buy is not None:
                    if holding_days_excl_buy >= max_holding_days_excl_buy:
                        sell_list.append(
                            (stock_code, sell_price, info, f"T+{max_holding_days_excl_buy + 1}强制卖出"))
                        print(
                            f"  持仓达到T+{max_holding_days_excl_buy + 1}，强制卖出 {stock_code}")
                        continue

                # 计算收益率（基于买入价）
                cost_price = info['cost_price']
                profit_rate = (sell_price - cost_price) / cost_price * 100

                # 卖出条件1: 跌破5日均线
                if sell_config['price_below_ma5']:
                    if pd.notna(prev_close) and pd.notna(prev_ma5) and prev_close < prev_ma5:
                        sell_list.append(
                            (stock_code, sell_price, info, "跌破5日均线"))
                        print(f"  卖出条件1触发: 跌破5日均线, 卖出 {stock_code}")
                        continue

                # 卖出条件2: 盈利大于6%止盈
                if profit_rate > sell_config['profit_target'] * 100:
                    sell_list.append(
                        (stock_code, sell_price, info, "盈利大于6%止盈"))
                    print(f"  卖出条件2触发: 盈利 {
                          profit_rate:.2f}%，止盈卖出 {stock_code}")
                    continue

                # 卖出条件3: 单只股票亏损大于5%卖出
                if profit_rate < -sell_config['loss_cut'] * 100:
                    sell_list.append(
                        (stock_code, sell_price, info, "亏损大于止损幅度"))
                    print(f"  卖出条件3触发: 亏损 {
                          profit_rate:.2f}%，止损卖出 {stock_code}")
                    continue

                # 卖出条件4: 股价低于前三日最低价格
                if sell_config.get('price_below_3d_low', False):
                    try:
                        # 用前一日收盘价比较前三日最低价（避免未来函数）
                        if date_idx >= 3:
                            low_3d = data.iloc[date_idx - 3:date_idx]['low']
                            min_low_3d = low_3d.min()
                            if pd.notna(prev_close) and pd.notna(min_low_3d) and prev_close < min_low_3d:
                                sell_list.append(
                                    (stock_code, sell_price, info, "低于前三日最低价"))
                                print(f"  卖出条件4触发: 前日收盘 {prev_close:.2f} < 3日最低 {
                                      min_low_3d:.2f}，卖出 {stock_code}")
                                continue
                    except Exception as e:
                        print(f"  计算3日最低价时出错: {e}")

                # 其他卖出条件已简化，只保留三个主要条件
                # 现在只依赖技术指标和止盈止损条件

            except Exception as e:
                print(f"  处理持仓 {stock_code} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue

        # 执行卖出
        for stock_code, price, info, reason in sell_list:
            # price在sell_list中已是"最终成交价"(开盘价附近*1.005)，这里不要再次乘以1.005
            sell_price = price
            quantity = info['quantity']
            proceeds = sell_price * quantity
            sell_fee = self.calculate_sell_fee(proceeds, stock_code=stock_code)
            net_proceeds = proceeds - sell_fee

            self.capital += net_proceeds

            # 计算盈亏
            cost = info['cost_price'] * quantity
            profit = net_proceeds - cost
            profit_rate = (profit / cost * 100) if cost > 0 else 0.0

            # 记录交易（包含盈亏信息）
            self.trades.append({
                'date': date,
                'stock_code': stock_code,
                'action': 'sell',
                'price': sell_price,
                'quantity': quantity,
                'amount': proceeds,
                'fee': sell_fee,
                'net_proceeds': net_proceeds,
                'profit': profit,
                'profit_rate': profit_rate,
                'reason': reason
            })

            # 从组合中移除
            del self.portfolio[stock_code]

            print(f"\n卖出 {stock_code}，价格(卖二): {sell_price:.2f}, 数量: {quantity}, 收入: {
                  proceeds:.2f}, 手续费: {sell_fee:.2f}, 实际所得: {net_proceeds:.2f}")
            print(f"成本: {cost:.2f}, 盈亏: {profit:.2f}, 收益率: {profit_rate:.2f}%")
            print(f"卖出原因: {reason}")

    def calculate_daily_value(self, date):
        """计算当日资产价值"""
        print(f"计算当日资产价值，日期: {date}")
        # 计算持仓价值
        portfolio_value = 0
        for stock_code, info in self.portfolio.items():
            try:
                data = self.stock_data.get(stock_code)
                if data is None:
                    print(f"  未找到 {stock_code} 的数据，跳过")
                    continue

                if not isinstance(data, pd.DataFrame):
                    print(f"  数据类型错误，期望DataFrame，实际类型: {type(data)}")
                    continue

                if date not in data.index:
                    print(f"  日期 {date} 不在 {stock_code} 的数据范围内，跳过")
                    continue

                price = data.loc[date, 'close']
                if pd.isna(price):
                    print(f"  价格数据缺失，跳过")
                    continue

                stock_value = price * info['quantity']
                portfolio_value += stock_value
                print(f"  {stock_code} 价值: {stock_value}")
            except Exception as e:
                print(f"  计算 {stock_code} 价值时出错: {e}")
                continue

        # 总价值
        total_value = self.capital + portfolio_value
        print(f"  持仓价值: {portfolio_value}")
        print(f"  现金: {self.capital}")
        print(f"  总价值: {total_value}")

        # 记录当日价值
        self.daily_values.append({
            'date': date,
            'capital': self.capital,
            'portfolio_value': portfolio_value,
            'total_value': total_value,
            'return': (total_value - self.initial_capital) / self.initial_capital * 100
        })

    def run_backtest(self, stock_list, force_download=False, period='1d'):
        """
        运行回测
        :param stock_list: 股票代码列表
        :param force_download: 是否强制下载数据（默认False，使用缓存）
        :param period: 数据周期，支持'1d'（日线）、'1m'（1分钟线）、'5m'（5分钟线）等
        """
        print(f"开始回测，时间范围: {self.start_date} 到 {self.end_date}")
        print(f"初始资金: {self.initial_capital}")
        print(f"每只股票资金分配: {self.capital_per_stock}")
        print(f"数据周期: {period}")
        print()

        # 加载股票数据
        self.load_stock_data(stock_list, force_download, period)

        if not self.stock_data:
            print("没有加载到股票数据，回测失败")
            return

        # 获取所有交易日
        all_dates = []
        for data in self.stock_data.values():
            all_dates.extend(data.index.tolist())

        if not all_dates:
            print("没有交易日数据，回测失败")
            return

        # 去重并排序
        all_dates = sorted(list(set(all_dates)))

        # 筛选回测期间的交易日
        # 将起止日期转换为datetime进行比较，避免字符串与Timestamp比较导致异常
        start_raw, end_raw = self._normalize_start_end_for_period(self.start_date, self.end_date, period)
        start_dt = pd.to_datetime(start_raw)
        end_dt = pd.to_datetime(end_raw)
        try:
            backtest_dates = [d if isinstance(d, pd.Timestamp) else pd.to_datetime(d)
                              for d in all_dates
                              if start_dt <= (d if isinstance(d, pd.Timestamp) else pd.to_datetime(d)) <= end_dt]
        except Exception as e:
            print(f"筛选回测交易日时出错: {e}")
            backtest_dates = all_dates

        print(f"回测期间共有 {len(backtest_dates)} 个交易日")
        print(f"前5个交易日: {backtest_dates[:5]}")
        print(f"后5个交易日: {backtest_dates[-5:]}")
        print()

        # 开始回测
        for date in backtest_dates:
            print(f"处理日期: {date}")
            self.simulate_trade(date)

        # 回测结束后卖出所有持仓
        if backtest_dates:
            final_date = backtest_dates[-1]
            print(f"\n回测结束，卖出所有持仓，日期: {final_date}")
            self.sell_all_holdings(final_date)

            # 计算最终价值
            self.calculate_daily_value(final_date)

            # 生成回测报告
            self.generate_report()
        else:
            print("没有回测交易日，无法完成回测")

    def sell_all_holdings(self, date):
        """卖出所有持仓"""
        print(f"\n回测结束，卖出所有持仓")

        sell_list = []
        for stock_code, info in list(self.portfolio.items()):
            try:
                data = self.stock_data.get(stock_code)
                if data is None:
                    print(f"  未找到 {stock_code} 的数据，跳过")
                    continue

                if not isinstance(data, pd.DataFrame):
                    print(f"  数据类型错误，期望DataFrame，实际类型: {type(data)}")
                    continue

                if date not in data.index:
                    print(f"  日期 {date} 不在 {stock_code} 的数据范围内，跳过")
                    continue

                price = data.loc[date, 'close']
                if pd.isna(price):
                    print(f"  价格数据缺失，跳过")
                    continue

                sell_list.append((stock_code, price, info))
            except Exception as e:
                print(f"  处理 {stock_code} 时出错: {e}")
                continue

        for stock_code, price, info in sell_list:
            try:
                # 使用卖二价（模拟为close价的100.5%）
                sell_price = price * 1.005
                quantity = info['quantity']
                cost_price = info['cost_price']
                cost = cost_price * quantity
                proceeds = sell_price * quantity
                sell_fee = self.calculate_sell_fee(proceeds, stock_code=stock_code)
                net_proceeds = proceeds - sell_fee
                profit = net_proceeds - cost
                profit_rate = (profit / cost * 100) if cost > 0 else 0.0

                self.capital += net_proceeds

                # 记录交易
                self.trades.append({
                    'date': date,
                    'stock_code': stock_code,
                    'action': 'sell',
                    'price': sell_price,
                    'quantity': quantity,
                    'amount': proceeds,
                    'fee': sell_fee,
                    'net_proceeds': net_proceeds,
                    'profit': profit,
                    'profit_rate': profit_rate,
                    'reason': '回测结束强制卖出'
                })

                # 从组合中移除
                del self.portfolio[stock_code]

                print(f"\n卖出 {stock_code}，价格(卖二): {sell_price:.2f}, 数量: {quantity}, 收入: {
                      proceeds:.2f}, 手续费: {sell_fee:.2f}, 实际所得: {net_proceeds:.2f}")
                print(f"成本: {cost:.2f}, 盈亏: {profit:.2f}, 收益率: {profit_rate:.2f}%")
                print(f"卖出原因: 回测结束强制卖出")
            except Exception as e:
                print(f"  卖出 {stock_code} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue

    def calculate_buy_fee(self, amount, stock_code: str | None = None):
        """计算买入手续费"""
        # 佣金：万分之3，最低5元
        commission = max(amount * 0.0003, 5)
        # 过户费：万分之0.2（仅沪市）
        transfer_fee = (amount * 0.00002) if self._is_sh_stock(stock_code) else 0
        return commission + transfer_fee

    def calculate_sell_fee(self, amount, stock_code: str | None = None):
        """计算卖出手续费"""
        # 佣金：万分之3，最低5元
        commission = max(amount * 0.0003, 5)
        # 过户费：万分之0.2（仅沪市）
        transfer_fee = (amount * 0.00002) if self._is_sh_stock(stock_code) else 0
        # 印花税：千分之1
        stamp_tax = amount * 0.001
        return commission + transfer_fee + stamp_tax

    def generate_report(self):
        """生成回测报告"""
        print("\n===== 回测报告 =====")

        # 计算回测结果
        if not self.daily_values:
            print("无回测数据")
            return

        # 提取回测结果
        df = pd.DataFrame(self.daily_values)
        df.set_index('date', inplace=True)

        # 确保时间索引为DatetimeIndex，便于按“交易日”聚合
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # 按交易日聚合：取每天最后一条记录作为当日收盘时的账户情况
        df_daily = df.resample('D').last().dropna(subset=['total_value'])

        if df_daily.empty:
            print("无有效的日度回测数据")
            return

        # 计算策略收益（基于日频序列）
        total_return = (df_daily['total_value'].iloc[-1] - self.initial_capital) / self.initial_capital * 100
        max_drawdown = ((df_daily['total_value'] / df_daily['total_value'].cummax() - 1) * 100).min()

        # 使用日度收益率计算夏普比率
        daily_returns = df_daily['total_value'].pct_change().dropna()
        if not daily_returns.empty and daily_returns.std() > 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 打印回测结果
        print(f"初始资金: {self.initial_capital}")
        print(f"最终资金: {df_daily['total_value'].iloc[-1]:.2f}")
        print(f"总收益率: {total_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")

        # 打印交易统计
        print(f"\n交易统计:")
        print(f"总交易次数: {len(self.trades)}")
        buy_trades = [t for t in self.trades if t['action'] == 'buy']
        sell_trades = [t for t in self.trades if t['action'] == 'sell']
        print(f"买入次数: {len(buy_trades)}")
        print(f"卖出次数: {len(sell_trades)}")

        # 计算盈亏
        if sell_trades:
            profits = [t.get('profit', 0) for t in sell_trades]
            total_profit = sum(profits)
            avg_profit = total_profit / len(sell_trades)
            win_trades = [p for p in profits if p > 0]
            win_rate = len(win_trades) / len(sell_trades) * 100
            print(f"总盈亏: {total_profit:.2f}")
            print(f"平均盈亏: {avg_profit:.2f}")
            print(f"胜率: {win_rate:.2f}%")

        # 绘制收益曲线
        plt.figure(figsize=(10, 6))
        plt.plot(df_daily.index, df_daily['total_value'], label='策略总价值')
        plt.axhline(y=self.initial_capital, color='r', linestyle='--', label='初始资金')
        plt.title('策略收益曲线')
        plt.xlabel('日期')
        plt.ylabel('总价值')
        plt.legend()
        plt.grid(True)
        plt.show()


# 主函数
if __name__ == '__main__':
    print("===== 策略回测系统 =====")

    # 创建回测器
    backtester = Backtester(
        start_date=START_DATE,
        end_date=END_DATE,
        initial_capital=INITIAL_CAPITAL,
        capital_per_stock=CAPITAL_PER_STOCK
    )

    # 确定股票列表
    if STRATEGY_CONFIG['use_index_constituents']:
        # 使用指数成分股
        index_code = INDEX_CONFIG[STRATEGY_CONFIG['target_index']]['code']
        print(f"使用 {INDEX_CONFIG[STRATEGY_CONFIG['target_index']]['name']} 成分股")
        stock_list = backtester.get_index_constituents(
            index_code, force_download=STRATEGY_CONFIG['force_download'])
        # 限制股票数量
        if len(stock_list) > STRATEGY_CONFIG['max_stocks']:
            stock_list = stock_list[:STRATEGY_CONFIG['max_stocks']]
            print(f"限制股票数量为 {STRATEGY_CONFIG['max_stocks']}")
    else:
        # 使用测试股票列表
        stock_list = TEST_STOCKS
        print("使用测试股票列表")

    if not stock_list:
        print("无股票数据，无法运行回测")
    else:
        print(f"股票列表: {stock_list[:10]}...")
        print(f"股票数量: {len(stock_list)}")

        # 运行回测（仅有日线权限时使用 1d）
        backtester.run_backtest(stock_list, force_download=STRATEGY_CONFIG['force_download'], period='1d')

    print("\n回测完成！")
