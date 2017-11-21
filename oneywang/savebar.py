# coding=utf-8

#################Readme#########################
#1.读取TICK合并成一分钟BAR存入datafeed！
#2.不支持多周期。
#3.支持多品种。

import sys 
sys.path.append("..") 
from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *

from  datetime  import  *
import time
import random


def Tick2Bar(tick, bar, period):
    bar.symbol = tick.symbol
    bar.exchange = tick.exchange
    bar.period = period
    
    bar.actionDate = tick.actionDate
    bar.barTime = datetime.strftime(datetime.strptime(tick.tickTime,"%H:%M:%S.%f"),"%H:%M:%S")
    bar.volume = tick.volume
    bar.openInterest = tick.openInterest
    bar.lastVolume = tick.lastVolume
    
    bar.openPrice = tick.lastPrice
    bar.highPrice = tick.lastPrice
    bar.lowPrice = tick.lastPrice
    bar.closePrice = tick.lastPrice

    return bar

class BarSaver(BfTraderClient):
    # 变量
    bars = {}
    _contract_inited = 0

    def __init__(self):
        print "init......"
        BfTraderClient.__init__(self)
        self.clientId = "Save 1min bar"
        self.tickHandler = True
        self.tradeHandler = False
        self.logHandler = False
        self.symbol = "rb1610"
        self.exchange = "SHFE"

        
    def OnTradeWillBegin(self, request):
        print "OnTradeWillBegin"
        print request        

    def insertContracts(self):
        # GetContract
        req = BfGetContractReq(symbol="*",exchange="*")
        resps = self.GwGetContract(req)
        for resp in resps:
            print resp
            df = self.InsertContract(resp)
        
    def OnGotContracts(self, request):
        print "OnGotContracts"
        print request

        # GetContract
        self._contract_inited = 1
        self.insertContracts()
        
        # QueryPosition
        req = BfVoid()
        resp = self.CancleOrder(req)
        print resp
        
        # QueryAccount
        req = BfVoid()
        resp = self.QueryAccount(req)
        print resp
    
    def OnTick(self, tick):
        df = self.InsertTick(tick)

        # 要把contract保存到datafeed里面才会看到数据
        # ongotcontracts只有ctpgateway连接上ctp时候才发，所有盘中策略连接ctpgateway时候，是没有这个信息的。
        # 可以手工把ctpgateway ctp-stop然后ctp-start以下，就可以得到这个消息。我们这里程序自动判断如果没有调用则主动调用一次。
        if self._contract_inited == 0 :
            self._contract_inited = 1
            self.insertContracts()
        
        # 计算K线
        id = tick.symbol + '@' + tick.exchange
        # tickDatetime = datetime.strptime(tick.actionDate+tick.tickTime,"%Y%m%d%H:%M:%S.%f")
        
        if not self.bars.has_key(id):
            bar = BfBarData()              
            Tick2Bar(tick, bar, PERIOD_M01)
            self.bars[id] = bar
            return

        #print "update bar for: " + id
        bar = self.bars[id]
        if datetime.strptime(tick.tickTime,"%H:%M:%S.%f").minute != datetime.strptime(bar.barTime,"%H:%M:%S").minute:
            # 过去的一个bar存入datafeed
            print "Insert bar" 
            print tick.tickTime
            print bar   
            self.InsertBar(bar)
            
            # 初始化一个新的k线
            Tick2Bar(tick, bar, PERIOD_M01)

        else:
            # 继续累加当前K线
            bar.highPrice = max(bar.highPrice, tick.lastPrice)
            bar.lowPrice = min(bar.lowPrice, tick.lastPrice)
            bar.closePrice = tick.lastPrice
            bar.volume = tick.volume
            bar.openInterest = tick.openInterest
            bar.lastVolume += tick.lastVolume
    
if __name__ == '__main__':
    client = BarSaver()
    BfRun(client,clientId=client.clientId,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)

