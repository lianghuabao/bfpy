# coding=utf-8
#creat by Bingdian(QQ:251859269)
from   strategy.strategycore import *
import strategy.quickFuncion as qf
import talib as ta

class ma_cross_algo(StrategyCore):
    def __init__(self):
        print "macd_dif dea cross__init__"
        StrategyCore.__init__(self)
        self.clientID='macd_dif_cross'
        self.clientMT=[("clientid",self.clientID)]
        self.symbol='ag1612'
        self.exchange='SHFE'
        self.strategyMulti=False #本合约只运行一个策略,与网关同步
        #self.strategyMulti=True#多策略运行于同一合约, 仓位/订单均独立,不与网关同步,仅接收myTaskData; 注意同一合约保持一致
        self.period={'bfPeriod':PERIOD_M01,'TALIB_NAME':'1MIN','secondsOfPeriod':60,'ticksOfSecond':2}
        self.period={'bfPeriod':PERIOD_M03,'TALIB_NAME':'3MIN','secondsOfPeriod':180,'ticksOfSecond':2}
        #bfPeriod----------------bf周期:PERIOD_M01,PERIOD_M03,PERIOD_M05,PERIOD_M15,PERIOD_M60,PERIOD_D01,PERIOD_W01
        #TALIB_NAME--------------tablib 周期: 1MIN 5MIN 15MIN 60MIN 1D 1W 1M
        #secondsOfPeriod=60 -----每周期秒数
        #ticksOfSecond=2.0--------tick/秒，用于计算 补数据的条数
        self.fastperiod=12
        self.slowperiod=26
        self.signalperiod=9
        self.leastBars=26+3 #cross需要3根k判断
        self.offsetNum=2 #每单2手
        
        self.test=0
    def singalOnTick(self):
        pass
        
    def singalOnBarOpen(self):
        pass        
    def singalOnBarclose(self):
        np_close=np.array(self.bar['close'],dtype=np.float) #TA-lib wants numpy arrays of "double" floats as inputs
        DIFF, DEA, MACD = ta.MACD(np_close, self.fastperiod, self.slowperiod, self.signalperiod)
        print '\n macd Singal:'
        print 'DIF:',DIFF[-3:]
        print 'DEA:',DEA[-3:],
        #DIFF与DEA交叉交易
        if qf.cross(DIFF[-3:],DEA[-3:]):
            print u'LONG:'
            #反手单分为三笔订单
            order_close,order_close_yd,order_open = self.SP_BK(self.bidprice,self.offsetNum) #本方价,买反手开仓
            #追撤单设置:
            if order_close != None:
                self.orderMNG_insert(order_close.bfOrderId,price_dif=2,b_After=True) #差价2,连续追平
            if order_close_yd != None:
                self.orderMNG_insert(order_close_yd.bfOrderId,seconds=5,b_After=True)#5秒为成交,连续追平
            self.orderMNG_insert(order_open.bfOrderId,price_dif=2)#差价2,撤单
        if qf.cross(DEA[-3:],DIFF[-3:]):
            print u'Short:'
            order_close,order_close_yd,order_open=self.BP_SK(self.askprice,self.offsetNum)  #本方价,反手开仓
            #追撤单设置:
            if order_close != None:
                self.orderMNG_insert(order_close.bfOrderId,price_dif=2,b_After=True) #差价2,连续追平
            if order_close_yd !=None:
                self.orderMNG_insert(order_close_yd.bfOrderId,seconds=5,b_After=True)#5秒为成交,连续追平
            self.orderMNG_insert(order_open.bfOrderId,price_dif=2)#差价2,撤单


if __name__ == '__main__':
    client = ma_cross_algo()
    BfRun(client,clientId=client.clientID,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)

 