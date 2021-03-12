
import random

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import talib


class Signal(object):
    fast_sma_periods = None
    slow_sma_periods = None
    fast_sma_shift = None
    slow_sma_shift = None
    rsi_period = None
    rsi_max = None
    rsi_min = None
    symbol = None

    def __init__(self, symbol, fast_sma_periods, slow_sma_periods, fast_sma_shift, slow_sma_shift, rsi_period, rsi_max,
                 rsi_min):
        self.fast_sma_periods = fast_sma_periods
        self.slow_sma_periods = slow_sma_periods
        self.fast_sma_shift = fast_sma_shift
        self.slow_sma_shift = slow_sma_shift
        self.rsi_period = rsi_period
        self.rsi_max = rsi_max
        self.rsi_min = rsi_min
        self.symbol = symbol

    def get(self, price_data, signal_type, current, plot=False):
        if signal_type == "EMA_RSI":
            return self.ema_rsi(price_data, signal_type, current, plot)
        elif signal_type == "EMA":
            return self.ema(price_data, signal_type, current, plot)
        elif signal_type == "TEST":
            return self.test(price_data, signal_type, current, plot)
        return "None"

    def ema_rsi(self, price_data, signal_type, current, plot=False):
        data_frame = pd.DataFrame(price_data)

        fast_sma_periods = str(self.fast_sma_periods) + '_' + signal_type
        slow_sma_periods = str(self.slow_sma_periods) + '_' + signal_type

        close_list = data_frame['close'].tolist()
        slow = talib.EMA(np.asarray(close_list), timeperiod=self.slow_sma_periods)
        fast = talib.EMA(np.asarray(close_list), timeperiod=self.fast_sma_periods)
        data_frame[slow_sma_periods] = slow
        data_frame[fast_sma_periods] = fast
        data_frame['ma_signal'] = np.where(data_frame[slow_sma_periods] < data_frame[fast_sma_periods], 1.0, 0.0)

        data_frame['ma_signal'] = data_frame['ma_signal'].diff()
        data_frame['rsi'] = talib.RSI(np.asarray(close_list), timeperiod=self.rsi_period)
        data_frame['rsi_signal'] = np.where(data_frame['rsi'] > self.rsi_max, 1.0, 0.0) + np.where(
            data_frame['rsi'] < self.rsi_min, -1.0, 0.0)

        data_frame['signal'] = np.where((data_frame['rsi_signal'] == 1) & (data_frame['ma_signal'] == 1), 1.0,
                                        0) + np.where(
            (data_frame['rsi_signal'] == -1) & (data_frame['ma_signal'] == -1), -1.0, 0)

        # print(data_frame.tail(10))

        self.plot_signal(data_frame, signal_type, fast_sma_periods, slow_sma_periods, 'rsi', plot)

        if current is None:
            if data_frame.signal.iat[-1] == 1.0:
                return "Buy"
            elif data_frame.signal.iat[-1] == -1.0:
                return "Sell"
        else:
            if current == "Sell" and data_frame.signal.iat[-1] == 1.0 \
                    or current == "Buy" and data_frame.signal.iat[-1] == -1.0:
                return "Close"
        return "None"

    def ema(self, price_data, signal_type, current, plot=False):
        data_frame = pd.DataFrame(price_data)

        fast_sma_periods = str(self.fast_sma_periods) + '_' + signal_type
        slow_sma_periods = str(self.slow_sma_periods) + '_' + signal_type

        close_list = data_frame['close'].tolist()
        slow = talib.EMA(np.asarray(close_list), timeperiod=self.slow_sma_periods)
        fast = talib.EMA(np.asarray(close_list), timeperiod=self.fast_sma_periods)
        data_frame[slow_sma_periods] = slow
        data_frame[fast_sma_periods] = fast
        data_frame['ma_signal'] = np.where(data_frame[slow_sma_periods] < data_frame[fast_sma_periods], 1.0, 0.0)

        data_frame['ma_signal'] = data_frame['ma_signal'].diff()
        data_frame['signal'] = data_frame['ma_signal']

        # print(data_frame.tail(10))

        self.plot_signal(data_frame, signal_type, fast_sma_periods, slow_sma_periods, None, plot)

        if current is None:
            if data_frame.signal.iat[-1] == 1.0:
                return "Buy"
            elif data_frame.signal.iat[-1] == -1.0:
                return "Sell"
        else:
            if current == "Sell" and data_frame.signal.iat[-1] == 1.0 \
                    or current == "Buy" and data_frame.signal.iat[-1] == -1.0:
                return "Close"
        return "None"

    @staticmethod
    def test(price_data, signal_type, current, plot=False):
        if random.randrange(0, 2) == 1:
            return "Buy"
        else:
            return "Sell"

    def plot_signal(self, data_frame, signal_type, fast_sma_periods, slow_sma_periods, lower_key, show):
        if show:
            plt.figure(figsize=(200, 100))

            fig, (upper, lower) = plt.subplots(2)
            fig.suptitle(signal_type)
            upper.plot(data_frame['close'])

            # plot 'buy' signals
            upper.plot(data_frame[data_frame['signal'] == 1].index,
                       data_frame[slow_sma_periods][data_frame['signal'] == 1], '^', markersize=7, color='g',
                       label='buy')
            # plot 'sell' signals
            upper.plot(data_frame[data_frame['signal'] == -1].index,
                       data_frame[fast_sma_periods][data_frame['signal'] == -1], 'v', markersize=7, color='r',
                       label='sell')
            upper.plot(data_frame[fast_sma_periods], color='k', lw=1, label=fast_sma_periods)
            upper.plot(data_frame[slow_sma_periods], color='g', lw=1, label=slow_sma_periods)
            if lower_key is not None:
                lower.plot(data_frame[lower_key])
            plt.ylabel('Price', fontsize=16)
            plt.xlabel('Date', fontsize=16)
            plt.title(str(self.symbol) + ' - ' + str(signal_type), fontsize=20)
            plt.legend()
            plt.grid()
            plt.show()
