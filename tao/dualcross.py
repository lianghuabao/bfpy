# coding=utf-8
#author:tao
#==============================================================================
# 1.在平仓时，暂未考虑上期所的平今、平昨的情况
# 2.在退出时，会将策略合约的未成交单全部撤单
# 3.使用的均线是EMA
#==============================================================================
import sys 
sys.path.append("..") 

import time
import random

from bfgateway_pb2 import *
from bfdatafeed_pb2 import *
from bftraderclient import BfTraderClient,BfRun

import numpy as np

EMPTY_STRING = ''
EMPTY_FLOAT = 0.0
EMPTY_INT = 0


class DualCross(BfTraderClient):
    #strategy const
    precision=3 #小数的精度
    fastPeriod=3 #快速EMA周期
    slowPeriod=5#慢速EMA周期
    fastP= np.round(1.0/(fastPeriod*2+1),2) #快速EMA参数
    slowP=np.round(1.0/(slowPeriod*2+1),2) #慢速EMA参数
    initDays=10 #初始化数据时所用的天数
    maxCounter=10 #第二个bar等待多久去取datafeed的数据
    period=PERIOD_M01
    maxPosition=100 #最大持仓量
    orderVolume=2 #每次开仓量
    
    #strategy variable
    bar=None
    barMinute=EMPTY_INT
    firstBarMinute=EMPTY_INT
    counter=EMPTY_INT
    
    bFirstTick=True
    position={"long":EMPTY_INT,"short":EMPTY_INT}#保存self.symbol的持仓信息
    orderData={}#保存self.symbol的报单信息   
    
    fastMa={"ma":[],"ma0":EMPTY_FLOAT,"ma1":EMPTY_FLOAT}
    slowMa={"ma":[],"ma0":EMPTY_FLOAT,"ma1":EMPTY_FLOAT}
    
    symbolTick=BfTickData() #获取第一个tick,用于在下单时使用的涨跌停价格
    def __init__(self):
        super(DualCross, self).__init__()	
        self.clientId="dualcross"
        self.tickHandler=True
        self.tradeHandler=True
        self.logHandler=False
        self.symbol="rb1610"
        self.exchange="SHFE"
        
        # 获取当前仓位
        print "Init Position"
        req = BfVoid()
        self.gateway.QueryPosition(req,_TIMEOUT_SECONDS,metadata=_MT)
                  
            
    def OnPing(self, request):
        pass

    def OnTick(self, tick):
        #如何处理隔夜情况
        tickHour=tick.tickTime.split(':')[0]
        tickMinute=tick.tickTime.split(':')[1]
        barMinute=int(tickHour)*60+int(tickMinute)
        if self.bFirstTick:
            self.bFirstTick=False
            self.firstBarMinute=barMinute
            self.symbolTick=tick
        elif barMinute == self.firstBarMinute:
            #在第一分钟内的数据从datarecorder中获取
            return
        else:
            if((barMinute-self.firstBarMinute)==1):
                #延迟
                self.counter+=1
                if self.counter == self.maxCounter:
                    #取数
                    req=BfGetBarReq(symbol=self.symbol,exchange=self.exchange,period=self.period,
                        toDate=tick.actionDate,
                        toTime= tickHour + ':' + tickMinute + ':00',count=1)
                    responses=self.GetBar(req)
                    for resp in responses:
                        self.OnBar(resp)
            #计算K线
            if self.barMinute != barMinute:
                if self.bar:
                    self.OnBar(self.bar)
                bar=BfBarData()
                bar.symbol=tick.symbol
                bar.exchange=tick.exchange
                bar.period=self.period
                
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
                self.barMinute=barMinute
            else:
                bar=self.bar
                
                bar.closePrice=tick.lastPrice
                bar.highPrice=max(bar.highPrice,tick.lastPrice)
                bar.lowPrice=min(bar.lowPrice,tick.lastPrice)
                
                bar.volume=tick.volume
                bar.lastVolume+=tick.lastVolume
                bar.openInterest=tick.openInterest
                
    def OnBar(self,bar):
        #print "OnBar",bar
        #当天EMA=昨天的EMA+加权因子*（当天的收盘价-昨天的EMA）= 加权因子*当天的收盘价+（1-加权因子）*昨天的EMA
        #当天EMA=昨天的EMA+加权因子*（当天的收盘价-昨天的EMA） 较后式应该会更快
        if not self.fastMa["ma0"]:
            self.fastMa["ma0"]=np.round( bar.closePrice,self.precision)
            self.fastMa["ma"].append(self.fastMa["ma0"])
        else:
            self.fastMa["ma1"]=self.fastMa["ma0"]
            self.fastMa["ma0"]= np.round(self.fastMa["ma0"]+self.fastP * (bar.closePrice-self.fastMa["ma0"]),self.precision)
            self.fastMa["ma"].append(self.fastMa["ma0"])
        
        if not self.slowMa["ma0"]:
            self.slowMa["ma0"]=np.round( bar.closePrice,self.precision)
            self.slowMa["ma"].append(self.slowMa["ma0"])
        else:
            self.slowMa["ma1"]=self.slowMa["ma0"]
            self.slowMa["ma0"]=np.round(self.slowMa["ma0"]+self.slowP * (bar.closePrice-self.slowMa["ma0"]),self.precision)
            self.slowMa["ma"].append(self.slowMa["ma0"])
            
        #判断买卖
            
        crossOver=self.fastMa["ma0"] > self.slowMa["ma0"] and self.fastMa["ma1"] < self.slowMa["ma1"]
        crossBelow=self.fastMa["ma0"] < self.slowMa["ma0"] and self.fastMa["ma1"] > self.slowMa["ma1"]
        
        #以当前bar的收盘价进行开平仓，可能不会立即成交,可以考虑使用涨跌停价/在收盘价的基础上加上一定跳数/使用市价 保证完成开平仓操作，目前使用涨跌停价格的方式                                             
        if crossOver:#金叉上穿
            if self.position["long"]+self.orderVolume > self.maxPosition:	#大于最大持仓量，不再开仓
                return
            else:
                #若有空仓，先平空仓，再开多仓
                if self.position["short"] > 0:
                    req1 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=self.symbolTick.lowerLimit,
                                  volume=self.position['short'],
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_LONG, offset=OFFSET_CLOSE)
                    self.SendOrder(req1)
                    print ("close short %s:price:%10.3f,volume:%d" %(self.symbol,self.symbolTick.lowerLimit,self.position['short']))
                req2 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=self.symbolTick.upperLimit, volume=self.orderVolume,
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_LONG, offset=OFFSET_OPEN)            
                self.SendOrder(req2)
                print ("open long %s:price:%10.3f,volume:%d" %(self.symbol,self.symbolTick.upperLimit,self.orderVolume))

        if crossBelow:#死叉下穿
            if self.position["short"] + self.orderVolume > self.maxPosition:
                return
            else:
                if self.position["long"] > 0:
                    req1 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=self.symbolTick.lowerLimit,
                                  volume=self.position['long'],
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_SHORT, offset=OFFSET_CLOSE)
                    self.SendOrder(req1)
                    print ("close long %s:price:%10.3f,volume:%d" %(self.symbol,self.symbolTick.lowerLimit,self.position['long']))
                req2 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=self.symbolTick.upperLimit, volume=self.orderVolume,
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_SHORT, offset=OFFSET_OPEN)            
                self.SendOrder(req2)
                print ("open short %s:price:%10.3f,volume:%d" %(self.symbol,self.symbolTick.upperLimit,self.orderVolume))
                
    def OnError(self, request):
        print "OnError"
        print request
            
    def OnLog(self, request):
        print "OnLog"
        print request
    
    def OnTrade(self, trade):
        print "OnTrade:",trade
        if trade.symbol == self.symbol:
            if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_OPEN:#多开
                self.position["long"]+=trade.volume
            elif trade.direction == DIRECTION_LONG and (trade.offset == OFFSET_CLOSEYESTERDAY or trade.offset == OFFSET_CLOSETODAY or trade.offset==OFFSET_CLOSE):#多平
                self.position["long"]-=trade.volume
            elif trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_OPEN:#空开
                self.position["short"]+=trade.volume
            elif trade.direction == DIRECTION_SHORT and (trade.offset == OFFSET_CLOSEYESTERDAY or trade.offset == OFFSET_CLOSETODAY or trade.offset==OFFSET_CLOSE):#空平
                self.position["short"]-=trade.volume
                
    def OnOrder(self, order):
        print "OnOrder:",order
        if order.symbol == self.symbol:
            self.orderData[order.bfOrderId]=order
            
    def OnPosition(self, pos):
        print "OnPosition:",pos
        if pos.symbol == self.symbol:
            if pos.direction == DIRECTION_LONG:#多单
                self.position["long"]=pos.position
            else :#空单
                self.position["short"]=pos.position
    
    def OnAccount(self, request):
        print "OnAccount"
        print request
    
    def OnStop(self):
        print 'OnStop'
        #在程序结束时，将所有未成交报单撤单
        req = BfCancelOrderReq(symbol=self.symbol, exchange=self.exchange)        
        for key in self.orderData:
            if self.orderData[key].status == STATUS_NOTTRADED or self.orderData[key].status == STATUS_PARTTRADED:
                req.bfOrderId=self.orderData[key].bfOrderId
                self.CancleOrder(req)
                print("cancle order:bfOrderId=%s" %(req.bfOrderId))
    
def run():
    print "start dualcross"
    client = DualCross()
    BfRun(client,clientId=client.clientId,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)
    
    
if __name__ == '__main__':
    run()
