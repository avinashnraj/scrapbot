import signals
import trade_api
from config import *
from logger import Logger
g_sym = 'XAUUSD'
g_price_data = dict()
g_api = trade_api.Trader()
g_strategy = signals.Signal(symbol=g_sym, fast_sma_shift=g_fast_sma_shift[g_sym],
                            fast_sma_periods=g_fast_sma_periods[g_sym],
                            slow_sma_periods=g_slow_sma_periods[g_sym], slow_sma_shift=g_slow_sma_shift[g_sym],
                            rsi_period=g_rsi_period[g_sym], rsi_max=70, rsi_min=30, gap_distance=0.1)
g_last_price_ask = 0
g_last_price_bid = 0

def prepare():
    global g_price_data
    g_price_data = g_api.get_candles(g_sym, period=g_time_frame[g_sym], number=g_number_of_candles[g_sym])

def get_latest_price_data():
    global g_price_data

    # Normal operation will update pricedata on first attempt
    new_price_data = g_api.get_candles(g_sym, period=g_time_frame[g_sym], number=g_number_of_candles[g_sym])
    Logger.print(new_price_data)
    if new_price_data is not None and new_price_data[-2:-1] != g_price_data[-2:-1]:
        Logger.print("updated prices found...")
        Logger.print(g_price_data[-2:-1])
        g_price_data = new_price_data
        return True
    return False


if __name__ == "__main__":
    prepare()
    get_latest_price_data()
    g_strategy.get(price_data=g_price_data, signal_type="EMA_RSI_GAP", current=None, plot=True, point=0.01)
    # time.sleep(5)
    # g_api.close_connection()
