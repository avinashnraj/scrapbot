from datetime import datetime

import backtrader as bt
from config import *
from expert import Expert
from logger import Logger
from signals import Signal
import numpy as np

symbol = 'XAUUSD'


class Position(object):
    size = 0.0
    profit = 0
    type = 0
    ticket = 0
    sl = 0
    tp = 0
    order = None

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
    dt = np.dtype([('time', np.float64), ('open', np.float64), ('high', np.float64), ('low', np.float64),
                   ('close', np.float64), ('volume', np.uint64), ('openinterest', np.uint64)])
    candles = list()
    def __init__(self):
        self.signals = Signal(symbol=g_symbol[symbol], fast_sma_shift=g_fast_sma_shift[symbol],
                              fast_sma_periods=g_fast_sma_periods[symbol],
                              slow_sma_periods=g_slow_sma_periods[symbol], slow_sma_shift=g_slow_sma_shift[symbol],
                              rsi_period=g_rsi_period[symbol], rsi_max=g_rsi_max[symbol], rsi_min=g_rsi_min[symbol],
                              gap_distance=g_gap_distance[symbol])
        self.api = self
        self.expert = Expert(api=self, signals=self.signals)
        ma_fast = bt.talib.SMA(self.data.close, timeperiod=g_fast_sma_periods[symbol], plotname='TA_SMA_SLOW')
        #bt.indicators.SMA(self.data, period=g_fast_sma_periods[symbol])
        ma_slow = bt.talib.SMA(self.data.close, timeperiod=g_slow_sma_periods[symbol], plotname='TA_SMA_SLOW')
        #bt.indicators.SMA(self.data, period=g_slow_sma_periods[symbol])

        #ma_fast = bt.ind.SMA(period=g_fast_sma_periods[symbol])
        #ma_slow = bt.ind.SMA(period=g_slow_sma_periods[symbol])
        self.crossover = bt.ind.CrossOver(ma_fast, ma_slow)
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=g_rsi_period[symbol])

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            # Logger.print('ORDER ACCEPTED/SUBMITTED ' + str(order.created.dt))
            self.order = order
            return

        if order.status in [order.Expired]:
            Logger.print('BUY EXPIRED')

        elif order.status in [order.Completed]:
            p = Position()
            p.size = 1
            p.position = order
            if order.isbuy():
                p.type = 0
                Logger.print(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                pass
            else:  # Sell
                p.type = 1
                Logger.print('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                             (order.executed.price,
                              order.executed.value,
                              order.executed.comm))
                pass
            self.positions.append(p)
        # Sentinel to None: new orders allowed

        self.order = None

    def next(self):
        # if self.crossover > 0:  # if fast crosses slow to the upside
        #     if self.position:
        #         self.close()
        #     self.buy()  # enter long
        # elif self.crossover < 0:  # in the market & cross to the downside
        #     if self.position:
        #         self.close()  # close long position
        #     self.sell()
        #print(self.data.open[0], self.data.high[0], self.data.low[0], self.data.close[0])
        self.update_price_data()
        ask = self.data.open[0]
        bid = self.data.open[0]
        if len(self.expert.get_price_data()) > 0:
            self.expert.engine(symbol, ask, bid)

    def update_price_data(self):
        new_price_data = self.api.get_candles(g_symbol[symbol], period=g_time_frame[symbol],
                                              number=g_number_of_candles[symbol])
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
        self.positions.clear()

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
            pos = self.buy()
            p.type = 0
            p.position = pos
            self.positions.append(p)
        else:
            pos = self.sell()
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
        if len(self.candles) == 0:
            for index in range(self.data.close.lencount):
                count = index
                self.candles.append((self.data.datetime.array[count], self.data.open.array[count], self.data.high.array[count],
                                     self.data.low.array[count], self.data.close.array[count],
                                     self.data.volume.array[count], self.data.openinterest.array[count]))
        else:
            self.candles.append((self.data.datetime[0], self.data.open[0], self.data.high[0],
                                 self.data.low[0], self.data.close[0],
                                 self.data.volume[0], self.data.openinterest[0]))
        ts = np.array(self.candles, dtype=self.dt)
        return ts

    def is_connected(self):
        return True

    def change_trade_stop_limit(self, symbol, order_type, position_id, sl, tp):
        pass


cerebro = bt.Cerebro()

data = bt.feeds.GenericCSVData(
    dataname='XAUUSD_M1_v1-2.csv',
    timeframe=bt.TimeFrame.Minutes,
    nullvalue=0.0,
    dtformat=('%Y.%m.%d'),
    tmformat=('%H:%M'),
    datetime=0,
    time=1,
    open=2,
    high=3,
    low=4,
    close=5,
    volume=6,
    openinterest=-1
)

cerebro.adddata(data)
cerebro.addstrategy(TestTrader)
cerebro.broker.setcash(10000.0)
# Add a FixedSize sizer according to the stake
cerebro.addsizer(bt.sizers.FixedSize, stake=0.01)
cerebro.broker.setcommission(commission=0.0001)
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
