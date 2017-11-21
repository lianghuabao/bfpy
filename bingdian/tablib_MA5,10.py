# coding=utf-8
#creat by Bingdian(QQ:251859269)
from   strategy.strategycore import *
import strategy.quickFuncion as qf
import talib as ta


class ma_cross_algo(StrategyCore):
    def __init__(self):
        print "macross__init__"
        StrategyCore.__init__(self)
        self.clientID = "macross_5_10"
        self.clientMT=[("clientid",self.clientID)]
        
        self.strategyMulti=True#多策略运行于同一合约, 仓位/订单均独立,不与网关同步,仅接收myTaskData; 注意同一合约保持一致
        self.symbol = "ag1612"
        self.exchange = "SHFE"
        self.period={'bfPeriod':PERIOD_M01,'TALIB_NAME':'1MIN','secondsOfPeriod':60,'ticksOfSecond':2}
        '''
        TALIB_NAME='2MIN' #talib周期 : 1MIN 5MIN 15MIN 60MIN 1D 1W 1M
        secondsOfPeriod=120#每周期秒数
        ticksOfSecond=2 #每秒2Tick
        '''
        self.ma1_p=5
        self.ma2_p=10
        self.leastBars=10+3#self.ma2_p+3 #cross需要3根k判断
        self.offsetNum=2 #每单2手
        
        
    def singalOnTick(self):
        pass
    def singalOnBarOpen(self):
        pass        
    def singalOnBarclose(self):
        ma1=ta.SMA(self.bar['close'].values.astype(np.float),self.ma1_p)[-3:]
        ma2=ta.SMA(self.bar['close'].values.astype(np.float),self.ma2_p)[-3:]
        print '\n singalOnBarclose:'
        print ma1
        print ma2,
        if qf.cross(ma1,ma2):
            print u'金叉'
            order_close,order_close_yd,order_open=self.SP_BK(self.bidprice-1,self.offsetNum) #本方价-1,买反手开仓
            #追撤单设置:
            if order_close != None:
                self.orderMNG_insert(order_close.bfOrderId,price_dif=2,b_After=True) #差价2,连续追平
            if order_close_yd != None:
                self.orderMNG_insert(order_close_yd.bfOrderId,seconds=5,b_After=True)#5秒为成交,连续追平
            self.orderMNG_insert(order_open.bfOrderId,price_dif=2)#差价2,撤单
        if qf.cross(ma2,ma1):
            print u'死叉'
            order_close,order_close_yd,order_open=self.BP_SK(self.askprice+1,self.offsetNum)  #本方价+1,反手开仓
            #追撤单设置:
            if order_close != None:
                self.orderMNG_insert(order_close.bfOrderId,price_dif=2,b_After=True) #差价2,连续追平
            if order_close_yd != None:
                self.orderMNG_insert(order_close_yd.bfOrderId,seconds=5,b_After=True)#5秒为成交,连续追平
            self.orderMNG_insert(order_open.bfOrderId,price_dif=2)#差价2,撤单


if __name__ == '__main__':
    client = ma_cross_algo()
    BfRun(client,clientId=client.clientID,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)

            
            