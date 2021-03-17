from config import *
from logger import Logger
import traceback, sys

class Expert(object):
    price_data = None
    api = None
    signals = None

    def __init__(self, api, signals):
        self.api = api
        self.signals = signals

    def set_price_data(self, price_data):
        self.price_data = price_data

    def get_price_data(self):
        return self.price_data

    def engine(self, sym, ask, bid):
        positions = self.api.get_open_positions(symbol=sym)
        orders = self.api.get_orders(symbol=sym)

        len_positions = len(positions) if positions is not None else 0
        len_orders = len(orders) if orders is not None else 0
        total_pl = -0.0
        last_close_price = self.price_data[-1]['close']
        if len_positions == 0 and len_orders == 0:
            try:
                signal = self.signals.get(price_data=self.price_data, signal_type=g_signal_open_type[sym],
                                          current=None,
                                          point=self.api.get_point(sym))
                if signal == "Buy":
                    Logger.print(signal + ": closing Price: " + str(last_close_price))
                    tp = g_take_profit[sym]
                    sl = ((g_level_maximum[sym] - 1) * g_level_spacing[sym] if g_martingale_enable[sym] else 0 +
                                                       g_stop_loss[sym])
                    tp = ask + tp * self.api.get_point(sym)
                    sl = ask - sl * self.api.get_point(sym)
                    self.api.open_trade(symbol=sym, is_buy=True, rate=ask, amount=g_initial_volume[sym],
                                        tp=tp, sl=sl)
                    if g_martingale_enable[sym]:
                        for index in range(1, g_level_maximum[sym]):
                            amt = index * g_scale_factor[sym] * g_initial_volume[sym]
                            self.api.create_entry_order(symbol=sym, is_buy=True, amount=amt,
                                                        tp=tp,
                                                        rate=ask - index * g_level_spacing[
                                                            symbol] * self.api.get_point(sym),
                                                        sl=sl)
                elif signal == "Sell":
                    Logger.print(signal + ": closing Price: " + str(last_close_price))
                    tp = g_take_profit[sym]
                    sl = (
                        (g_level_maximum[sym] - 1) * g_level_spacing[sym] if g_martingale_enable[sym] else 0 +
                                                                                                           g_stop_loss[sym])
                    tp = bid - tp * self.api.get_point(sym)
                    sl = bid + sl * self.api.get_point(sym)
                    self.api.open_trade(symbol=sym, is_buy=False, rate=bid,
                                        amount=g_initial_volume[sym], tp=tp, sl=sl)
                    if g_martingale_enable[sym]:
                        for index in range(1, g_level_maximum[sym]):
                            amt = index * g_scale_factor[sym] * g_initial_volume[sym]
                            self.api.create_entry_order(symbol=sym, is_buy=False, amount=amt, tp=tp,
                                                        rate=bid + index * g_level_spacing[sym] * self.api.get_point(sym),
                                                        sl=sl)
            except Exception as e:
                Logger.print(str(e))
                traceback.print_exception(*sys.exc_info())
        else:
            order_type = None
            for row in positions:
                total_pl += row.profit
                order_type = row.type
            signal = self.signals.get(price_data=self.price_data, signal_type=g_signal_close_type[sym],
                                      current=self.api.get_type_str(order_type), point=self.api.get_point(sym))
            if signal == "Close":
                Logger.print(signal + ": closing Price: " + str(self.price_data[-1]['close']))
                self.api.close_all_orders(sym)
            elif g_enable_sl_to_open[sym] and total_pl > g_sl_to_open_total_profit[sym]:
                # slow ema for sl
                raw1, raw2 = self.signals.get_signal_raw(price_data=self.price_data,
                                                         signal_type=g_signal_close_type[sym])
                self.set_sell_to_safe(sym, positions, ask, bid, last_close_price, raw1)
            elif total_pl > g_min_total_profit[sym]:
                if g_enable_sl_trailing[sym]:
                    if len_orders > 0:
                        self.api.close_all_entry_orders(sym)
                    self.trail(sym, positions, ask, bid, last_close_price)
                else:
                    self.api.close_all_orders(g_symbol)
                    Logger.print("Finishing and closing all orders and got enough profit")

    def trail(self, sym, positions, ask, bid, last_close_price):
        trailing_start = g_trailing_start[sym]
        for row in positions:
            position_id = row.ticket
            if row.type == 0:
                if ask > last_close_price and ask - (
                        trailing_start + g_trailing_step[sym]) * self.api.get_point(sym) > row.sl:
                    sl = ask - trailing_start * self.api.get_point(sym)
                    self.api.change_trade_stop_limit(symbol=sym, order_type=row.type,
                                                     position_id=position_id, sl=sl, tp=row.tp)
                    Logger.print("[%s] Adjusting the buy trade stop and trailing step - %f,%f" % (position_id,
                                                                                                  last_close_price,
                                                                                                  ask))
            else:
                if bid < last_close_price and bid + (trailing_start + g_trailing_step[sym]) * self.api.get_point(
                        sym) < row.sl:
                    sl = bid + trailing_start * self.api.get_point(sym)
                    self.api.change_trade_stop_limit(symbol=sym, order_type=row.type,
                                                     position_id=position_id, sl=sl, tp=row.tp)
                    Logger.print("[%s] Adjusting the sell trade stop and trailing step - %f,%f" % (position_id,
                                                                                                   last_close_price,
                                                                                                   bid))

    def set_sell_to_safe(self, sym, positions, ask, bid, last_close_price, signal_raw):
        for row in positions:
            position_id = row.ticket
            sl = row.price_open
            if row.type == 0:
                if ask > signal_raw[-2] > row.price_open and signal_raw[-2] > row.sl:
                    sl = signal_raw[-2]
                    self.api.change_trade_stop_limit(symbol=sym, order_type=row.type,
                                                     position_id=position_id, sl=sl, tp=row.tp)
                    Logger.print("[%s] Adjusting the buy trade stop to signal value - %f,%f" % (position_id,
                                                                                                last_close_price,
                                                                                                ask))
                elif ask > last_close_price and sl != row.sl:
                    self.api.change_trade_stop_limit(symbol=sym, order_type=row.type,
                                                     position_id=position_id, sl=sl, tp=row.tp)
                    Logger.print("[%s] Adjusting the buy trade stop to open - %f,%f" % (position_id,
                                                                                        last_close_price, ask))
            else:
                if bid < signal_raw[-2] < row.price_open and signal_raw[-2] < row.sl:
                    sl = signal_raw[-2]
                    self.api.change_trade_stop_limit(symbol=sym, order_type=row.type,
                                                     position_id=position_id, sl=sl, tp=row.tp)
                    Logger.print("[%s] Adjusting the sell trade stop to signal value - %f,%f" % (position_id,
                                                                                                 last_close_price,
                                                                                                 bid))
                elif bid < last_close_price and sl != row.sl:
                    self.api.change_trade_stop_limit(symbol=sym, order_type=row.type,
                                                     position_id=position_id, sl=sl, tp=row.tp)
                    Logger.print("[%s] Adjusting the sell trade stop to open - %f,%f" % (position_id,
                                                                                         last_close_price,
                                                                                         bid))
