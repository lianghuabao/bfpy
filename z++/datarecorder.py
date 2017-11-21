# coding=utf-8

from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *

class DataRecorder(BfTraderClient):
    bar = None
    barMinute = ''

    def __init__(self):
        BfTraderClient.__init__(self)
        self.clientId = "DataRecorder";
        self.tickHandler = True
        self.tradeHandler = False
        self.logHandler = False
        self.symbol = "rb1609"
        self.exchange = "SHFE"

    def OnPing(self, response):
        print 'OnPing'
        pass


    def OnGotContracts(self, response):
        print "OnGotContracts"
        print response
        
        #
        # save contract
        #
        req = BfGetContractReq(symbol="*",exchange="*")
        resps = self.GwGetContract(req)
        for resp in resps:
            print resp
            self.InsertContract(resp)


    def OnTick(self, tick):
        print "OnTick"
        print tick
        
        #
        # save tick
        #
        resp = self.InsertTick(tick)

        #
        # save bar
        #
        tickMinute = tick.tickTime.split(':')[1]

        if tickMinute != self.barMinute:
            if self.bar:
                self.InsertBar(self.bar)

            bar = BfBarData()
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange
            bar.period = PERIOD_M01

            bar.openPrice = tick.lastPrice
            bar.highPrice = tick.lastPrice
            bar.lowPrice = tick.lastPrice
            bar.closePrice = tick.lastPrice

            bar.actionDate = tick.actionDate
            bar.barTime = tick.tickTime.split('.')[0]

            # 实盘中用不到的数据可以选择不算，从而加快速度
            # bar.volume = tick.volume
            # bar.openInterest = tick.openInterest

            self.bar = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute  # 更新当前的分钟

        else:  # 否则继续累加新的K线
            bar = self.bar  # 写法同样为了加快速度

            bar.highPrice = max(bar.highPrice, tick.lastPrice)
            bar.lowPrice = min(bar.lowPrice, tick.lastPrice)
            bar.closePrice = tick.lastPrice


if __name__ == '__main__':
    client = DataRecorder()
    BfRun(client,clientId=client.clientId,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)
