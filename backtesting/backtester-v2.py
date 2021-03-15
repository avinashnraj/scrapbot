#!/usr/bin/env python
import backtrader as bt


class SmaCross(bt.Strategy):
    params = dict(sma1=25, sma2=50, rsi=5, rsi_max=50, rsi_min=50)

    def notify_order(self, order):
        if not order.alive():
            print('{} {} {}@{}'.format(
                bt.num2date(order.executed.dt),
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price)
            )

    def notify_trade(self, trade):
        if trade.isclosed:
            print('profit {}'.format(trade.pnlcomm))

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.params.sma1)
        sma2 = bt.ind.SMA(period=self.params.sma2)
        self.crossover = bt.ind.CrossOver(sma1, sma2)
        self.crossunder = bt.ind.CrossOver(sma2, sma1)
        self.rsi = bt.talib.RSI(self.data, plotname='TA_RSI')

    def next(self):
        if self.crossover > 0:  # if fast crosses slow to the upside
            if self.position:
                self.close()
            # print(self.position)
            if self.rsi > self.params.rsi_max:
                self.buy()  # enter long
                # print("Buy {} shares".format( self.data.close[0]))
                # print(self.position)
        elif self.crossover < 0:  # in the market & cross to the downside
            if self.position:
                self.close()  # close long position
                # print(self.position)
            if self.rsi < self.params.rsi_min:
                self.sell()
                # print("Sale {} shares".format(self.data.close[0]))
                # print(self.position)


def runstrat():
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100)

    data = bt.feeds.GenericCSVData(
        dataname='XAUUSD_M1_v1-1.csv',
        timeframe=bt.TimeFrame.Minutes,
        nullvalue=0.0,
        dtformat=('%Y.%m.%d'),
        tmformat=('%H:%M'),
        datetime=0,
        time=1,
        high=2,
        low=3,
        open=4,
        close=5,
        volume=6,
        openinterest=-1
    )

    cerebro.adddata(data)
    cerebro.addstrategy(SmaCross)
    cerebro.run()
    cerebro.plot(style="candles")


if __name__ == '__main__':
    runstrat()
