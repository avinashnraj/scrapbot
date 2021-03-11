import time

import signals
import mt5_trade_api
from config import *

g_price_data = dict()
g_api = mt5_trade_api.Trader(access_token=g_token, symbol=g_symbol, magic=12345, log_level='error', server='demo',
                             log_file='log.txt')
g_strategy = signals.Signal(symbol=g_symbol, fast_sma_shift=g_fast_sma_shift,
                            fast_sma_periods=g_fast_sma_periods,
                            slow_sma_periods=g_slow_sma_periods, slow_sma_shift=g_slow_sma_shift,
                            rsi_period=g_rsi_period, rsi_max=70, rsi_min=30)
g_last_price_ask = 0
g_last_price_bid = 0


def prepare():
    global g_price_data
    g_price_data = g_api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)


def get_latest_price_data():
    global g_price_data

    # Normal operation will update pricedata on first attempt
    new_price_data = g_api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
    print(new_price_data)
    if new_price_data is not None and new_price_data[-2:-1] != g_price_data[-2:-1]:
        g_api.__print__("updated prices found...")
        print(g_price_data[-2:-1])
        g_price_data = new_price_data
        return True

    # If data is not available on first attempt, try up to 3 times to update g_pricedata
    counter = 0
    while new_price_data is not None and new_price_data[-2:-1] == g_price_data[-2:-1] and counter < 3:
        g_api.__print__("No updated prices found, trying again in 1 second...")
        counter += 1
        time.sleep(0.1)
        new_price_data = g_api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
    if new_price_data[-2:-1] != g_price_data[-2:-1]:
        g_api.__print__("updated prices found...")
        print(g_price_data[-2:-1])
        g_price_data = new_price_data
        return True
    else:
        return False


if __name__ == "__main__":
    prepare()
    get_latest_price_data()
    g_strategy.get(price_data=g_price_data, signal_type="EMA_RSI", current=None, plot=True)
    # time.sleep(5)
    # g_api.close_connection()
