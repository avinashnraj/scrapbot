import time

import pandas as pd

from trade_api import Trader

from signals import Signal
from config import *
from expert import Expert
from logger import Logger


class Main(object):
    api = None
    signals = None
    expert = None
    last_price_ask = 0
    last_price_bid = 0

    def __init__(self):
        self.api = Trader(symbol=g_symbol, magic=g_magic)
        self.signals = Signal(symbol=g_symbol, fast_sma_shift=g_fast_sma_shift, fast_sma_periods=g_fast_sma_periods,
                              slow_sma_periods=g_slow_sma_periods, slow_sma_shift=g_slow_sma_shift,
                              rsi_period=g_rsi_period, rsi_max=g_rsi_max, rsi_min=g_rsi_min,
                              gap_distance=g_gap_distance)

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
            self.expert.set_price_data(pd.DataFrame(new_price_data))
            Logger.print("Initial Price Data Received...")
            return True
        # Normal operation will update pricedata on first attempt
        data = self.api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
        new_price_data = pd.DataFrame(data)
        current_list = self.expert.get_price_data().values[-2:-1].tolist()
        new_list = new_price_data.values[-2:-1].tolist()
        if new_list != current_list:
            self.expert.set_price_data(new_price_data)
            Logger.print("updated prices found..." + str(self.expert.get_price_data().values[-2:-1].tolist()))
            return True
        return False


if __name__ == "__main__":
    main = Main()
    main.run()
