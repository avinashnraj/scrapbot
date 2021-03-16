import time

import pandas as pd

from config import *
from expert import Expert
from logger import Logger
from signals import Signal
from trade_api import Trader


class Main(object):
    api = None
    signals = dict()
    expert = dict()
    last_price_ask = 0
    last_price_bid = 0

    def __init__(self):
        self.api = Trader()
        for sym in g_symbols:
            self.signals[sym] = Signal(symbol=sym, fast_sma_shift=g_fast_sma_shift[sym],
                                       fast_sma_periods=g_fast_sma_periods[sym],
                                       slow_sma_periods=g_slow_sma_periods[sym], slow_sma_shift=g_slow_sma_shift[sym],
                                       rsi_period=g_rsi_period[sym], rsi_max=g_rsi_max[sym], rsi_min=g_rsi_min[sym],
                                       gap_distance=g_gap_distance[sym])
            self.expert[sym] = Expert(api=self.api, signals=self.signals[sym])
            self.api.init(sym, g_magic[sym])

    def run(self):
        # self.api.close_all_orders(g_symbol[symbol])
        self.heart_beat()
        self.api.close_connection()

    def heart_beat(self):
        while True:
            for sym in g_symbols:
                if self.update_price_data(sym):
                    last_price = self.api.get_last_price(sym)
                    bid = last_price.bid
                    ask = last_price.ask
                    if bid == self.last_price_bid and ask == self.last_price_ask:
                        continue
                    self.last_price_bid = bid
                    self.last_price_ask = ask

                    self.expert[sym].engine(sym=sym, ask=self.last_price_ask, bid=self.last_price_bid)
            time.sleep(0.3)

    def update_price_data(self, sym):
        if self.expert[sym].get_price_data() is None:
            new_price_data = self.api.get_candles(sym, period=g_time_frame[sym],
                                                  number=g_number_of_candles[sym])
            self.expert[sym].set_price_data(pd.DataFrame(new_price_data))
            Logger.print("Initial Price Data Received...")
            return True
        # Normal operation will update pricedata on first attempt
        data = self.api.get_candles(sym, period=g_time_frame[sym], number=g_number_of_candles[sym])
        new_price_data = pd.DataFrame(data)
        current_list = self.expert[sym].get_price_data().values[-2:-1].tolist()
        new_list = new_price_data.values[-2:-1].tolist()
        if new_list != current_list:
            self.expert[sym].set_price_data(new_price_data)
            Logger.print("updated prices found..." + str(self.expert[sym].get_price_data().values[-2:-1].tolist()))
            return True
        return False


if __name__ == "__main__":
    main = Main()
    main.run()
