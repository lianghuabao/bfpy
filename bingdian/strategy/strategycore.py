# coding=utf-8
#creat by Bingdian(QQ:251859269)
import sys
sys.path.append("..")
from sdk.bftraderclient import BfTraderClient,BfRun
from sdk.bfgateway_pb2 import *
from sdk.bfdatafeed_pb2 import *
import PrintColor
import numpy as np
import pandas as pd
import time
from dataserver import bfHistoryData as dataserver
_ONE_DAY_IN_SECONDS = 60 * 60 * 24
_TIMEOUT_SECONDS = 1

# 默认空值
EMPTY_STRING = ''
EMPTY_UNICODE = u''
EMPTY_INT = 0
EMPTY_FLOAT = 0.0
TR_Direction=[u'未知',u'买入',u'卖出',u'Net']
TR_Offset=[u'未知',u'开仓',u'平仓',u'平今',u'平昨']
ORDER_STATUS=[u'状态未知',u'未成交',u'部分成交',u'全部成交',u'已撤销']
class EMPTY_CLASS:pass

class StrategyCore(BfTraderClient):
    #gatewayserver=EMPTY_CLASS()
    #dataserver=dataserver.bfDataFeed()
    reconnect=True #在bftraderclient._tryconnect中添加"client.reconnect=False",用于判断是否需要盘中补数据
    clrPrint = PrintColor.Color() 
    # 策略变量
    orderData = {}  # 订单
    orderFollow={}
    pos = {'td_long': EMPTY_INT,'yd_long':EMPTY_INT, 'td_short': EMPTY_INT,'yd_short': EMPTY_INT}  # 仓位
    #frozenPos={'long': EMPTY_INT, 'short': EMPTY_INT,'shtd_long':EMPTY_INT,'shtd_short': EMPTY_INT} #冻结仓位,上交所今仓单独,其他今昨合并
    frozenPos={DIRECTION_LONG:{OFFSET_CLOSE:0,OFFSET_CLOSETODAY:0},DIRECTION_SHORT:{OFFSET_CLOSE:0,OFFSET_CLOSETODAY:0}}
    #冻结仓位的方向与持单方向相反， 空单减仓冻结多单买平未成交部分
    bidvol=EMPTY_INT
    bidprice=EMPTY_FLOAT
    askvol=EMPTY_INT
    askprice=EMPTY_FLOAT
    lastprice=EMPTY_FLOAT
    lastvol=EMPTY_INT
    
        
    #策略参数,在算法实例中初始化
    clientID=EMPTY_STRING 
    clientMT=[("clientid",clientID)]
    symbol=EMPTY_STRING 
    exchange=EMPTY_STRING
    leastBars=EMPTY_INT #计算需要的bar数
    period={'bfPeriod':EMPTY_INT,'TALIB_NAME':EMPTY_STRING,'secondsOfPeriod':EMPTY_INT,'ticksOfSecond':2}
    #bfPeriod----------------bf周期:PERIOD_M01,PERIOD_M03,PERIOD_M05,PERIOD_M15,PERIOD_M60,PERIOD_D01,PERIOD_W01
    #TALIB_NAME--------------tablib 周期: 1MIN 5MIN 15MIN 60MIN 1D 1W 1M
    #secondsOfPeriod=60 -----每周期秒数
    #ticksOfSecond=2.0--------tick/秒，用于计算 补数据的条数
    offsetNum=EMPTY_INT #每次交易手数 
    strategyMulti=False#多策略运行于同一合约, 仓位/订单均独立,不与网关同步,仅接收myTaskData
    
    
    def __init__(self):
        BfTraderClient.__init__(self)
        self.clientID = "StrategyCore"
        self.clientMT=[("clientid",self.clientID)]
        self.strategyMulti=False#多策略运行于同一合约, 仓位/订单均独立,不与网关同步,仅接收myTaskData
        self.tickHandler = True
        self.tradeHandler = True
        self.logHandler = True
        self.symbol = "rb1610"
        self.exchange = "SHFE"
        self.period={'bfPeriod':PERIOD_M01,'TALIB_NAME':'1MIN','secondsOfPeriod':60,'ticksOfSecond':2}
        self.leastBars=10
        
       
        
    #----------------------------------------------------------------------
    #数据补充
    def datafeedBarCount(self,count,period):
        #print 'count:',count , 'periond:',period
        self.bar=dataserver.getBarData(self,count,period)
        print self.bar
        
      
    def datafeedBarFrmDateTime(self,tickDateTime,period):
        #处理,补数据时收到新的Tick
        #ToDo:datefeed增加获取tick方向后,简化
        start=pd.to_datetime(self.bar.tail(1).index.values[0])#从最后一个bar的开始取,倒序
        end=tickDateTime
        temp_bar=dataserver.getTick2BarFrmTo(self,start,end,period)
        self.bar=pd.concat([self.bar[:-1],temp_bar])
        
   #----------------------------------------------------------------------
   #下单函数
    def buy(self, price, volume):
        """买开"""
        
        req = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=price, volume=volume,
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_LONG, offset=OFFSET_OPEN)
        order_open=self.SendOrder(req)
        print TR_Direction[req.direction],TR_Offset[req.offset],req.price,req.volume
        self.orderData[order_open.bfOrderId]=order_open
        return order_open
        
    
    
    def sell(self, price, volume):#返回两个单号
        """卖平"""
        # 只有上期所才要考虑平今平昨
        order1=None
        order2=None
        td_AvailablePos=self.pos['td_long']-self.frozenPos[DIRECTION_SHORT][OFFSET_CLOSETODAY]
        if self.exchange=='SHFE' and td_AvailablePos>0: #今仓优先平
            tdVolume=min(td_AvailablePos,volume)
            req = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=price, volume=tdVolume,
                                     priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_SHORT, offset=OFFSET_CLOSETODAY)
            order1=self.SendOrder(req)
            print TR_Direction[req.direction],TR_Offset[req.offset],req.price,req.volume
            self.frozenPos[req.direction][req.offset] += tdVolume
            self.orderData[order1.bfOrderId]=order1
            volume -= tdVolume #更新volume
        if volume>0:
            self.frozenPos['long'] +=volume
            req = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=price, volume=volume,
                                 priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_SHORT, offset=OFFSET_CLOSE)
            order2=self.SendOrder(req)
            print TR_Direction[req.direction],TR_Offset[req.offset],req.price,req.volume
            self.frozenPos[req.direction][req.offset] += Volume
            self.orderData[order2.bfOrderId]=order2
        return order1,order2      
        
            

   
    def short(self, price, volume):
        """卖开"""
        req = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=price, volume=volume,
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_SHORT, offset=OFFSET_OPEN)
        order_open=self.SendOrder(req)
        print TR_Direction[req.direction],TR_Offset[req.offset],req.price,req.volume
        self.orderData[order_open.bfOrderId]=order_open
        
                    
        return order_open
 
    def cover(self, price, volume): #返回两个单号
        # 只有上期所才要考虑平今平昨
        order1=None
        order2=None
        td_AvailablePos=self.pos['td_short']-self.frozenPos[DIRECTION_LONG][OFFSET_CLOSETODAY]
        if self.exchange=='SHFE' and td_AvailablePos>0: #今仓优先平
            tdVolume=min(td_AvailablePos,volume)
            req = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=price, volume=tdVolume,
                                     priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_LONG, offset=OFFSET_CLOSETODAY)
            order1=self.SendOrder(req)
            print TR_Direction[req.direction],TR_Offset[req.offset],req.price,req.volume
            self.frozenPos[req.direction][req.offset] += tdVolume
            self.orderData[order1.bfOrderId]=order1
            volume -= tdVolume #更新volume
        if volume>0:
            
            req = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=price, volume=volume,
                                 priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_LONG, offset=OFFSET_CLOSE)
            order2=self.SendOrder(req)
            print TR_Direction[req.direction],TR_Offset[req.offset],req.price,req.volume
            self.frozenPos[req.direction][req.offset] += Volume
            self.orderData[order2.bfOrderId]=order2
        return order1,order2      
    
    
   
    def SP_BK(self,price,volume): #空翻多, 返回三个单号---平今 平昨 开仓
        order_close1=None
        order_close2=None
        toltal_pos=self.pos['td_short']+self.pos['yd_short'] \
            -self.frozenPos[DIRECTION_LONG][OFFSET_CLOSETODAY]-self.frozenPos[DIRECTION_LONG][OFFSET_CLOSE]
        #有反向仓位,先全平
        if toltal_pos>0:
            order_close1,order_close2=self.cover(price,toltal_pos)
        order_open=self.buy(price,volume) 
       
        return order_close1,order_close2,order_open
        
    def BP_SK(self,price,volume):#多翻空, 返回三个单号---平今 平昨 开仓
        order_close1=None
        order_close2=None  
        #有反向仓位,先全平
        toltal_pos=self.pos['td_long']+self.pos['yd_long'] \
            -self.frozenPos[DIRECTION_SHORT][OFFSET_CLOSETODAY]-self.frozenPos[DIRECTION_SHORT][OFFSET_CLOSE]
        #有反向仓位,先全平
        if toltal_pos>0:
            order_close,order2=self.sell(price,toltal_pos)
        order_open=self.short(price,volume) 
        
        return order_close1,order_close2,order_open
    #----------------------------------------------------------------------
    #定单管理
    #参数:orderId 定单号 bfOrderId, price 价差 , seconds 超时秒数,  b_After 连续追单
    #
    def orderMNG_insert(self,orderId,price_dif=999999,seconds=999999,b_After=False):
         self.orderFollow[orderId]=[price_dif,seconds,b_After,0]#0：撤单成功标志 0未处理;1 已提交撤单;2 撤单成功
                                                                  #0  临时存放部分成交 的交易量 #测试后简化
         
        
    def orderMNG_DO(self):
        for k,v in self.orderFollow.items(): 
            if k in  self.orderData :
                order=self.orderData[k]
                if type(order) != BfOrderData :break  # !=BfSendOrderReq
                signNeg= -1 if order.direction== DIRECTION_SHORT else 1
                if v[3]==0 and (order.status == STATUS_PARTTRADED or order.status==STATUS_NOTTRADED) and \
                    (  signNeg*(self.lastprice-order.price)>=v[0] or  \
                      (pd.to_datetime(self.ticktime)-pd.to_datetime(order.insertDate+' '+order.insertTime)).total_seconds()>=v[1]):
                    print u'撤单:' ,TR_Direction[order.direction],TR_Offset[order.offset],order.price,order.totalVolume,ORDER_STATUS[order.status],order.bfOrderId
                    
                    req = BfCancelOrderReq(symbol=order.symbol, exchange=order.exchange,bfOrderId=order.bfOrderId)
                    self.CancelOrder(req)
                    self.orderFollow[k][3]=1 
                
                #if order.status == STATUS_PARTTRADED:
                #    self.orderFollow[k][4] = max(v[4],order.tradedVolume )#测试后简化:部分成交的撤单tradedVolume返回值 
                #    print order
                
                if order.status==STATUS_CANCELLED and v[2]==1 and v[3]==1:
                    #撤单成功，对价追
                    #部分成交的剩余量????
                    print u'**************撤单成功，对价追************************'
                    volume_after=order.totalVolume-order.tradedVolume
                    price_after=self.bidprice if order.direction==DIRECTION_SHORT else self.askprice 
                    req = BfSendOrderReq(symbol=order.symbol, exchange=order.exchange, price=price_after, 
                           volume=volume_after, priceType=PRICETYPE_LIMITPRICE, direction=order.direction, offset=order.offset)
                    order_after=self.SendOrder(req)
                    self.orderData[order_after.bfOrderId]=order_after
                    self.orderMNG_insert(order_after.bfOrderId,1,3,True)#连续追单
                    if order.offset == OFFSET_CLOSETODAY or order.offset == OFFSET_CLOSE :
                        self.frozenPos[order.direction][order.offset] += volume_after
                    print u'对价追:',TR_Direction[order.direction],TR_Offset[order.offset],price_after,volume_after,order_after.bfOrderId
                    
                if order.status==STATUS_ALLTRADED or order.status==STATUS_CANCELLED:
                       del self.orderFollow[k]  
                
     #----------------------------------------------------------------------  
     #交易信号
    def singalOnTick(self): 
        pass
        

   
    def singalOnBarOpen(self):
        pass
   
    def singalOnBarclose(self):
        #raise NotImplementedError
        pass
            
     #----------------------------------------------------------------------    
    def OnStart(self):
        print "====================================OnStart================="
        self.datafeedBarCount(self.leastBars,self.period)
        print 'finish OnInit'
        
    def OnTradeWillBegin(self, response):
        print "===============================OnTradeWillBegin"
        print response        

    def OnGotContracts(self, response):
        print "==================================OnGotContracts"
        print response
        
        #
        # save contract
        #
        req = BfGetContractReq(symbol="*",exchange="*")
        resps = self.GwGetContract(req)
        for resp in resps:
            #print resp
            self.InsertContract(resp)
        
    def OnPing(self, response):
        #print "OnPing"
        #print response
        pass

    def OnTick(self, tick):
        #处理实盘"0" 值tick
        start_do_tick=time.clock()
        self.bidvol=tick.bidVolume1 if tick.bidVolume1>0 else self.bidvol
        self.askvol=tick.askVolume1 if tick.askVolume1 >0 else self.askvol
        self.bidprice=tick.bidPrice1 if tick.bidPrice1>0 else  self.bidprice
        self.askprice=tick.askPrice1 if tick.askPrice1>0 else self.askprice
        self.lastprice=tick.lastPrice if tick.lastPrice>0 else self.lastprice
        self.lastvol=tick.lastVolume if tick.lastVolume >0 else 0
        self.ticktime=tick.tickTime 
        
        
        tickDateTime=pd.to_datetime(tick.actionDate+' '+tick.tickTime)
        tickPrice=self.lastprice
        tickVolume=self.lastvol
        self.orderMNG_DO()#定单管理
        if self.reconnect==True :#client 中断5秒重连，补数据 更新仓位
            print 'Reconnect:get tick  from datafeed,and update bar '
            self.datafeedBarFrmDateTime(tickDateTime,self.period)
            self.reconnect=False
            self.tickInbar=1
            if self.strategyMulti==False:
                self.QueryPosition()#多策略独立维护仓位,不需要同步
            
        else:
            lastbar=self.bar.tail(1)
            lastbarDateTime=pd.to_datetime(lastbar.index.values[0])
            
            tickSecondsOfLastbar=(tickDateTime-lastbarDateTime).total_seconds()
            if tickSecondsOfLastbar<self.period['secondsOfPeriod']:
                self.tickInbar=self.tickInbar+1
                lastbarOpen=lastbar.open[0]
                lastbarHigh=max(lastbar.high[0],tickPrice)
                lastbarLow=min(lastbar.low[0],tickPrice)
                lastbarClose=tickPrice
                lastbarVolume=lastbar.volume[0]+tickVolume
                self.bar.iloc[-1]=(lastbarOpen,lastbarHigh,lastbarLow,lastbarClose,lastbarVolume)#直接修改原始对象
                print lastbarDateTime,'',lastbarOpen,'',lastbarHigh,'',lastbarLow,'',
                if lastbarClose>self.bidprice: 
                    self.clrPrint.print_red_text_oneline(lastbarClose)
                    print '',lastbarVolume,
                    self.clrPrint.print_red_text_oneline(self.lastvol)
                else:
                    self.clrPrint.print_green_text_oneline(lastbarClose)
                    print '',lastbarVolume,
                    self.clrPrint.print_green_text_oneline(self.lastvol)
                print '        \r',
                #计算Tick交易信号
                self.singalOnTick()
            else:
                #new bar
                self.tickInbar=1
                #防止bar的开始时间点没有的tick, 若周期内无tick(小节间),则不生成bar,不能使用tickDateTime:作为新bar的开始
                newBarDateTime=lastbarDateTime+pd.Timedelta(seconds=self.period['secondsOfPeriod']*int(tickSecondsOfLastbar/self.period['secondsOfPeriod'])) 
                newbar=pd.DataFrame([(tickPrice,tickPrice,tickPrice,tickPrice,tickVolume)],columns=['open','high','low','close','volume'],index=[newBarDateTime])
                #上根bar收盘,计算交易信号
                self.singalOnBarclose()
                self.bar=pd.concat([self.bar,newbar])
                print '\n concatbar**********************\n',self.bar.tail(self.leastBars) 
                #新bar开盘,计算交易信号
                self.singalOnBarOpen()
        #监测Tick处理时长
        time_dowith_tick=time.clock()-start_do_tick
        if time_dowith_tick>0.3:
            self.clrPrint.print_red_text("=================time to Do tick=============",time_dowith_tick)
        if time_dowith_tick>1/float(self.period['ticksOfSecond']):
            self.reconnect=True #重连则从datafeed补tick
    def OnError(self, response):
        print "====================OnError================"
        print response.message.encode("GBK")
            
    def OnLog(self, response):
        print "================OnLog=================="
        print response.message.encode("GBK")
    #--------------------------------------------------------------------------
    #仓位数据
    def OnTrade(self, tradeData):
        isMyData=  self.strategyMulti==False or tradeData.bfOrderId in self.orderData #多策略独立维护仓位,不需要同步
        if tradeData.symbol == self.symbol and isMyData :
            if tradeData.direction == DIRECTION_LONG and tradeData.offset == OFFSET_OPEN:
                self.pos['td_long'] += tradeData.volume
            if tradeData.direction == DIRECTION_SHORT and tradeData.offset == OFFSET_OPEN:
                self.pos['td_short'] += tradeData.volume
            
            if tradeData.direction == DIRECTION_LONG and tradeData.offset == OFFSET_CLOSE :
                self.pos['td_short'] -= tradeData.volume
                if self.pos['td_short']<0 : #非上期所,平仓数是昨仓和今仓的和 , 大于昨仓
                    self.pos['yd_short'] +=self.pos['td_short']
                    self.pos['td_short']=0
            if tradeData.direction == DIRECTION_SHORT and tradeData.offset == OFFSET_CLOSE :
                self.pos['td_long'] -= tradeData.volume
                if self.pos['td_long']<0 : #非上期所,平仓数是昨仓和今仓的和 , 大于昨仓
                    self.pos['yd_long'] +=self.pos['td_long']
                    self.pos['td_long']=0
            
            if tradeData.direction == DIRECTION_LONG and tradeData.offset == OFFSET_CLOSETODAY:
                self.pos['td_short'] -= tradeData.volume
            if tradeData.direction == DIRECTION_SHORT and tradeData.offset == OFFSET_CLOSETODAY:
                self.pos['td_long'] -= tradeData.volume
            print u'\n成交回报:',tradeData.symbol,TR_Direction[tradeData.direction], \
                        TR_Offset[tradeData.offset],tradeData.price,tradeData.volume,tradeData.bfOrderId
            self.clrPrint.print_blue_text(self.pos)
            
    
        
    
    def OnOrder(self, orderData):
        isMyData = orderData.bfOrderId in self.orderData
        if orderData.symbol == self.symbol and isMyData:
            self.orderData[orderData.bfOrderId] = orderData
            if orderData.status >1 and  orderData.offset == OFFSET_CLOSETODAY or orderData.offset == OFFSET_CLOSE :
                    freeValume=orderData.totalVolume-orderData.tradedVolume if orderData.status == STATUS_CANCELLED else orderData.tradedVolume
                    self.frozenPos[orderData.direction][orderData.offset] -= freeValume
                    
                
                
                
                
    def OnPosition(self, posData):
        if self.strategyMulti==True: return #多策略独立维护仓位,不需要同步
        if posData.symbol == self.symbol:
            print posData
            if posData.direction==DIRECTION_LONG :
                if posData.ydPosition==0 and posData.position>0: #昨仓为0，是今仓数据 
                    self.pos['td_long'] = posData.position
                if posData.ydPosition>0 and posData.position>0:
                    self.pos['yd_long']=posData.ydPosition
            if posData.direction==DIRECTION_SHORT :
                if posData.ydPosition==0 and posData.position>0:
                    self.pos['td_short'] = posData.position
                if posData.ydPosition>0 and posData.position>0:
                    self.pos['yd_short']=posData.ydPosition
                    
            self.clrPrint.print_blue_text(self.pos)
            if posData.frozen>0 :
                #开仓委托未成交部分,用于冻结保证金???有无postion区别??
                print posData
         
    #-----------------------------------------------------------------------
    def OnAccount(self, response):
        print "OnAccount"
        print response
        
    def OnStop(self):
        print "=======================================OnStop"

if __name__ == '__main__':
    client = StrategyCore()
    BfRun(client,clientId=client.clientID,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)
