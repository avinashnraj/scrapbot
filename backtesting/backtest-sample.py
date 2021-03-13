from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from backtesting.test import SMA, EURUSD


class SmaCross(Strategy):
    ma1 = None
    ma2 = None

    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA, price, 10)
        self.ma2 = self.I(SMA, price, 20)

    def next(self):
        self.count += 1
    #    self.ma1.data
        print("Current close : ", self.data.index[-1:][0], self.data.Close[-1:][0])
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.sell()


bt = Backtest(EURUSD, SmaCross, commission=0.0002, exclusive_orders=True)
stats = bt.run()
bt.plot()