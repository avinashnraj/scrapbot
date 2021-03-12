import time

import pandas as pd

import mt5_trade_api
import signals
from config import *

g_price_data = dict()
g_api = mt5_trade_api.Trader(access_token=g_token, symbol=g_symbol, magic=g_magic, log_level='error', server='demo',
                             log_file='log.txt')
g_signals = signals.Signal(symbol=g_symbol, fast_sma_shift=g_fast_sma_shift, fast_sma_periods=g_fast_sma_periods,
                           slow_sma_periods=g_slow_sma_periods, slow_sma_shift=g_slow_sma_shift,
                           rsi_period=g_rsi_period, rsi_max=g_rsi_max, rsi_min=g_rsi_min)
g_last_price_ask = 0
g_last_price_bid = 0


def prepare():
    global g_price_data
    g_api.__print__("Requesting Initial Price Data...")
    g_price_data = g_api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
    g_api.__print__("Initial Price Data Received...")


def strategy_heart_beat():
    while True:
        get_latest_price_data()
        engine()
        time.sleep(0.1)


def get_latest_price_data():
    global g_price_data
    # Normal operation will update pricedata on first attempt
    new_price_data = g_api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
    if new_price_data[-2:-1] != g_price_data[-2:-1]:
        g_price_data = new_price_data
        data_frame = pd.DataFrame(g_price_data[-2:-1])
        data_frame['time'] = pd.to_datetime(data_frame['time'], unit='s')
        g_api.__print__("updated prices found..." + str(data_frame.values.tolist()))
        return True

    # If data is not available on first attempt, try up to 3 times to update g_pricedata
    counter = 0
    while new_price_data[-2:-1] == g_price_data[-2:-1] and counter < 3:
        # g_api.__print__("No updated prices found, trying again in 1 second...")
        counter += 1
        time.sleep(0.1)
        new_price_data = g_api.get_candles(g_symbol, period=g_time_frame, number=g_number_of_candles)
    if new_price_data[-2:-1] != g_price_data[-2:-1]:
        # g_api.__print__("updated prices found...")
        g_price_data = new_price_data
        data_frame = pd.DataFrame(g_price_data[-2:-1])
        data_frame['time'] = pd.to_datetime(data_frame['time'], unit='s')
        g_api.__print__("updated prices found..." + str(data_frame.values.tolist()))
        return True
    else:
        return False


def engine():
    global g_api, g_last_price_ask, g_last_price_bid

    last_price = g_api.get_last_price(g_symbol)
    bid = last_price.bid
    ask = last_price.ask

    if bid == g_last_price_bid and ask == g_last_price_ask:
        return
    g_last_price_bid = bid
    g_last_price_ask = ask

    positions = g_api.get_open_positions(symbol=g_symbol)
    orders = g_api.get_orders(symbol=g_symbol)

    len_positions = len(positions) if positions is not None else 0
    len_orders = len(orders) if orders is not None else 0
    total_pl = -0.0
    last_close_price = g_price_data['close'][-2:-1]
    if len_positions == 0 and len_orders == 0:
        try:
            signal = g_signals.get(price_data=g_price_data, signal_type=g_signal_open_type, current=None)
            if signal == "Buy":
                g_api.__print__(signal + ": closing Price: " + str(last_close_price))
                tp = g_take_profit
                sl = ((g_level_maximum - 1) * g_level_spacing if g_martingale_enable else 0 + g_stop_loss)
                tp = ask + tp * g_api.get_point()
                sl = ask - sl * g_api.get_point()
                g_api.open_trade(symbol=g_symbol, is_buy=True, rate=ask, amount=g_initial_volume, tp=tp, sl=sl)
                if g_martingale_enable:
                    for index in range(1, g_level_maximum):
                        amt = index * g_scale_factor * g_initial_volume
                        g_api.create_entry_order(symbol=g_symbol, is_buy=True, amount=amt,
                                                 tp=tp, rate=ask - index * g_level_spacing * g_api.get_point(), sl=sl)
            elif signal == "Sell":
                g_api.__print__(signal + ": closing Price: " + str(last_close_price))
                tp = g_take_profit
                sl = ((g_level_maximum - 1) * g_level_spacing if g_martingale_enable else 0 + g_stop_loss)
                tp = bid - tp * g_api.get_point()
                sl = bid + sl * g_api.get_point()
                g_api.open_trade(symbol=g_symbol, is_buy=False, rate=bid, amount=g_initial_volume, tp=tp, sl=sl)
                if g_martingale_enable:
                    for index in range(1, g_level_maximum):
                        amt = index * g_scale_factor * g_initial_volume
                        g_api.create_entry_order(symbol=g_symbol, is_buy=False, amount=amt,
                                                 tp=tp, rate=bid + index * g_level_spacing * g_api.get_point(), sl=sl)
        except Exception as e:
            g_api.__print__(str(e))
    else:
        order_type = None
        for row in positions:
            total_pl += row.profit
            order_type = row.type
        signal = g_signals.get(price_data=g_price_data, signal_type=g_signal_close_type,
                               current=g_api.get_type_str(order_type))
        if signal == "Close":
            g_api.__print__(signal + ": closing Price: " + str(g_price_data['close'][-1:]))
            g_api.close_all_orders(g_symbol)
        elif g_enable_sl_to_open and total_pl > g_sl_to_open_total_profit:
            # slow ema for sl
            raw1, raw2 = g_signals.get_signal_raw(price_data=g_price_data, signal_type=g_signal_close_type)
            set_sell_to_safe(positions, ask, bid, last_close_price, raw1)
        elif total_pl > g_min_total_profit:
            if g_enable_sl_trailing:
                if len_orders > 0:
                    g_api.close_all_entry_orders(g_symbol)
                trail(positions, ask, bid, last_close_price)
            else:
                g_api.close_all_orders(g_symbol)
                g_api.__print__("Finishing and closing all orders and got enough profit")


def trail(positions, ask, bid, last_close_price):
    trailing_start = g_trailing_start
    for row in positions:
        position_id = row.ticket
        if row.type == 0:
            if ask > last_close_price and ask - (trailing_start + g_trailing_step) * g_api.get_point() > row.sl:
                sl = ask - trailing_start * g_api.get_point()
                g_api.change_trade_stop_limit(symbol=g_symbol, order_type=row.type,
                                              position_id=position_id, sl=sl, tp=row.tp)
                g_api.__print__("[%s] Adjusting the buy trade stop and trailing step - %f,%f" % (position_id,
                                                                                                 last_close_price, ask))
        else:
            if bid < last_close_price and bid + (trailing_start + g_trailing_step) * g_api.get_point() < row.sl:
                sl = bid + trailing_start * g_api.get_point()
                g_api.change_trade_stop_limit(symbol=g_symbol, order_type=row.type,
                                              position_id=position_id, sl=sl, tp=row.tp)
                g_api.__print__("[%s] Adjusting the sell trade stop and trailing step - %f,%f" % (position_id,
                                                                                                  last_close_price,
                                                                                                  bid))


def set_sell_to_safe(positions, ask, bid, last_close_price, signal_raw):
    for row in positions:
        position_id = row.ticket
        sl = row.price_open
        if row.type == 0:
            if ask > signal_raw[-2] > row.price_open and signal_raw[-2] > row.sl:
                sl = signal_raw[-2]
                g_api.change_trade_stop_limit(symbol=g_symbol, order_type=row.type,
                                              position_id=position_id, sl=sl, tp=row.tp)
                g_api.__print__("[%s] Adjusting the buy trade stop to signal value - %f,%f" % (position_id,
                                                                                       last_close_price, ask))
            elif ask > last_close_price and sl != row.sl:
                g_api.change_trade_stop_limit(symbol=g_symbol, order_type=row.type,
                                              position_id=position_id, sl=sl, tp=row.tp)
                g_api.__print__("[%s] Adjusting the buy trade stop to open - %f,%f" % (position_id,
                                                                                       last_close_price, ask))
        else:
            if bid < signal_raw[-2] < row.price_open and signal_raw[-2] < row.sl:
                sl = signal_raw[-2]
                g_api.change_trade_stop_limit(symbol=g_symbol, order_type=row.type,
                                              position_id=position_id, sl=sl, tp=row.tp)
                g_api.__print__("[%s] Adjusting the sell trade stop to signal value - %f,%f" % (position_id,
                                                                                         last_close_price,
                                                                                            bid))
            elif bid < last_close_price and sl != row.sl:
                g_api.change_trade_stop_limit(symbol=g_symbol, order_type=row.type,
                                              position_id=position_id, sl=sl, tp=row.tp)
                g_api.__print__("[%s] Adjusting the sell trade stop to open - %f,%f" % (position_id,
                                                                                        last_close_price,
                                                                                        bid))


if __name__ == "__main__":
    # g_api.close_all_orders(g_symbol)
    prepare()  # Initialize strategy
    strategy_heart_beat()
    g_api.close_connection()
