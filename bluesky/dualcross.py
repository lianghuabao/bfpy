# coding=utf-8

import time
import random
import datetime as dt

from bfgateway_pb2 import *
from bfdatafeed_pb2 import *
from google.protobuf.any_pb2 import *

from grpc.beta import implementations
from grpc.beta import interfaces

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
_TIMEOUT_SECONDS = 1
_CLIENT_ID = "dualcross"
_MT = [("clientid",_CLIENT_ID)]

_PING_TYPE = BfPingData().DESCRIPTOR
_ACCOUNT_TYPE = BfAccountData().DESCRIPTOR
_POSITION_TYPE = BfPositionData().DESCRIPTOR
_TICK_TYPE = BfTickData().DESCRIPTOR
_TRADE_TYPE = BfTradeData().DESCRIPTOR
_ORDER_TYPE = BfOrderData().DESCRIPTOR
_LOG_TYPE = BfLogData().DESCRIPTOR
_ERROR_TYPE = BfErrorData().DESCRIPTOR
_NOTIFICATION_TYPE = BfNotificationData().DESCRIPTOR
#----------------------------------------------------
_symbol = "SR609"   #策略运行合约
_exchange = "CZCE"   #合约交易所


class DualCross(object):
    """双均线策略Demo"""
    period = PERIOD_M01  #策略运行周期
    MarketPosition = 0   #持仓
    
    # 策略参数
    N1 = 15      # 参数
    N2 = 60      # 参数
    
    
    # 策略变量
    Close=[]             # 收盘价列表    
    Ma1 = []             # 均线1列表
    Ma2 = []             # 均线2列表

    barMinute=[]        #查看用
    bar = None
    barMT = u''
    
    def __init__(self):

        print "init dualcross"
        self.gateway_channel = implementations.insecure_channel('localhost', 50051)
        self.gateway = beta_create_BfGatewayService_stub(self.gateway_channel)
        self.datafeed_channel = implementations.insecure_channel('localhost',50052)
        self.datafeed = beta_create_BfDatafeedService_stub(self.datafeed_channel)
        self.connectivity = interfaces.ChannelConnectivity.IDLE
    
    def update(self,connectivity):
        '''C:\projects\grpc\src\python\grpcio\tests\unit\beta\_connectivity_channel_test.py'''
        print connectivity
        self.connectivity = connectivity
        
    def subscribe(self):
        self.gateway_channel.subscribe(self.update,try_to_connect=True)
    
    def unsubscribe(self):
        self.gateway_channel.unsubscribe(self.update)

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

    def OnInit(self):
        # 初始化  
        # QueryPosition
        req = BfVoid()
        resp = self.gateway.QueryPosition(req,_TIMEOUT_SECONDS,metadata=_MT)
        print resp
        
        # loadbar"
        dt_now = dt.datetime.now()   #取现在时间
        dt_now = dt_now- dt.timedelta(minutes=1)  #往前1分
        nowDate = dt_now.strftime('%Y%m%d')   #'20160606'
        nowTime = dt_now.strftime('%X')       #'01:12:45'
        req = BfGetBarReq(symbol=_symbol,exchange=_exchange, period = self.period,toDate=nowDate,
                          toTime=nowTime,count=40)
        responses = self.datafeed.GetBar(req,timeout=_ONE_DAY_IN_SECONDS,metadata=_MT)
        for resp in responses:
            #print resp
            self.Close.insert(0,resp.closePrice)        #仅加载收盘价，
            self.barMinute.insert(0,resp.barTime[0:5])   #记录bar的分钟
        print self.barMinute
        
        #-----------------------------------------------------------------------
        #计算均线1
        print len(self.Close)
        for i in range(0,len(self.Close)):
            if i==0:
                self.Ma1.append(self.Close[0])
                
            else:
                self.Ma1.append((self.Ma1[i-1]*(self.N1-1)+self.Close[i])/self.N1)
                
        #计算均线2
        for i in range(0,len(self.Close)):
            if i==0:
                self.Ma2.append(self.Close[0])
            else:
                self.Ma2.append((self.Ma2[i-1]*(self.N2-1)+self.Close[i])/self.N2)

        #------------------------------------------------------------------------

    def OnTradeWillBegin(self, request):
        print "OnTradeWillBegin"
        print request        

    def OnGotContracts(self, request):
        print "OnGotContracts"
        print request
        
        # GetContract
        for i in range(1,1000):
            req = BfGetContractReq(index=i,subscribled=True)
            resp = self.gateway.GetContract(req,_TIMEOUT_SECONDS,metadata=_MT)
            if (resp.symbol):
                print resp
            else:
                break
        
        # QueryPosition
        req = BfVoid()
        resp = self.gateway.QueryPosition(req,_TIMEOUT_SECONDS,metadata=_MT)
        print resp
        
        # QueryAccount
        req = BfVoid()
        resp = self.gateway.QueryAccount(req,_TIMEOUT_SECONDS,metadata=_MT)
        print resp
            
    def OnPing(self, request,):
        #print "OnPing"
        #print request
        pass
    def OnTick(self, request):
        #print "OnTick"
        #print request
         # 计算K线
        
        tick = request
        if tick.tickTime[3:5] != self.barMT:
            if self.bar:
                self.OnBar(self.bar)
                #print self.bar
                
            bar = BfBarData()              
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange
            bar.period=PERIOD_M01
            bar.openPrice = tick.lastPrice
            bar.highPrice = tick.lastPrice
            bar.lowPrice = tick.lastPrice
            bar.closePrice = tick.lastPrice
            bar.actionDate = tick.actionDate
            bar.barTime = tick.tickTime[0:8]
            bar.volume = tick.volume    #今天总成交量
            bar.openInterest = tick.openInterest
            bar.lastVolume=tick.lastVolume
            self.bar = bar                  
            self.barMT = tick.tickTime[3:5]     # 更新当前的分钟
            
        else:                               # 否则继续累加新的K线
            bar = self.bar                  
            
            bar.highPrice = max(bar.highPrice, tick.lastPrice)
            bar.lowPrice = min(bar.lowPrice, tick.lastPrice)
            bar.closePrice = tick.lastPrice
            bar.volume = tick.volume
            bar.openInterest = tick.openInterest
            bar.lastVolume = bar.lastVolume+tick.lastVolume
        
    def OnBar(self, bar):
        """策略处理过程"""
        self.Close.append(bar.closePrice)
        # 计算均线
        self.Ma1.append((self.Ma1[-1]*(self.N1-1)+self.Close[-1])/self.N1)
        self.Ma2.append((self.Ma2[-1]*(self.N2-1)+self.Close[-1])/self.N2)
            
        # 判断买卖
        crossOver = self.Ma1[-1]>self.Ma2[-1] and self.Ma1[-2]<self.Ma2[-2]     # 金叉上穿
        crossBelow = self.Ma1[-1]<self.Ma2[-1] and self.Ma1[-2]>self.Ma2[-2]    # 死叉下穿
        
        # 金叉和死叉的条件是互斥
        # 所有的委托均以K线收盘价委托
        if crossOver:
            self.Buy(bar.closePrice,1)
            
        # 死叉和金叉相反
        elif crossBelow:
            self.SellShort(bar.closePrice, 1)
                    
    def OnError(self, request):
        print "OnError"
        print request
            
    def OnLog(self, request):
        print "OnLog"
        print request
    
    def OnTrade(self, request):
        print "OnTrade"
        print request
        if request.symbol == _symbol:
            if request.direction == DIRECTION_LONG:
                self.MarketPosition += request.volume
            elif request.direction == DIRECTION_SHORT:
                self.MarketPosition -= request.volume
            print self.MarketPosition
    
    def OnOrder(self, request):
        print "OnOrder"
        print request
            
    def OnPosition(self, request):
        print "OnPosition"
        print request
        if request.symbol == _symbol:
            if request.direction == DIRECTION_LONG:
                self.MarketPosition = request.position * 1
            elif request.direction == DIRECTION_SHORT:
                self.MarketPosition = request.position * -1
            print self.MarketPosition
    def OnAccount(self, request):
        print "OnAccount"
        print request
    
def dispatchPush(client,resp):
    if resp.Is(_TICK_TYPE):
        resp_data = BfTickData()
        resp.Unpack(resp_data)
        client.OnTick(resp_data)
    elif resp.Is(_PING_TYPE):
        resp_data = BfPingData()
        resp.Unpack(resp_data)
        client.OnPing(resp_data)
    elif resp.Is(_ACCOUNT_TYPE):
        resp_data = BfAccountData()
        resp.Unpack(resp_data)
        client.OnAccount(resp_data)
    elif resp.Is(_POSITION_TYPE):
        resp_data = BfPositionData()
        resp.Unpack(resp_data)
        client.OnPosition(resp_data)
    elif resp.Is(_TRADE_TYPE):
        resp_data = BfTradeData()
        resp.Unpack(resp_data)
        client.OnTrade(resp_data)
    elif resp.Is(_ORDER_TYPE):
        resp_data = BfOrderData()
        resp.Unpack(resp_data)
        client.OnOrder(resp_data)
    elif resp.Is(_LOG_TYPE):
        resp_data = BfLogData()
        resp.Unpack(resp_data)
        client.OnLog(resp_data)
    elif resp.Is(_ERROR_TYPE):
        resp_data = BfErrorData()
        resp.Unpack(resp_data)
        client.OnError(resp_data)
    elif resp.Is(_NOTIFICATION_TYPE):
        resp_data = BfNotificationData()
        resp.Unpack(resp_data)
        if resp_data.type == NOTIFICATION_GOTCONTRACTS:
            client.OnGotContracts(resp_data)
        elif resp_data.type == NOTIFICATION_TRADEWILLBEGIN:
            client.OnTradeWillBegin(resp_data)
        else:
            print "invliad notification type"
    else:
        print "invalid push type"        
    
def connect(client):
    print "connect gateway"
    req = BfConnectPushReq(clientId=_CLIENT_ID,tickHandler=True,tradeHandler=True,logHandler=True,
                       symbol=_symbol,exchange=_exchange)
    responses = client.gateway.ConnectPush(req,timeout=_ONE_DAY_IN_SECONDS)
    for resp in responses:
        dispatchPush(client,resp)            
    print "connect quit"
    
def disconnect(client):
    print "disconnect gateway"
    req = BfVoid()
    resp = client.gateway.DisconnectPush(req,_TIMEOUT_SECONDS,metadata=_MT)
    
def tryconnect(client):
    '''subscribe dont tryconnect after server shutdown. so unsubscrible and subscrible again'''
    print "sleep 5s,try reconnect..."
    time.sleep(_TIMEOUT_SECONDS)
    client.unsubscribe()
    time.sleep(_TIMEOUT_SECONDS)
    client.subscribe()            
    time.sleep(_TIMEOUT_SECONDS)
    time.sleep(_TIMEOUT_SECONDS)
    time.sleep(_TIMEOUT_SECONDS)
    
def run():
    print "start dualcross"
    client = DualCross()
    client.subscribe()
    client.OnInit()

    try:
        while True:
            if client.connectivity == interfaces.ChannelConnectivity.READY:
                connect(client)
            tryconnect(client)
    except KeyboardInterrupt:
        print "ctrl+c"        
    
    if client.connectivity == interfaces.ChannelConnectivity.READY:
        disconnect(client)
    
    print "stop dualcross"
    client.unsubscribe()
    
if __name__ == '__main__':
    run()
