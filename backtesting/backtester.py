from datetime import datetime
from os.path import dirname, join

import pandas as pd
from backtesting import Backtest, Strategy

from config import *
from expert import Expert
from signals import Signal
from backtesting.test import SMA


class Position(object):
    size = 0.0
    profit = 0
    type = 0
    ticket = 0
    sl = 0
    tp = 0
    position = None

    def __init__(self):
        pass


class TestTrader(Strategy):
    access_token = None
    log_level = None
    server = None
    log_file = None
    connection = None
    symbol_point = 0.01
    magic = None
    candle_data = None
    positions = list()
    api = None
    signals = None
    expert = None
    fast_ma = None
    slow_ma = None

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        self.signals = Signal(symbol=g_symbol, fast_sma_shift=g_fast_sma_shift, fast_sma_periods=g_fast_sma_periods,
                              slow_sma_periods=g_slow_sma_periods, slow_sma_shift=g_slow_sma_shift,
                              rsi_period=g_rsi_period, rsi_max=g_rsi_max, rsi_min=g_rsi_min)
        self.api = self
        self.expert = Expert(api=self, signals=self.signals)

    def init(self):
        candle_data = self.data.Close
        self.fast_ma = self.I(SMA, candle_data, g_fast_sma_periods)
        self.slow_ma = self.I(SMA, candle_data, g_slow_sma_periods)

    def next(self):
        self.update_price_data()
        bid = ask = self.data.Close[-1:][0]
        self.expert.engine(ask, bid)

    def update_price_data(self):
        new_price_data = self.api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
        self.expert.set_price_data(new_price_data)
        return True

    @staticmethod
    def __print__(print_str):
        print("[%s] %s" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), print_str))

    def subscribe_market_data(self, symbol):
        pass

    def close_all_orders(self, symbol):
        if not self.position:
            self.position.close()
        self.positions.pop()

    def get_point(self):
        return self.symbol_point

    def get_symbol_info(self, symbol):
        return None

    @staticmethod
    def get_type_str(order_type):
        if order_type == 0:
            return "Buy"
        elif order_type == 1:
            return "Sell"
        else:
            return None

    def close_all_entry_orders(self, symbol):
        for order in self.orders:
            order.cancel()

    def open_trade(self, symbol, amount, rate, tp, sl, is_buy):
        p = Position()
        p.size = amount
        if is_buy:
            pos = self.buy(size=amount)
            p.type = 0
            p.position = pos
            self.positions.append(p)
        else:
            pos = self.sell(size=amount)
            p.type = 1
            p.position = pos
            self.positions.append(p)

    def create_entry_order(self, symbol, is_buy, amount, tp, rate, sl, trailing_step=None):
        pass

    def get_last_price(self, symbol):
        return None

    def get_open_positions(self, symbol=None):
        return self.positions

    def get_orders(self, symbol):
        return self.orders

    def filter_magic(self, position):
        if position.magic == self.magic:
            return True
        else:
            return False

    def close_connection(self):
        pass

    def get_timeframe(self, period):
        return "m1"

    def get_candles(self, symbol, period, number, start=0):
        df = pd.DataFrame()
        df['time'] = self.data.df.index
        df['open'] = self.data.df['Open'].values
        df['high'] = self.data.df['High'].values
        df['low'] = self.data.df['Low'].values
        df['close'] = self.data.df['Close'].values
        df['volume'] = self.data.df['Volume'].values
        # print(df)
        return df

    def is_connected(self):
        return True

    def change_trade_stop_limit(self, symbol, order_type, position_id, sl, tp):
        pass


XAUUSD = pd.read_csv(join(dirname(__file__), 'XAUUSD_M1.csv'),
                     index_col=0, parse_dates=True, infer_datetime_format=True)

bt = Backtest(XAUUSD.tail(300), TestTrader, commission=0.01, exclusive_orders=True, hedging=True)
stats = bt.run()
bt.plot(superimpose=False)
