# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 17:09:46 2021

@author: Avinash
"""
import MetaTrader5 as Mt5
import time
from logger import Logger


class Trader(object):
    access_token = None
    log_level = None
    server = None
    log_file = None
    connection = Mt5
    symbol_point = None
    magic = None

    def __init__(self, symbol, magic):
        self.magic = magic
        Logger.print("MetaTrader5 package author: " + self.connection.__author__)
        Logger.print("MetaTrader5 package version: " + self.connection.__version__)

        if not self.connection.initialize():
            Logger.print("initialize() failed, error code =" + self.connection.last_error())
            quit()
        self.symbol_point = self.get_symbol_info(symbol).point

    def subscribe_market_data(self, symbol):
        pass

    def close_all_orders(self, symbol):
        max_tries = 1
        while max_tries > 0:
            positions = self.get_open_positions(symbol=symbol)
            if positions is None:
                Logger.print("No positions on " + symbol + ", error code={}".format(self.connection.last_error()))
            elif len(positions) > 0:
                Logger.print("Total positions on " + symbol + " =" + len(positions))
                # display all open positions
                info = self.connection.symbol_info_tick(symbol)
                for position in positions:
                    order = {
                        "action": self.connection.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": position.volume,
                        "type": self.connection.ORDER_TYPE_SELL if position.type == self.connection.ORDER_TYPE_BUY
                        else self.connection.ORDER_TYPE_BUY,
                        "price": info.bid if position.type == self.connection.ORDER_TYPE_BUY else info.ask,
                        "deviation": 10,
                        "position": position.ticket,
                        "type_filling": self.connection.ORDER_FILLING_IOC
                    }
                    self.connection.order_send(order)

            orders = self.get_orders(symbol=symbol)
            if orders is None:
                Logger.print("No orders on " + symbol + ", error code={}".format(self.connection.last_error()))
            elif len(orders) > 0:
                Logger.print("Total orders on " + symbol + ":" + len(orders))
                # display all active orders
                for order in orders:
                    request = {
                        "action": self.connection.TRADE_ACTION_REMOVE,
                        "order": order.ticket
                    }
                    self.connection.order_send(request)
            if len(self.get_orders(symbol=symbol)) == 0 and len(self.get_open_positions(symbol=symbol)) == 0:
                break
            Logger.print("Failed retrying delete - orders: %d, open_orders: %d" %
                         (self.connection.orders_total(), self.connection.positions_total()))
            max_tries -= 1
            time.sleep(0.1)

    def get_point(self):
        return self.symbol_point

    def get_symbol_info(self, symbol):
        symbol_info = self.connection.symbol_info(symbol)
        if symbol_info is None:
            Logger.print(symbol + "not found, can not call order_check()")
            self.connection.shutdown()
            quit()

        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            Logger.print(symbol + "is not visible, trying to switch on")
            if not self.connection.symbol_select(symbol, True):
                Logger.print("symbol_select(%s) failed, exit" % (symbol))
                self.connection.shutdown()
                quit()
            point = self.connection.symbol_info(symbol).point
        return self.connection.symbol_info(symbol)

    @staticmethod
    def get_type_str(order_type):
        if order_type == Mt5.ORDER_TYPE_BUY:
            return "Buy"
        elif order_type == Mt5.ORDER_TYPE_SELL:
            return "Sell"
        elif order_type == Mt5.ORDER_TYPE_BUY_LIMIT:
            return "BuyLimit"
        elif order_type == Mt5.ORDER_TYPE_SELL_LIMIT:
            return "SellLimit"
        elif order_type == Mt5.ORDER_TYPE_BUY_STOP:
            return "BuyStop"
        elif order_type == Mt5.ORDER_TYPE_SELL_STOP:
            return "SellStop"
        else:
            return None

    def close_all_entry_orders(self, symbol):
        max_tries = 1
        while max_tries > 0:
            orders = self.get_orders(symbol=symbol)
            if orders is None:
                Logger.print("No orders on " + symbol + ", error code={}".format(self.connection.last_error()))
            elif len(orders) > 0:
                Logger.print("Total orders on " + symbol + ":" + len(orders))
                # display all active orders
                for order in orders:
                    request = {
                        "action": self.connection.TRADE_ACTION_REMOVE,
                        "order": order.ticket
                    }
                    self.connection.order_send(request)

                if len(self.get_orders(symbol=symbol)) == 0:
                    break
                Logger.print("Failed retrying delete - orders")
                max_tries -= 1
                time.sleep(0.1)

    def open_trade(self, symbol, amount, rate, tp, sl, is_buy):
        symbol_info = self.connection.symbol_info(symbol)
        if symbol_info is None:
            Logger.print(symbol + "not found, can not call order_check()")
            self.connection.shutdown()
            quit()

        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            Logger.print(symbol + "is not visible, trying to switch on")
            if not self.connection.symbol_select(symbol, True):
                Logger.print("symbol_select({}}) failed, exit" + symbol)
                self.connection.shutdown()
                quit()

        max_tries = 1
        while max_tries > 0:
            try:
                lot = amount
                point = self.connection.symbol_info(symbol).point
                price = rate
                deviation = 20
                request = {
                    "action": self.connection.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": lot,
                    "type": self.connection.ORDER_TYPE_BUY if is_buy else self.connection.ORDER_TYPE_SELL,
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": deviation,
                    "magic": self.magic,
                    "comment": "scrapbot open",
                    "type_time": self.connection.ORDER_TIME_GTC,
                    "type_filling": self.connection.ORDER_FILLING_IOC,
                }
                result = self.connection.order_send(request)
                if result.retcode != self.connection.TRADE_RETCODE_DONE:
                    Logger.print(
                        "Failed opening a new market %s with size %f, with reason %d:%s" %
                        ("buy" if is_buy else "sell", amount, result.retcode, result.comment))
            except Exception as ex:
                Logger.print("Exception: Failed opening a new market %s with size %f, %s" % (
                    "buy" if (is_buy is True) else "sell", amount, str(ex)))
            max_tries -= 1

    def create_entry_order(self, symbol, is_buy, amount, tp, rate, sl, trailing_step=None):
        symbol_info = self.connection.symbol_info(symbol)
        if symbol_info is None:
            Logger.print(symbol + "not found, can not call order_check()")
            self.connection.shutdown()
            quit()

        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            Logger.print(symbol + "is not visible, trying to switch on")
            if not self.connection.symbol_select(symbol, True):
                Logger.print("symbol_select(%s) failed, exit" % (symbol))
                self.connection.shutdown()
                quit()
        max_tries = 1
        while max_tries > 0:
            try:
                lot = amount
                point = self.connection.symbol_info(symbol).point
                price = rate
                deviation = 20
                request = {
                    "action": self.connection.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": lot,
                    "type": self.connection.ORDER_TYPE_BUY_LIMIT if is_buy else self.connection.ORDER_TYPE_SELL_LIMIT,
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": deviation,
                    "magic": self.magic,
                    "comment": "scrapbot open",
                    "type_time": self.connection.ORDER_TIME_GTC,
                    "type_filling": self.connection.ORDER_FILLING_IOC
                }
                result = self.connection.order_send(request)
                if result.retcode != self.connection.TRADE_RETCODE_DONE:
                    Logger.print(
                        "Failed opening a new entry %s with size %f, with reason %d:%s" %
                        ("buy" if (is_buy is True) else "sell", amount, result.retcode, result.comment))
            except Exception as ex:
                Logger.print("Exception: Failed opening a new entry %s with size %f, %s" % (
                    "buy" if (is_buy is True) else "sell", amount, str(ex)))
            max_tries -= 1

    def get_last_price(self, symbol):
        return self.connection.symbol_info_tick(symbol)

    def get_open_positions(self, symbol=None):
        positions = self.connection.positions_get(symbol=symbol)
        return list(filter(self.filter_magic, positions))

    def get_orders(self, symbol):
        orders = self.connection.orders_get(symbol=symbol)
        return list(filter(self.filter_magic, orders))

    def filter_magic(self, position):
        if position.magic == self.magic:
            return True
        else:
            return False

    def close_connection(self):
        return self.connection.shutdown()

    def get_timeframe(self, period):
        timeperiod = self.connection.TIMEFRAME_M1
        if period == "m1":
            timeperiod = self.connection.TIMEFRAME_M1
        elif period == "m5":
            timeperiod = self.connection.TIMEFRAME_M5
        elif period == "m15":
            timeperiod = self.connection.TIMEFRAME_M15
        elif period == "m30":
            timeperiod = self.connection.TIMEFRAME_M30
        elif period == "H1":
            timeperiod = self.connection.TIMEFRAME_H1
        elif period == "H4":
            timeperiod = self.connection.TIMEFRAME_H4
        return timeperiod

    def get_candles(self, symbol, period, number, start=0):
        return self.connection.copy_rates_from_pos(symbol, self.get_timeframe(period), start, number)

    def is_connected(self):
        return True

    def change_trade_stop_limit(self, symbol, order_type, position_id, sl, tp):
        max_tries = 1
        while max_tries > 0:
            try:
                request = {
                    "action": self.connection.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "position": position_id,
                    "sl": sl,
                    "tp": tp,
                    "magic": self.magic
                }
                # send a trading request
                result = self.connection.order_send(request)
                # check the execution result
                if result is None or (result is not None and result.retcode != self.connection.TRADE_RETCODE_DONE):
                    Logger.print(
                        "Failed modifying the %s position %d, with reason (%s)" %
                        ("buy" if (order_type == 0) else "sell", position_id,
                         result if result is None else result.comment))
                else:
                    Logger.print(
                        "Modified the %s position %d" % ("buy" if (order_type == 0) else "sell", position_id))
            except Exception as ex:
                Logger.print("Exception: Failed opening a new entry %s with %s" % (
                    "buy" if (order_type == 0) else "sell", str(ex)))
            max_tries -= 1
