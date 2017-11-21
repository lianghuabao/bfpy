# coding=utf-8
#creat by Hege
#modified by bingdian: in "_tryconnect"  
import time
import random

from bfgateway_pb2 import *
from bfdatafeed_pb2 import *
from google.protobuf.any_pb2 import *

from grpc.beta import implementations
from grpc.beta import interfaces

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
_TIMEOUT_SECONDS = 1
_CLIENT_ID = "BfTraderClient"
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

class BfTraderClient(object):
    #
    # internal
    #
    def __init__(self):
        print "init BfTraderClient"
        self.gateway_channel = implementations.insecure_channel('localhost', 50051)
        self.gateway = beta_create_BfGatewayService_stub(self.gateway_channel)
        self.datafeed_channel = implementations.insecure_channel('localhost',50052)
        self.datafeed = beta_create_BfDatafeedService_stub(self.datafeed_channel)
        self._connectivity = interfaces.ChannelConnectivity.IDLE

     
        
    def _update(self,connectivity):
        '''C:\projects\grpc\src\python\grpcio\tests\unit\beta\_connectivity_channel_test.py'''
        print connectivity
        self._connectivity = connectivity
        
    def _subscribe(self):
        self.gateway_channel.subscribe(self._update,try_to_connect=True)
    
    def _unsubscribe(self):
        self.gateway_channel.unsubscribe(self._update)
        
    #
    # callback
    #
    def OnStart(self):
        pass
        
    def OnTradeWillBegin(self, response):
        #pass 
        print '==================Trade Will Begin==========\n'
        print response

    def OnGotContracts(self, response):
        pass        
            
    def OnPing(self, response):
        pass        

    def OnTick(self, response):
        pass 
   
    def OnError(self, response):
        print '==================Error==========\n',response.message.encode("GBK")
        #pass        
            
    def OnLog(self, response):
        print '==================Log==========\n',response.when,response.message.encode("GBK")
        #pass        
    
    def OnTrade(self, response):
        #print '===============on Trader===============\n'
        #print response
        pass        
    
    def OnOrder(self, response):
    
        #pass
        print '==============on oder==============\n',response
        print '**tradedVolume:',response.tradedVolume 
    def OnPosition(self, response):
        #pass 
        print response

    def OnAccount(self, response):
        pass        
        
    def OnStop(self):
        print '===================on Stop==============='
        #pass        
        
    #
    #  gateway api
    #
    def SendOrder(self,request):
        response = self.gateway.SendOrder(request,timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
    def CancelOrder(self,request): # 'Cancel' ,not  'Cancle' , Fixed
        response = self.gateway.CancelOrder(request,timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
    def QueryAccount(self):
        response = self.gateway.QueryAccount(BfVoid(),timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
    def QueryPosition(self):
        response = self.gateway.QueryPosition(BfVoid(),timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
    def GwGetContract(self,request):
        responses = self.gateway.GetContract(request,timeout=5*_TIMEOUT_SECONDS,metadata=_MT)
        return responses

    def GwPing(self,request):
        response = self.gateway.Ping(request,timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
    #
    # datafeed api
    #
    
    def InsertContract(self,request):
        response = self.datafeed.InsertContract(request,timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response 
    
    def InsertTick(self,request):
        response = self.datafeed.InsertTick(request,timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
    def InsertBar(self,request):
        response = self.datafeed.InsertBar(request,timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response        

    def DfGetContract(self,request):
        responses = self.datafeed.GetContract(request,timeout=5*_TIMEOUT_SECONDS,metadata=_MT)
        return responses 
    
    def GetTick(self,request):
        response = self.datafeed.GetTick(request,timeout=5*_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
    def GetBar(self,request):
        response = self.datafeed.GetBar(request,timeout=5*_TIMEOUT_SECONDS,metadata=_MT)
        return response 

    def DfPing(self,request):
        response = self.datafeed.Ping(request,timeout=_TIMEOUT_SECONDS,metadata=_MT)
        return response
    
def _dispatchPush(client,resp):
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
    
def _connect(client,clientId,tickHandler,tradeHandler,logHandler,symbol,exchange):
    print "connect gateway"
    req = BfConnectPushReq(clientId=clientId,tickHandler=tickHandler,tradeHandler=tradeHandler,logHandler=logHandler,symbol=symbol,exchange=exchange)
    responses = client.gateway.ConnectPush(req,timeout=_ONE_DAY_IN_SECONDS)
    for resp in responses:
        _dispatchPush(client,resp)            
    print "connect quit"
    
def _disconnect(client):
    print "disconnect gateway"
    req = BfVoid()
    resp = client.gateway.DisconnectPush(req,timeout=_TIMEOUT_SECONDS,metadata=_MT)
    
    
def _tryconnect(client):
    '''subscribe dont tryconnect after server shutdown. so unsubscrible and subscrible again'''
    print "sleep 5s,try reconnect..."
    time.sleep(_TIMEOUT_SECONDS)
    client._unsubscribe()
    time.sleep(_TIMEOUT_SECONDS)
    client._subscribe()            
    time.sleep(_TIMEOUT_SECONDS)
    time.sleep(_TIMEOUT_SECONDS)
    time.sleep(_TIMEOUT_SECONDS)
    client.reconnect=True #by dingdian
    
def BfRun(client,clientId,tickHandler,tradeHandler,logHandler,symbol,exchange):
    print "start BfTraderClient"
    _CLIENT_ID = clientId
    _MT = [("clientid",clientId)]
    client._subscribe()
    firstConnect=True

    try:
        while True:
            if client._connectivity == interfaces.ChannelConnectivity.READY:
                if firstConnect:
                    firstConnect = False
                    client.OnStart()
                _connect(client,clientId,tickHandler,tradeHandler,logHandler,symbol,exchange)
            _tryconnect(client)
    except KeyboardInterrupt:
        print "ctrl+c"        
    
    if client._connectivity == interfaces.ChannelConnectivity.READY:
        client.OnStop()
        _disconnect(client)
    
    print "stop BfTraderClient"
    client._unsubscribe()
    
if __name__ == '__main__':
    client = BfTraderClient()
    BfRun(client,clientId=_CLIENT_ID,tickHandler=True,tradeHandler=True,logHandler=True,symbol="*",exchange="*")
