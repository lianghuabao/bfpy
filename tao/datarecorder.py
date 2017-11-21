# coding=utf-8
#author:tao
import sys 
sys.path.append("..") 
from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *

class DataRecorder(BfTraderClient):
    bar=None
    barMinute=''
    def __init__(self):
        BfTraderClient.__init__(self)
        self.clientId = "DataRecorder"
        self.tickHandler = True
        self.tradeHandler = False
        self.logHandler = False
        self.symbol = "rb1610"
        self.exchange = "SHFE"
        
    def OnStart(self):
        print "OnStart"
        
    def OnTradeWillBegin(self, response):
        print "OnTradeWillBegin"
        print response        

    def OnGotContracts(self, response):
        print "OnGotContracts"
        print response
        
        # save all contracts
        req = BfGetContractReq(symbol="*",exchange="*")
        resps = self.GwGetContract(req)
        for resp in resps:
            print resp
            self.InsertContract(resp)
            
    def OnPing(self, response):
        print "OnPing"
        pass

    def OnTick(self, tick):
        print "OnTick"
        #print tick
        #简单的过滤数据
        if (tick.volume==0 or tick.lastVolume==0):
            return
        # save tick
        resp = self.InsertTick(tick)

        #save bar
        tickMinute=tick.tickTime.split(':')[1]
        if self.barMinute != tickMinute:
            if self.bar:
                self.insertBar(self.bar)
            bar=BfBarData()
            bar.symbol=tick.symbol
            bar.exchange=tick.exchange
            bar.period=PERIOD_M01
            
            bar.openPrice=tick.lastPrice
            bar.closePrice=tick.lastPrice
            bar.highPrice=tick.lastPrice
            bar.lowPrice=tick.lastPrice
            
            bar.actionDate=tick.actionDate
            bar.barTime=tick.tickTime.split('.')[0]
            bar.volume=tick.volume
            bar.lastVolume=tick.lastVolume
            bar.openInterest=tick.openInterest
            
            self.bar=bar
            self.barMinute=tickMinute
        else:
            bar=self.bar
            
            bar.closePrice=tick.lastPrice
            bar.highPrice=max(bar.highPrice,tick.lastPrice)
            bar.lowPrice=min(bar.lowPrice,tick.lastPrice)
            
            bar.barTime=tick.tickTime.split('.')[0]
            bar.volume=tick.volume
            bar.lastVolume+=tick.lastVolume
            bar.openInterest=tick.openInterest

    def OnError(self, response):
        print "OnError"
        print response
            
    def OnOrder(self, response):
        print "OnOrder"
        print response
            
    def OnPosition(self, response):
        print "OnPosition"
        print response

    def OnAccount(self, response):
        print "OnAccount"
        print response
        
    def OnStop(self):
        print "OnStop"

if __name__ == '__main__':
    client = DataRecorder()
    BfRun(client,clientId=client.clientId,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)
