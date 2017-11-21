# coding=utf-8
# -*- coding: utf-8 -*-
#creat by Bingdian(QQ:251859269)
import sys
sys.path.append("..")
import datetime
import random
import numpy as np
import pandas as pd
from sdk.bfdatafeed_pb2 import *
from google.protobuf.any_pb2 import *

from grpc.beta import implementations
from grpc.beta import interfaces

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
_TIMEOUT_SECONDS = 1

class bfHistoryData(object):
    
   
   #----------------------------------------------------------------------
   #功能:取得tickNum个Tick,并转换成period的bar
   #----------------------------------------------------------------------
    @classmethod 
    def getTick2BarLast(cls,client,tickNum,period,toDate="20991231",toTime="00:00:00"):
        
        req = BfGetTickReq(symbol=client.symbol,exchange=client.exchange,toDate=toDate,toTime=toTime,count=tickNum)
        responses = client.datafeed.GetTick(req,timeout=_ONE_DAY_IN_SECONDS,metadata=client.clientMT)
        tickList=[(resp.actionDate+' '+resp.tickTime,resp.lastPrice,resp.lastVolume) for resp in responses]
        tickdataType=np.dtype({'names':['time','price','volume'],'formats':['S68','f','i']}) #datetime64[ns]
        tickNp=np.array(tickList,dtype=tickdataType)
        ts_index=pd.to_datetime(tickNp['time'])
        ts_price=pd.Series(tickNp['price'],name='price',index=ts_index)
        ts_volume=pd.Series(tickNp['volume'],name='volume',index=ts_index)
        bar_ohlc=ts_price.resample(period['TALIB_NAME']).ohlc()
        bar_volume=ts_volume.resample(period['TALIB_NAME']).sum()
        bar=pd.concat([bar_ohlc,bar_volume],axis=1)
        bar.dropna(how='any',inplace=True)
        return bar
   #----------------------------------------------------------------------
   #功能:取得从start到end时间内的Tick,并转换成period的bar
   #ToDo:datefeed增加获取tick方向后,简化
   #----------------------------------------------------------------------
    @classmethod 
    def getTick2BarFrmTo(cls,client,start,end,period):
        
        delta=end-start
        seconds=delta.total_seconds()
        tickNum=int(seconds*period['ticksOfSecond'])##abs:7x24服务器传过来的tick时间倒流
        step=period['secondsOfPeriod']*period['ticksOfSecond'] #每次取得用于生成bar的tick数
        temp_bar=pd.DataFrame()
        temp_datetime=end
        temp_deltime=datetime.timedelta(microseconds=1000)
        for i in range(step,tickNum+step,step):
            temp_date=temp_datetime.strftime('%Y%m%d')
            temp_time=temp_datetime.strftime('%H:%M:%S.%f')[:-3] #去除字符串后三位 保留到小数点后3位
            bar1=cls.getTick2BarLast(client,step+10,period,toDate=temp_date,toTime=temp_time) #每次返回 1.5个bar
            temp_bar=pd.concat([bar1[1:],temp_bar])#bar1[0]为不完整的bar,丢掉. temp_bar中 为完整的历史bar+当前bar
            if start in temp_bar.index:
                temp_bar=temp_bar[start:] #结束
                break
            temp_datetime=temp_bar.index[0]-temp_deltime
                     
        return temp_bar  
   #----------------------------------------------------------------------
   #功能:查询datafeed, 返回bar
   #
   #----------------------------------------------------------------------
    @classmethod 
    def getBarData(cls,client,count,period,toDate="20991231",toTime="00:00:00"):
        print 'count:',count , 'periond:',period['bfPeriod'],client.symbol
        req = BfGetBarReq(symbol=client.symbol,exchange=client.exchange,period=period['bfPeriod'],toDate=toDate,toTime=toTime,count=count)
        responses = client.datafeed.GetBar(req,timeout=_ONE_DAY_IN_SECONDS,metadata=client.clientMT)
        barList=[[resp.actionDate+' '+resp.barTime,resp.openPrice,resp.highPrice,resp.lowPrice,resp.closePrice,resp.volume] \
                    for resp in responses]
        barNp=np.array(barList)
        print barNp.shape
        bar=pd.DataFrame(barNp[::-1,1:],columns=['open','high','low','close','volume'],dtype=float,index=pd.to_datetime(barNp[::-1,0]))
        return bar          
       