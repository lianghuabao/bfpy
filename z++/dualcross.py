# coding=utf-8

from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *

EMPTY_STRING = ''
EMPTY_FLOAT = 0.0
EMPTY_INT = 0

class DualCross(BfTraderClient):
    # 策略参数
    fastK = 0.9  # 快速EMA参数
    slowK = 0.1  # 慢速EMA参数
    initDays = 10  # 初始化数据所用的天数
    theMaxCounter = 10  # 第二个bar等待多久去取datafeed的数据

    # 策略变量
    bar = None
    barMinute = EMPTY_INT
    intFirstBarMinute = EMPTY_INT
    strFirstBarMinute = EMPTY_STRING
    theCounter = EMPTY_INT

    orderData = {}  # 订单
    pos = {'long': EMPTY_INT, 'short': EMPTY_INT}  # 仓位

    # 是否是第一个tick
    theFirstTick = True

    fastMa = []  # 快速EMA均线数组
    fastMa0 = EMPTY_FLOAT  # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT  # 上一根的快速EMA

    slowMa = []  # 与上面相同
    slowMa0 = EMPTY_FLOAT
    slowMa1 = EMPTY_FLOAT

    def __init__(self):
        super(DualCross, self).__init__()
        self.clientId = "dualcross"
        self.tickHandler = True
        self.tradeHandler = True
        self.logHandler = False
        self.symbol = "rb1609"
        self.exchange = "SHFE"


    def OnTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        print 'OnTick'

        tickHour = tick.tickTime.split(':')[0]
        tickMinute = tick.tickTime.split(':')[1]
        barMinute = int(tickHour) * 60 + int(tickMinute)  # 暂时不考虑隔夜交易
        # 收到的第一个tick
        if self.theFirstTick:
            self.theFirstTick = False
            # 确定第一个barMinute
            self.intFirstBarMinute = barMinute
            self.strFirstBarMinute = tickHour + ':' + tickMinute + ':00'
        elif barMinute == self.intFirstBarMinute:
            # 在第一个minute内的数据从datarecorder里面获取
            return
        else:
            if ((barMinute - self.intFirstBarMinute) == 1):
                # 在第二分钟，由于datarecorder未必处理完前一分钟的bar数据，故延迟theMaxCounter取数
                self.theCounter += 1
                if self.theCounter == self.theMaxCounter:
                    req = BfGetBarReq(symbol=self.symbol, exchange=self.exchange, period=PERIOD_M01,
                                      toDate=tick.actionDate,
                                      toTime=self.strFirstBarMinute,
                                      count=1)
                    responses = self.GetBar(req)
                    for resp in responses:
                        self.OnBar(resp)

            # 计算K线
            if barMinute != self.barMinute:
                if self.bar:
                    self.OnBar(self.bar)

                bar = BfBarData()
                bar.symbol = tick.symbol
                bar.exchange = tick.exchange
                bar.period = PERIOD_M01

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
                self.barMinute = barMinute  # 更新当前的分钟

            else:  # 否则继续累加新的K线
                bar = self.bar  # 写法同样为了加快速度

                bar.highPrice = max(bar.highPrice, tick.lastPrice)
                bar.lowPrice = min(bar.lowPrice, tick.lastPrice)
                bar.closePrice = tick.lastPrice

    # ----------------------------------------------------------------------
    def OnBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        print 'OnBar'
        # 计算快慢均线
        if not self.fastMa0:
            self.fastMa0 = bar.closePrice
            self.fastMa.append(self.fastMa0)
        else:
            self.fastMa1 = self.fastMa0
            self.fastMa0 = bar.closePrice * self.fastK + self.fastMa0 * (1 - self.fastK)
            self.fastMa.append(self.fastMa0)

        if not self.slowMa0:
            self.slowMa0 = bar.closePrice
            self.slowMa.append(self.slowMa0)
        else:
            self.slowMa1 = self.slowMa0
            self.slowMa0 = bar.closePrice * self.slowK + self.slowMa0 * (1 - self.slowK)
            self.slowMa.append(self.slowMa0)

        # 判断买卖
        crossOver = self.fastMa0 > self.slowMa0 and self.fastMa1 < self.slowMa1  # 金叉上穿
        crossBelow = self.fastMa0 < self.slowMa0 and self.fastMa1 > self.slowMa1  # 死叉下穿

        # 金叉和死叉的条件是互斥
        # 所有的委托均以K线收盘价委托（这里有一个实盘中无法成交的风险，考虑添加对模拟市价单类型的支持）
        # self.gateway.QueryPosition()
        if crossOver:
            req1 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=bar.closePrice,
                                  volume=self.pos['short'],
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_LONG, offset=OFFSET_CLOSE)
            req2 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=bar.closePrice, volume=1,
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_LONG, offset=OFFSET_OPEN)
            self.SendOrder(req1)
            self.SendOrder(req2)  # 死叉和金叉相反
        elif crossBelow:
            req1 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=bar.closePrice,
                                  volume=self.pos['long'],
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_SHORT, offset=OFFSET_CLOSE)
            req2 = BfSendOrderReq(symbol=self.symbol, exchange=self.exchange, price=bar.closePrice, volume=1,
                                  priceType=PRICETYPE_LIMITPRICE, direction=DIRECTION_SHORT, offset=OFFSET_OPEN)
            self.SendOrder(req1)
            self.SendOrder(req2)

    def OnTrade(self, tradeData):
        print "OnTrade"
        print tradeData
        if tradeData.symbol == self.symbol:
            if tradeData.direction == DIRECTION_LONG and tradeData.offset == OFFSET_OPEN:
                self.pos['long'] += 1
            elif tradeData.direction == DIRECTION_SHORT and tradeData.offset == OFFSET_OPEN:
                self.pos['short'] += 1
            elif tradeData.direction == DIRECTION_LONG and tradeData.offset == OFFSET_CLOSE:
                self.pos['short'] -= 1
            elif tradeData.direction == DIRECTION_SHORT and tradeData.offset == OFFSET_CLOSE:
                self.pos['long'] -= 1

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


if __name__ == '__main__':
    client = DualCross()
    BfRun(client, clientId=client.clientId, tickHandler=client.tickHandler, tradeHandler=client.tradeHandler,
          logHandler=client.logHandler, symbol=client.symbol, exchange=client.exchange)
