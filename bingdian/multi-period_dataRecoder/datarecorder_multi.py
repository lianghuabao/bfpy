# coding=utf-8
#creat by XiaoGe(QQ:376999514)
#modified by bingdian(QQ:251859269) : CheckTimeInterval
import sys
sys.path.append("..\sdk")
import datetime as dt
import copy
from timesection import *
import re

from datarecorder import DataRecorder

from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *

class DataRecorder_Multi(DataRecorder):
    def __init__(self):
        # # 继承基类
        DataRecorder.__init__(self)

        # # --------------------------------------------------
        self.tickfilter = False

        self.period_key_list = ['M01', 'M03', 'M05', 'M10', 'M15', 'M30', 'H01', 'D01', 'W01']
        self.PERIOD = {}
        self.PERIOD['M01'] = PERIOD_M01
        self.PERIOD['M03'] = PERIOD_M03
        self.PERIOD['M05'] = PERIOD_M05
        self.PERIOD['M10'] = PERIOD_M10
        self.PERIOD['M15'] = PERIOD_M15
        self.PERIOD['M30'] = PERIOD_M30
        self.PERIOD['H01'] = PERIOD_H01
        self.PERIOD['D01'] = PERIOD_D01
        self.PERIOD['W01'] = PERIOD_W01
        # Bar的时间戳
        self.last_dt_bar = {}
        # 当前累积的Bar
        self.CntBar = {}
        # 上一个Bar
        self.last_bar = {}

        # # 获取合约
        req = BfGetContractReq(symbol="*", exchange="*")
        resps = self.GwGetContract(req)
        symbol_list = []
        for resp in resps:
            print resp
            self.InsertContract(resp)
            symbol_list = symbol_list + [resp.symbol]
            print '*' * 60
        # # 根据合约初始化
        for symbol in symbol_list:
            if symbol not in self.last_dt_bar.keys():
                self.last_dt_bar[symbol] = {}
                self.CntBar[symbol] = {}
                self.last_bar[symbol] = {}
                dt_now = dt.datetime.now()
                for k in self.period_key_list:
                    self.last_dt_bar[symbol][k] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour,
                                                              dt_now.minute / int(k[1:]) * int(k[1:]), 0)
                    self.CntBar[symbol][k] = BfBarData()
                    self.last_bar[symbol][k] = BfBarData()


    def OnGotContracts(self, response):
        # # 继承基类
        DataRecorder.OnGotContracts(self, response)
        # # 获取合约
        req = BfGetContractReq(symbol="*",exchange="*")
        resps = self.GwGetContract(req)
        symbol_list = []
        for resp in resps:
            print resp
            self.InsertContract(resp)
            symbol_list = symbol_list + [resp.symbol]
            print '*' * 60
        # # 根据合约初始化
        for symbol in symbol_list:
            if symbol not in self.last_dt_bar.keys():
                self.last_dt_bar[symbol] = {}
                self.CntBar[symbol] = {}
                self.last_bar[symbol] = {}
                dt_now = dt.datetime.now()
                for k in self.period_key_list:
                    self.last_dt_bar[symbol][k] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour,
                                                              dt_now.minute / int(k[1:]) * int(k[1:]), 0)
                    self.CntBar[symbol][k] = BfBarData()
                    self.last_bar[symbol][k] = BfBarData()


    def OnTick(self, response):
        # # 继承基类
        DataRecorder.OnTick(self,response)

        # # --------------------------------------------------
        # # 第一次订阅
        # if response.symbol not in self.last_dt_bar.keys():
        #     self.last_dt_bar[response.symbol] = {}
        #     self.CntBar[response.symbol] = {}
        #     self.last_bar[response.symbol] = {}
        #     dt_now = dt.datetime.now()
        #     for k in self.period_key_list:
        #         self.last_dt_bar[response.symbol][k] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour,
        #                                           dt_now.minute / int(k[1:]) * int(k[1:]), 0)
        #         self.CntBar[response.symbol][k] = BfBarData()
        #         self.last_bar[response.symbol][k] = BfBarData()

        # # 当前时刻

        dt_now = dt.datetime.strptime(response.actionDate + " " + response.tickTime, "%Y%m%d %H:%M:%S.%f")
        # print dt_now
        # # 当前bar时间戳
        dt_bar = {}
        dt_bar['M01'] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, dt_now.minute, 0)
        dt_bar['M03'] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, dt_now.minute / 3 * 3, 0)
        dt_bar['M05'] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, dt_now.minute / 5 * 5, 0)
        dt_bar['M10'] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, dt_now.minute / 10 * 10, 0)
        dt_bar['M15'] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, dt_now.minute / 15 * 15, 0)
        dt_bar['M30'] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, dt_now.minute / 30 * 30, 0)
        dt_bar['H01'] = dt.datetime(dt_now.year, dt_now.month, dt_now.day, dt_now.hour, 0, 0)
        dt_now_shift4 = dt_now + dt.timedelta(hours=4) #21点为 次日
        dt_bar['D01'] = dt.datetime(dt_now_shift4.year, dt_now_shift4.month, dt_now_shift4.day, 0, 0, 0)
        dt_bar['W01'] = dt_bar['D01'] - dt.timedelta(days=dt_bar['D01'].weekday())

        # print '*'*60

        self.Tick_To_M01(dt_bar, response, PERIOD_M01)


    def Tick_To_M01(self, dt_bar, Tick, Period):
        # # 判断是否同一个Bar
        if (dt_bar['M01'] == self.last_dt_bar[Tick.symbol]['M01']):
            # # 同一个Bar
            self.CntBar[Tick.symbol]['M01'].volume = Tick.volume
            self.CntBar[Tick.symbol]['M01'].lastVolume = self.CntBar[Tick.symbol]['M01'].lastVolume \
                                                         + Tick.lastVolume
            self.CntBar[Tick.symbol]['M01'].openInterest = Tick.openInterest
            self.CntBar[Tick.symbol]['M01'].highPrice = max(self.CntBar[Tick.symbol]['M01'].highPrice,
                                                            Tick.lastPrice)
            self.CntBar[Tick.symbol]['M01'].lowPrice = min(self.CntBar[Tick.symbol]['M01'].lowPrice,
                                                           Tick.lastPrice)
            self.CntBar[Tick.symbol]['M01'].closePrice = Tick.lastPrice
        else:
            print dt_bar['M01']
            # print Tick
            # # 推送旧Bar
            self.last_bar[Tick.symbol]['M01'] = copy.deepcopy(self.CntBar[Tick.symbol]['M01'])
            # # 判断是否在交易时间内
            time_interval = self.CheckTimeInterval(Tick.symbol, self.last_dt_bar[Tick.symbol]['M01'].time())
            print 'time_interval: ' + str(time_interval)
            if time_interval | (self.tickfilter==False):
                resp = self.InsertBar(self.last_bar[Tick.symbol]['M01'])

            print self.last_bar[Tick.symbol]['M01']

            self.last_dt_bar[Tick.symbol]['M01'] = dt_bar['M01']
            # # 建立新的CntBar['M01']
            self.CntBar[Tick.symbol]['M01'].symbol = Tick.symbol
            self.CntBar[Tick.symbol]['M01'].exchange = Tick.exchange
            self.CntBar[Tick.symbol]['M01'].period = Period
            self.CntBar[Tick.symbol]['M01'].actionDate = dt.datetime.strftime(dt_bar['M01'], "%Y%m%d")
            self.CntBar[Tick.symbol]['M01'].barTime = dt.datetime.strftime(dt_bar['M01'], "%H:%M:%S")
            self.CntBar[Tick.symbol]['M01'].openPrice = Tick.lastPrice
            self.CntBar[Tick.symbol]['M01'].highPrice = Tick.lastPrice
            self.CntBar[Tick.symbol]['M01'].lowPrice = Tick.lastPrice
            self.CntBar[Tick.symbol]['M01'].closePrice = Tick.lastPrice
            self.CntBar[Tick.symbol]['M01'].volume = Tick.volume
            self.CntBar[Tick.symbol]['M01'].openInterest = Tick.openInterest
            self.CntBar[Tick.symbol]['M01'].lastVolume = Tick.lastVolume

            # # 基于M01生成其他Min的Bar
            for key in self.period_key_list[1:6]:
                self.M01_To_Mnn(dt_bar, Tick.symbol, key)


    def M01_To_Mnn(self, dt_bar, symbol, period_key):
        # # 先按1Min更新，然后判断是否新Bar
        if True:
            self.CntBar[symbol][period_key].volume = self.last_bar[symbol]['M01'].volume
            self.CntBar[symbol][period_key].openInterest = self.last_bar[symbol]['M01'].openInterest
            # self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol][period_key].lastVolume \
            #                                              + self.last_bar[symbol]['M01'].lastVolume
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol][period_key].volume \
                                                         - self.last_bar[symbol][period_key].volume
            self.CntBar[symbol][period_key].highPrice = max(self.CntBar[symbol][period_key].highPrice,
                                                            self.last_bar[symbol]['M01'].highPrice)
            self.CntBar[symbol][period_key].lowPrice = min(self.CntBar[symbol][period_key].lowPrice,
                                                           self.last_bar[symbol]['M01'].lowPrice)
            self.CntBar[symbol][period_key].closePrice = self.last_bar[symbol]['M01'].closePrice
        if (dt_bar[period_key] != self.last_dt_bar[symbol][period_key]):
            # # 推送旧Bar
            self.last_bar[symbol][period_key] = copy.deepcopy(self.CntBar[symbol][period_key])
            # # 判断是否在交易时间内
            time_interval = self.CheckTimeInterval(symbol, self.last_dt_bar[symbol][period_key].time())
            print symbol,'time_interval: ' + str(time_interval)
            if time_interval | (self.tickfilter==False):
                resp = self.InsertBar(self.last_bar[symbol][period_key])

            print self.last_bar[symbol][period_key]

            self.last_dt_bar[symbol][period_key] = dt_bar[period_key]

            # # 建立新的CntBar[period_key]
            self.CntBar[symbol][period_key].symbol = self.CntBar[symbol]['M01'].symbol
            self.CntBar[symbol][period_key].exchange = self.CntBar[symbol]['M01'].exchange
            self.CntBar[symbol][period_key].period = self.PERIOD[period_key]
            self.CntBar[symbol][period_key].actionDate = dt.datetime.strftime(dt_bar[period_key], "%Y%m%d")
            self.CntBar[symbol][period_key].barTime = dt.datetime.strftime(dt_bar[period_key], "%H:%M:%S")
            self.CntBar[symbol][period_key].openPrice = self.CntBar[symbol]['M01'].openPrice
            self.CntBar[symbol][period_key].highPrice = self.CntBar[symbol]['M01'].highPrice
            self.CntBar[symbol][period_key].lowPrice = self.CntBar[symbol]['M01'].lowPrice
            self.CntBar[symbol][period_key].closePrice = self.CntBar[symbol]['M01'].closePrice
            self.CntBar[symbol][period_key].volume = self.CntBar[symbol]['M01'].volume
            self.CntBar[symbol][period_key].openInterest = self.CntBar[symbol]['M01'].openInterest
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol]['M01'].lastVolume

            if period_key == 'M30':
                self.M30_To_H01(dt_bar, symbol)
                self.M30_To_D01(dt_bar, symbol)


    def M30_To_H01(self, dt_bar, symbol):
        period_key = 'H01'
        # # 先按M30更新，然后判断是否新Bar
        if True:
            self.CntBar[symbol][period_key].volume = self.last_bar[symbol]['M30'].volume
            self.CntBar[symbol][period_key].openInterest = self.last_bar[symbol]['M30'].openInterest
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol][period_key].volume \
                                                         - self.last_bar[symbol][period_key].volume
            self.CntBar[symbol][period_key].highPrice = max(self.CntBar[symbol][period_key].highPrice,
                                                            self.last_bar[symbol]['M30'].highPrice)
            self.CntBar[symbol][period_key].lowPrice = min(self.CntBar[symbol][period_key].lowPrice,
                                                           self.last_bar[symbol]['M30'].lowPrice)
            self.CntBar[symbol][period_key].closePrice = self.last_bar[symbol]['M30'].closePrice

        if (dt_bar[period_key] != self.last_dt_bar[symbol][period_key]):
            # # 推送旧Bar
            self.last_bar[symbol][period_key] = copy.deepcopy(self.CntBar[symbol][period_key])
            # # 不用 判断是否在交易时间内
            if True:
                resp = self.InsertBar(self.last_bar[symbol][period_key])

            print self.last_bar[symbol][period_key]

            self.last_dt_bar[symbol][period_key] = dt_bar[period_key]

            # # 建立新的CntBar[period_key]
            self.CntBar[symbol][period_key].symbol = self.CntBar[symbol]['M30'].symbol
            self.CntBar[symbol][period_key].exchange = self.CntBar[symbol]['M30'].exchange
            self.CntBar[symbol][period_key].period = self.PERIOD[period_key]
            self.CntBar[symbol][period_key].actionDate = dt.datetime.strftime(dt_bar[period_key], "%Y%m%d")
            self.CntBar[symbol][period_key].barTime = dt.datetime.strftime(dt_bar[period_key], "%H:%M:%S")
            self.CntBar[symbol][period_key].openPrice = self.CntBar[symbol]['M30'].openPrice
            self.CntBar[symbol][period_key].highPrice = self.CntBar[symbol]['M30'].highPrice
            self.CntBar[symbol][period_key].lowPrice = self.CntBar[symbol]['M30'].lowPrice
            self.CntBar[symbol][period_key].closePrice = self.CntBar[symbol]['M30'].closePrice
            self.CntBar[symbol][period_key].volume = self.CntBar[symbol]['M30'].volume
            self.CntBar[symbol][period_key].openInterest = self.CntBar[symbol]['M30'].openInterest
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol]['M30'].lastVolume


    def M30_To_D01(self, dt_bar, symbol):
        period_key = 'D01'
        # # 先按M30更新，然后判断是否新Bar
        if True:
            self.CntBar[symbol][period_key].volume = self.last_bar[symbol]['M30'].volume
            self.CntBar[symbol][period_key].openInterest = self.last_bar[symbol]['M30'].openInterest
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol][period_key].volume \
                                                         - self.last_bar[symbol][period_key].volume
            self.CntBar[symbol][period_key].highPrice = max(self.CntBar[symbol][period_key].highPrice,
                                                            self.last_bar[symbol]['M30'].highPrice)
            self.CntBar[symbol][period_key].lowPrice = min(self.CntBar[symbol][period_key].lowPrice,
                                                           self.last_bar[symbol]['M30'].lowPrice)
            self.CntBar[symbol][period_key].closePrice = self.last_bar[symbol]['M30'].closePrice

        if (dt_bar[period_key] != self.last_dt_bar[symbol][period_key])&(dt_bar[period_key].weekday()<5):
            # # 推送旧Bar, 要判断是否属于同一天，周五晚上
            self.last_bar[symbol][period_key] = copy.deepcopy(self.CntBar[symbol][period_key])
            # # 修改日期为最新日期
            self.last_bar[symbol][period_key].actionDate = self.last_bar[symbol]['M30'].actionDate
            if True:
                resp = self.InsertBar(self.last_bar[symbol][period_key])

            print self.last_bar[symbol][period_key]

            self.last_dt_bar[symbol][period_key] = dt_bar[period_key]

            # # 建立新的CntBar[period_key]
            self.CntBar[symbol][period_key].symbol = self.CntBar[symbol]['M30'].symbol
            self.CntBar[symbol][period_key].exchange = self.CntBar[symbol]['M30'].exchange
            self.CntBar[symbol][period_key].period = self.PERIOD[period_key]
            self.CntBar[symbol][period_key].actionDate = dt.datetime.strftime(dt_bar[period_key], "%Y%m%d")
            self.CntBar[symbol][period_key].barTime = dt.datetime.strftime(dt_bar[period_key], "%H:%M:%S")
            self.CntBar[symbol][period_key].openPrice = self.CntBar[symbol]['M30'].openPrice
            self.CntBar[symbol][period_key].highPrice = self.CntBar[symbol]['M30'].highPrice
            self.CntBar[symbol][period_key].lowPrice = self.CntBar[symbol]['M30'].lowPrice
            self.CntBar[symbol][period_key].closePrice = self.CntBar[symbol]['M30'].closePrice
            self.CntBar[symbol][period_key].volume = self.CntBar[symbol]['M30'].volume
            self.CntBar[symbol][period_key].openInterest = self.CntBar[symbol]['M30'].openInterest
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol]['M30'].lastVolume

            self.D01_To_W01(dt_bar, symbol)


    def D01_To_W01(self, dt_bar, symbol):
        period_key = 'W01'
        # # 先按M30更新，然后判断是否新Bar
        if True:
            self.CntBar[symbol][period_key].volume = self.last_bar[symbol]['D01'].volume
            self.CntBar[symbol][period_key].openInterest = self.last_bar[symbol]['D01'].openInterest
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol][period_key].volume \
                                                         - self.last_bar[symbol][period_key].volume
            self.CntBar[symbol][period_key].highPrice = max(self.CntBar[symbol][period_key].highPrice,
                                                            self.last_bar[symbol]['D01'].highPrice)
            self.CntBar[symbol][period_key].lowPrice = min(self.CntBar[symbol][period_key].lowPrice,
                                                           self.last_bar[symbol]['D01'].lowPrice)
            self.CntBar[symbol][period_key].closePrice = self.last_bar[symbol]['D01'].closePrice

        if (dt_bar[period_key] != self.last_dt_bar[symbol][period_key]):
            # # 推送旧Bar
            self.last_bar[symbol][period_key] = copy.deepcopy(self.CntBar[symbol][period_key])
            # # 不用 判断是否在交易时间内
            if True:
                resp = self.InsertBar(self.last_bar[symbol][period_key])

            print self.last_bar[symbol][period_key]

            self.last_dt_bar[symbol][period_key] = dt_bar[period_key]

            # # 建立新的CntBar[period_key]
            self.CntBar[symbol][period_key].symbol = self.CntBar[symbol]['D01'].symbol
            self.CntBar[symbol][period_key].exchange = self.CntBar[symbol]['D01'].exchange
            self.CntBar[symbol][period_key].period = self.PERIOD[period_key]
            self.CntBar[symbol][period_key].actionDate = dt.datetime.strftime(dt_bar[period_key], "%Y%m%d")
            self.CntBar[symbol][period_key].barTime = dt.datetime.strftime(dt_bar[period_key], "%H:%M:%S")
            self.CntBar[symbol][period_key].openPrice = self.CntBar[symbol]['D01'].openPrice
            self.CntBar[symbol][period_key].highPrice = self.CntBar[symbol]['D01'].highPrice
            self.CntBar[symbol][period_key].lowPrice = self.CntBar[symbol]['D01'].lowPrice
            self.CntBar[symbol][period_key].closePrice = self.CntBar[symbol]['D01'].closePrice
            self.CntBar[symbol][period_key].volume = self.CntBar[symbol]['D01'].volume
            self.CntBar[symbol][period_key].openInterest = self.CntBar[symbol]['D01'].openInterest
            self.CntBar[symbol][period_key].lastVolume = self.CntBar[symbol]['D01'].lastVolume


    def CheckTimeInterval(self,symbol,dt_time):
        time_interval_day =   ((dt_time >= SectionDay['S10_beg']) & (dt_time <  SectionDay['S10_end'])) \
                            | ((dt_time >= SectionDay['S20_beg']) & (dt_time <  SectionDay['S20_end'])) \
                            | ((dt_time >= SectionDay['S30_beg']) & (dt_time <  SectionDay['S30_end']))
        SYMBOL = re.findall(r'[a-zA-Z]+',symbol)[0]
        if SYMBOL not in SectionEve.keys():
            SectionEve[SYMBOL] = {}
        if SectionEve[SYMBOL] == {}:
            time_interval_eve = False
        else:
            time_interval_eve = (dt_time >= SectionEve[SYMBOL]['S01_beg']) & (dt_time < SectionEve[SYMBOL]['S01_end'])
            if 'S02_beg' in SectionEve[SYMBOL]:
                #time_interval_eve = time_interval_eve | ((dt_time >= SectionEve[SYMBOL]['S01_beg'])
                #                                         & (SectionEve[SYMBOL] < SectionDay['S01_end']))
                time_interval_eve = time_interval_eve | ((dt_time >= SectionEve[SYMBOL]['S02_beg']) 
                                                         & (dt_time < SectionEve[SYMBOL]['S02_end'])) #modified by bingdian
        time_interval = time_interval_day | time_interval_eve
        return time_interval


if __name__ == '__main__':
    client = DataRecorder_Multi()
    BfRun(client,clientId=client.clientId,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,
          logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)


