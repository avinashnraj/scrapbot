import time

import pandas as pd

from trade_api import Trader
from signals import Signal
from config import *
from expert import Expert


class Main(object):
    api = None
    signals = None
    expert = None
    last_price_ask = 0
    last_price_bid = 0

    def __init__(self):
        self.api = Trader(access_token=g_token, symbol=g_symbol, magic=g_magic, log_level='error', server='demo',
                          log_file='log.txt')
        self.signals = Signal(symbol=g_symbol, fast_sma_shift=g_fast_sma_shift, fast_sma_periods=g_fast_sma_periods,
                              slow_sma_periods=g_slow_sma_periods, slow_sma_shift=g_slow_sma_shift,
                              rsi_period=g_rsi_period, rsi_max=g_rsi_max, rsi_min=g_rsi_min)

        self.expert = Expert(api=self.api, signals=self.signals)

    def run(self):
        # self.api.close_all_orders(g_symbol)
        main.heart_beat()
        self.api.close_connection()

    def heart_beat(self):
        while True:
            if self.update_price_data():
                last_price = self.api.get_last_price(g_symbol)
                bid = last_price.bid
                ask = last_price.ask
                if bid == self.last_price_bid and ask == self.last_price_ask:
                    continue
                self.last_price_bid = bid
                self.last_price_ask = ask

                self.expert.engine(ask=self.last_price_ask, bid=self.last_price_bid)
            time.sleep(0.1)

    def update_price_data(self):
        if self.expert.get_price_data() is None:
            new_price_data = self.api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
            self.expert.set_price_data(new_price_data)
            self.api.__print__("Initial Price Data Received...")
            return True
        # Normal operation will update pricedata on first attempt
        new_price_data = self.api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
        if new_price_data[-2:-1] != self.expert.get_price_data()[-2:-1]:
            self.expert.set_price_data(new_price_data)
            data_frame = pd.DataFrame(self.expert.get_price_data()[-2:-1])
            data_frame['time'] = pd.to_datetime(data_frame['time'], unit='s')
            self.api.__print__("updated prices found..." + str(data_frame.values.tolist()))
            return True
        return False


if __name__ == "__main__":
    main = Main()
    main.run()
