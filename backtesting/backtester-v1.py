from datetime import datetime

import backtrader as bt
import pandas as pd

from config import *
from expert import Expert
from logger import Logger
from signals import Signal

symbol = 'XAUUSD'
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


class TestTrader(bt.Strategy):
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

    def __init__(self):
        self.signals = Signal(symbol=g_symbol[symbol], fast_sma_shift=g_fast_sma_shift[symbol], fast_sma_periods=g_fast_sma_periods[symbol],
                              slow_sma_periods=g_slow_sma_periods[symbol], slow_sma_shift=g_slow_sma_shift[symbol],
                              rsi_period=g_rsi_period[symbol], rsi_max=g_rsi_max[symbol], rsi_min=g_rsi_min[symbol], gap_distance=g_gap_distance[symbol])
        self.api = self
        self.expert = Expert(api=self, signals=self.signals)

        ma_fast = bt.ind.SMA(period=g_fast_sma_periods[symbol])
        ma_slow = bt.ind.SMA(period=g_slow_sma_periods[symbol])
        self.crossover = bt.ind.CrossOver(ma_fast, ma_slow)
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=14)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            #Logger.print('ORDER ACCEPTED/SUBMITTED ' + str(order.created.dt))
            self.order = order
            return

        if order.status in [order.Expired]:
            Logger.print('BUY EXPIRED')

        elif order.status in [order.Completed]:
            if order.isbuy():
                Logger.print(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                pass
            else:  # Sell
                Logger.print('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                pass
        # Sentinel to None: new orders allowed
        self.order = None

    def next(self):
        self.update_price_data()
        bid = ask = self.data.close[0]
        #print(ask, bid, len(self.data.close))
        #print(len(self.expert.get_price_data().values))

        if len(self.expert.get_price_data().values) > 0:
            self.expert.engine(symbol, ask, bid)

    def update_price_data(self):
        new_price_data = self.api.get_candles(g_symbol[symbol], period=g_time_frame[symbol], number=g_number_of_candles[symbol])
        self.expert.set_price_data(new_price_data)
        # Logger.print( self.expert.get_price_data())
        return True

    @staticmethod
    def __print__(print_str):
        print("[%s] %s" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), print_str))

    def subscribe_market_data(self, symbol):
        pass

    def close_all_orders(self, symbol):
        if self.position:

            self.close()
        #self.positions.pop()

    def get_point(self, symbol):
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
        result = list()
        if self.position:
            p = Position()
            p.size = 1
            p.type = 0
            p.position = self.position
            result.append(p)
        # for position in self.getpositions():
        #     p = Position()
        #     p.size = position.size
        #     p.type = 0
        #     p.position = position
        #     result.append(p)
        #print(result)
        return result

    def get_orders(self, symbol):
        return list()

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
        # df['time'] = self.data.volume
        o = []
        h = []
        l = []
        c = []
        v = []
        try:
            if len(self.data.open) > number:
                for i in range(number):
                    o.append(self.data.open[number - 1 - i])
                    h.append(self.data.high[number - 1 - i])
                    l.append(self.data.low[number - 1 - i])
                    c.append(self.data.close[number - 1 - i])
                    v.append(self.data.volume[number - 1 - i])
        except Exception:
            pass
        df['open'] = o
        df['high'] = h
        df['low'] = l
        df['close'] = c
        df['volume'] = v
        return df

    def is_connected(self):
        return True

    def change_trade_stop_limit(self, symbol, order_type, position_id, sl, tp):
        pass


cerebro = bt.Cerebro()

data = bt.feeds.GenericCSVData(
    dataname='XAUUSD_M1_v1-1.csv',
    timeframe=bt.TimeFrame.Minutes,
    nullvalue=0.0,
    dtformat=('%Y.%m.%d'),
    tmformat=('%H:%M'),
    datetime=0,
    time=1,
    high=2,
    low=3,
    open=4,
    close=5,
    volume=6,
    openinterest=-1
)


cerebro.adddata(data)
cerebro.addstrategy(TestTrader)
cerebro.broker.setcash(10000.0)
# Add a FixedSize sizer according to the stake
cerebro.addsizer(bt.sizers.FixedSize, stake=0.2)
cerebro.broker.setcommission(commission=0.001)
# erebro.addsizer(bt.sizers.PercentSizer, percents = 10)

# cerebro.addanalyzer(btanalysers.SharpeRatio, _name="sharpe")
# cerebro.addanalyzer(btanalysers.Transactions, _name="trans")
# cerebro.addanalyzer(btanalysers.TradeAnalyzer, _name="trades")
# Print out the starting conditions
print('Starting Portfolio Value: %.8f' % cerebro.broker.getvalue())

back = cerebro.run()

# print(cerebro.broker.getvalue() - cerebro.broker.getcash())

# print(back[0].analyzers.sharpe.get_analysis())
# print(back[0].analyzers.trans.get_analysis())
# print(back[0].analyzers.trades.get_analysis())

# Print out the final result
print('Final Portfolio Value: %.8f' % cerebro.broker.getvalue())

cerebro.plot(style='candlestick', barup='green', bardown='red')
