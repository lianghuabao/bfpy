# coding=utf-8

from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *
from Indicator import *


class MacdShockL(BfTraderClient):
    """
    1.onStart中获得历史数据，如果数据不是很多，漏掉几个tick应该问题不大
    2.为了简单，这里示例单策略单方向单品种，如果是多空都做，只要运行多个策略对象即可
    3.没考虑追单,基于图表交易的理论模型交易，理论仓与实际仓的差异如果用加跳入场可以忽略
    4.没考虑tick数据清洗
    5.模仿了tb的写法
    6.指标不返回none，比如ma60，k线没有60根则复制最前面的k线补足60根
    7.没考虑bar内交易，这个需要对指标进行修改，另外可以考虑将指标修改成支持多周期的
    8.MacdShockS做空策略可以参考这个写
    9.参考了z++和oneywang
    """

    def __init__(self):
        super(MacdShockL, self).__init__()
        self.clientId = "MacdShockL"
        self.tickHandler = True
        self.tradeHandler = True
        self.logHandler = False
        self.symbol = "rb1610"
        self.exchange = "SHFE"
        
        self.barMinute=None
        self.bar=None
        self.pos=0
        self.orderData = {}  # 订单
        self.MarketPosition =0 # 仓位    
        self.ma60f=averageF(60) #ma60指标
        self.macdf=macdF(12, 26, 9) #macd指标
        self.entry=False # 是否开仓
        self.trading=False # 是否开始交易
        self.barsSinceEntry=-1 #开仓之后bar的根数

    def OnStart(self):
        req = BfGetBarReq(symbol=self.symbol, exchange=self.exchange, period=PERIOD_M15,
                          toDate="20170808",
                          toTime="121212",
                          count=2)
        responses = self.GetBar(req)

        for resp in responses:
            self.OnBar(resp)        
        self.trading=True
        self.firstTick=True
        
    def OnTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        #print 'OnTick'

        tickHour = tick.tickTime.split(':')[0]
        tickMinute = tick.tickTime.split(':')[1]
        #barMinute = int(tickHour) * 60 + int(tickMinute) 
        

        # 计算K线
        if self.firstTick==True or tickMinute != self.barMinute and int(tickMinute)%15==0 :
            self.firstTick=False
            if self.bar :
                self.OnBar(self.bar)

            bar = BfBarData()
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange
            bar.period = PERIOD_M15

            bar.openPrice = tick.lastPrice
            bar.highPrice = tick.lastPrice
            bar.lowPrice = tick.lastPrice
            bar.closePrice = tick.lastPrice

            bar.actionDate = tick.actionDate
            bar.barTime = tick.tickTime

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

    # ----------------------------------------------------------------------
    def OnBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        print 'OnBar'
        

        # 计算指标    
        close=bar.closePrice
        ma60=self.ma60f(close)
        macdValue,avgMacd,macdDiff=self.macdf(close)
        print bar.barTime +":"+str(close)
        
        #是否开始交易
        if self.trading==False:
            return
        #计算barsSinceEntry
        if self.entry:
            self.barsSinceEntry+=1
        else:
            self.barsSinceEntry=-1
            
        buyCon= close<ma60[-1] and (ma60[-1]-close)*1.0/close>0.01 and macdDiff[-2]<=0 and macdDiff[-1]>0
        if self.pos==0 and buyCon:
            self.Buy(close+1, 3) #1跳暂时用1表示
            self.pos=3
            self.entry=True
            self.barsSinceEntry=0
            print("buy->price:"+str(close+1)+"/lots:3")
            
        if self.pos>0:
            if self.barsSinceEntry>=1 and macdDiff[-2]>=0 and macdDiff[-1]<0:
                self.Sell(close-1, 1)
                self.pos-=1
                print("sell->con:1/price:"+str(close-1)+"/lots:1")
            if self.barsSinceEntry>=1 and close<ma60[-1]:
                self.Sell(close-1, 1)
                self.pos-=1
                print("sell->con:2/price:"+str(close-1)+"/lots:1")
            if self.barsSinceEntry>=10:
                self.Sell(close-1, 1)   
                self.pos-=1
                print("sell->con:3/price:"+str(close-1)+"/lots:1")
            if self.pos==0:
                self.entry=False

    def OnTrade(self, tradeData):
        print "OnTrade"
        print tradeData
        

    def OnOrder(self, orderData):
        print "OnOrder"
        print orderData
        if orderData.symbol == self.symbol:
            self.orderData[orderData.bfOrderId] = orderData

    def OnPosition(self, request):
        print "OnPosition"
        self.pos = request
        print request

    def OnStop(self):
        print 'OnStop'
        
        for key in self.orderData:
            if self.orderData[key].status == STATUS_NOTTRADED or self.orderData[key].status == STATUS_PARTTRADED:
                req = BfCancelOrderReq(symbol=self.symbol, exchange=self.exchange,
                                       bfOrderId=self.orderData[key].bfOrderId)
                self.SendOrder(req)
    def Buy(self,price,lot):
        ''' 
        发单时传入的对象类 BfSendOrderReq
        string symbol = 1;          // 合约代码
        string exchange = 2;        // 交易所代码    
        double price = 3;           // 价格
        int32 volume = 4;           // 数量
        BfPriceType priceType = 5;  // 价格类型 PRICETYPE_UNKONWN =  未知 PRICETYPE_LIMITPRICE =  限价
                                                PRICETYPE_MARKETPRICE =  市价
        BfDirection direction = 6;  // 买卖 DIRECTION_UNKNOWN = 未知 DIRECTION_LONG = 多 DIRECTION_SHORT =  空
                                            DIRECTION_NET =  净
        BfOffset offset = 7;        // 开平 OFFSET_UNKNOWN =  未知  OFFSET_OPEN =  开仓  OFFSET_CLOSE =  平仓 
                                            OFFSET_CLOSETODAY = 平今 OFFSET_CLOSEYESTERDAY =平昨
        '''
        #
        if self.MarketPosition < 0:

            self.BuyToCover(price,self.MarketPosition*-1)   #先平仓
        
        req = BfSendOrderReq(symbol = _symbol, exchange = _exchange ,price = price, volume = lot,
            priceType = PRICETYPE_LIMITPRICE,direction = DIRECTION_LONG, offset = OFFSET_OPEN)
        request = self.gateway.SendOrder(req,_TIMEOUT_SECONDS,metadata=_MT)   #再开仓
        print request
        
    def Sell(self,price,lot):
        '''卖平仓，使用限价委托单，有可能成交不了，可以在价格上考虑加滑点'''
        req = BfSendOrderReq(symbol = _symbol, exchange = _exchange ,price = price, volume = lot,
            priceType = PRICETYPE_LIMITPRICE,direction = DIRECTION_SHORT, offset = OFFSET_CLOSE)
        request = self.gateway.SendOrder(req,_TIMEOUT_SECONDS,metadata=_MT)
        print request

    def BuyToCover(self,price,lot):
        '''买平仓'''
        req = BfSendOrderReq(symbol = _symbol, exchange = _exchange ,price = price, volume = lot,
            priceType = PRICETYPE_LIMITPRICE,direction = DIRECTION_LONG, offset = OFFSET_CLOSE)
        request = self.gateway.SendOrder(req,_TIMEOUT_SECONDS,metadata=_MT)
        print request

    def SellShort(self,price,lot):
        '''卖开仓，有多持仓的话，会先平掉，再开仓'''
        if self.MarketPosition >0:
            self.Sell(price,self.MarketPosition)   #先平仓
        
        req = BfSendOrderReq(symbol = _symbol, exchange = _exchange ,price = price, volume = lot,
            priceType = PRICETYPE_LIMITPRICE,direction = DIRECTION_SHORT, offset = OFFSET_CLOSE)
        request = self.gateway.SendOrder(req,_TIMEOUT_SECONDS,metadata=_MT) #在开仓
        print request

if __name__ == '__main__':
    client = MacdShockL()
    BfRun(client, clientId=client.clientId, tickHandler=client.tickHandler, tradeHandler=client.tradeHandler,
          logHandler=client.logHandler, symbol=client.symbol, exchange=client.exchange)
