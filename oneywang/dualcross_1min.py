# coding=utf-8

#################Readme#########################
#1.请手工保证帐号上的钱够！
#2.本策略还不支持多实例等复杂场景。
#3.策略退出时会清除所有挂单。



import sys 
sys.path.append("..") 
from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *

from  datetime  import  *
import time
import random

# 默认空值
EMPTY_STRING = ''
EMPTY_UNICODE = u''
EMPTY_INT = 0
EMPTY_FLOAT = 0.0

#################要与BfBarData返回结果一致#########################
class BarData(object):
    # K线数据

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING          # 代码
        self.exchange = EMPTY_STRING        # 交易所
    
        self.open = EMPTY_FLOAT             # OHLC
        self.high = EMPTY_FLOAT
        self.low = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        
        self.date = EMPTY_STRING            # bar开始的时间，日期
        self.time = EMPTY_STRING            # 时间
        #self.datetime = None                # python的datetime时间对象
        
        self.volume = EMPTY_INT             # 成交量
        self.openInterest = EMPTY_INT       # 持仓量


class DualCross(BfTraderClient):
    # 策略参数
    TRADE_VOLUME = 1    # 每次交易的手数
    VOLUME_LIMIT = 5      # 多仓或空仓的最大手数
    FAST_K_NUM = 15     # 快速均线
    SLOW_K_NUM = 60     # 慢速均线
    
    # 策略变量
    #bar = None
    inited = 0
    barCount = 0
    barMinute = EMPTY_STRING
    
    fastMa = []             # 15均线数组
    fastMa0 = EMPTY_FLOAT   # 当前最新的快均线
    fastMa1 = EMPTY_FLOAT   # 上一根的快均线

    slowMa = []             # 60均线数组
    slowMa0 = EMPTY_FLOAT   # 当前最新的慢均线
    slowMa1 = EMPTY_FLOAT   # 上一根的慢均线

    # 关心的品种，持有仓位
    period = PERIOD_M01
    pos_long = 0    #多仓
    pos_short = 0   #空仓
    pending_orders = []

    def __init__(self):
        print "init dualcross"
        BfTraderClient.__init__(self)
        self.clientId = "Save 1min bar"
        self.tickHandler = True
        self.tradeHandler = False
        self.logHandler = False
        self.symbol = "rb1610"
        self.exchange = "SHFE"
    
    def _initPosition(self, position):
        if position.direction == DIRECTION_LONG:
            self.pos_long += position.position
        elif position.direction == DIRECTION_SHORT:
            self.pos_short += position.position
    
    def OnStart(self):
        print "OnInit-->QueryPosition"
        # 获取当前仓位
        #positions = self.QueryPosition(BfVoid())
        #for pos in positions:
        #    print pos
        #    if pos.symbol == self.symbol and pos.exchange == self.exchange:
        #        _initPosition(pos)

    def OnTick(self, tick):
        # 收到行情TICK推送
        tickMinute = datetime.strptime(tick.tickTime,"%H:%M:%S.%f").minute

        # 初始得到K线
        if not self.inited:
            self.inited = 1
            print "Init: load history Bar"
            now = datetime.now()
            req = BfGetBarReq(symbol=self.symbol,exchange=self.exchange,period=self.period,toDate=tick.actionDate,toTime=tick.tickTime,count=self.SLOW_K_NUM)
            bars = self.GetBar(req)
            for bar in bars:
                self._onBar(bar.closePrice)
            
            self.barMinute = tickMinute
            return
        
        # 每一新分钟得到K线
        if tickMinute != self.barMinute:
            print tick.tickTime + " got a new bar"
            # 因为只用到了bar.closePrice，所以不必再去datafeed取上一K线
            # TODO，如果需要去datafeed取，记得稍微延迟几个tick以防datafeed还没准备好。
            self._onBar(tick.lastPrice)
            self.barMinute = tickMinute    

    def _onBar(self, closePrice):
        # 计算快慢均线
        if not self.fastMa0:        
            self.fastMa0 = closePrice
            self.fastMa.append(self.fastMa0)
        else:
            self.fastMa1 = self.fastMa0
            self.fastMa0 = ( closePrice + self.fastMa0 * (self.FAST_K_NUM - 1)) / self.FAST_K_NUM
            self.fastMa.append(self.fastMa0)
            
        if not self.slowMa0:
            self.slowMa0 = closePrice
            self.slowMa.append(self.slowMa0)
        else:
            self.slowMa1 = self.slowMa0
            self.slowMa0 = ( closePrice + self.slowMa0 * (self.SLOW_K_NUM -1) ) / self.SLOW_K_NUM
            self.slowMa.append(self.slowMa0)
        
        # 判断是否足够bar--初始化时会去历史，如果历史不够，会积累到至少  SLOW_K_NUM 数量的bar才会交易
        self.barCount += 1
        print self.barCount
        if self.barCount < self.SLOW_K_NUM:
            return

        # 判断买卖
        print self.fastMa0
        print self.slowMa0
        crossOver = self.fastMa0>self.slowMa0 and self.fastMa1<self.slowMa1     # 金叉上穿
        crossBelow = self.fastMa0<self.slowMa0 and self.fastMa1>self.slowMa1    # 死叉下穿
        
        # 金叉
        if crossOver:
            # 1.如果有空头持仓，则先平仓
            if self.pos_short > 0:
                self.cover(closePrice, self.pos_short)
            # 2.持仓未到上限，则继续做多
            if self.pos_long < self.VOLUME_LIMIT:
                self.buy(closePrice, self.TRADE_VOLUME)
        # 死叉
        elif crossBelow:
            # 1.如果有多头持仓，则先平仓
            if self.pos_long > 0:
                self.sell(closePrice, self.pos_long)
            # 2.持仓未到上限，则继续做空
            if self.pos_short < self.VOLUME_LIMIT:
                self.short(closePrice, self.TRADE_VOLUME)
    
    def buy(self, price, volume):
        print time.strftime("%Y-%m-%d %H:%M:%S")
        print ("buy: price=%10.3f vol=%d" %(price, volume))
        req = BfSendOrderReq(symbol=self.symbol,exchange=self.exchange,price=price,volume=volume,priceType=PRICETYPE_LIMITPRICE,direction=DIRECTION_LONG,offset=OFFSET_OPEN)
        resp = self.SendOrder(req)
        self.pending_orders.append(resp.bfOrderId)
        print resp

    def sell(self, price, volume):
        print time.strftime("%Y-%m-%d %H:%M:%S")
        print ("sell: price=%10.3f vol=%d" %(price, volume))
        req = BfSendOrderReq(symbol=self.symbol,exchange=self.exchange,price=price,volume=volume,priceType=PRICETYPE_LIMITPRICE,direction=DIRECTION_LONG,offset=OFFSET_CLOSE)
        resp = self.SendOrder(req)
        self.pending_orders.append(resp.bfOrderId)
        print resp

    def short(self, price, volume):
        print time.strftime("%Y-%m-%d %H:%M:%S")
        print ("short: price=%10.3f vol=%d" %(price, volume))
        req = BfSendOrderReq(symbol=self.symbol,exchange=self.exchange,price=price,volume=volume,priceType=PRICETYPE_LIMITPRICE,direction=DIRECTION_SHORT,offset=OFFSET_OPEN)
        resp = self.SendOrder(req)
        self.pending_orders.append(resp.bfOrderId)
        print resp

    def cover(self, price, volume):
        print time.strftime("%Y-%m-%d %H:%M:%S")
        print ("cover: price=%10.3f vol=%d" %(price, volume))
        req = BfSendOrderReq(symbol=self.symbol,exchange=self.exchange,price=price,volume=volume,priceType=PRICETYPE_LIMITPRICE,direction=DIRECTION_SHORT,offset=OFFSET_CLOSE)
        resp = self.SendOrder(req)
        self.pending_orders.append(resp.bfOrderId)
        print resp

    def OnTradeWillBegin(self, request):
        # 盘前启动策略，能收到这个消息，而且是第一个消息
        # TODO：这里是做初始化的一个时机
        pass        

    def OnGotContracts(self, request):
        # 盘前启动策略，能收到这个消息，是第二个消息
        # TODO：这里是做初始化的一个时机
        pass
            
    def OnPing(self, request,):
        pass

    def OnError(self, request):
        print "OnError"
        print request
            
    def OnLog(self, request):
        print "OnLog"
        print request

    def _updatePosition(self, direction, offset, volume):
        if (direction == DIRECTION_LONG and offset == OFFSET_OPEN):
            self.pos_long += volume
        elif (direction == DIRECTION_LONG and offset == OFFSET_CLOSE):
            self.pos_long -= volume
        elif (direction == DIRECTION_SHORT and offset == OFFSET_OPEN):
            self.pos_short += volume
        elif (direction == DIRECTION_SHORT and offset == OFFSET_CLOSE):
            self.pos_short -= volume
    
    def OnTrade(self, request):
        # 挂单的成交
        print "OnTrade"
        print request
        # 按最新结果更新当前仓位
        if request.bfOrderId not in self.pending_orders:
            return;
        if request.symbol != self.symbol or request.exchange != self.exchange:
            return;
        
        self.pending_orders.remove(request.bfOrderId)
        _updatePosition(request.direction, request.offset, request.volume)
        
    def OnStop(self):
        # 退出前，把挂单都撤了
        print "cancel all pending orders"
        req = BfCancelOrderReq(symbol=client.symbol,exchange=client.exchange)
        for id in self.pending_orders:
            req.bfOrderId = id
            self.CancleOrder(req)
    
    def OnOrder(self, request):
        # 挂单的中间状态，一般只需要在OnTrade里面处理。
        print "OnOrder"
        print request
            
    def OnPosition(self, request):
        print "OnPosition"
        print request

    def OnAccount(self, request):
        print "OnAccount"
        print request
    
if __name__ == '__main__':
    client = DualCross()
    BfRun(client,clientId=client.clientId,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)
    
