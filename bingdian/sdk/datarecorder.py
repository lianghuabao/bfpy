# coding=utf-8

from bftraderclient import BfTraderClient,BfRun
from bfgateway_pb2 import *
from bfdatafeed_pb2 import *

class DataRecorder(BfTraderClient):
    def __init__(self):
        BfTraderClient.__init__(self)
        self.clientId = "DataRecorder"
        self.tickHandler = True
        self.tradeHandler = False
        self.logHandler = False
        self.symbol = "*"
        self.exchange = "*"
        
    def OnStart(self):
        print "OnStart"
        
    def OnTradeWillBegin(self, response):
        print "OnTradeWillBegin"
        print response        

    def OnGotContracts(self, response):
        print "OnGotContracts"
        print response
        
        #
        # save contract
        #
        req = BfGetContractReq(symbol="*",exchange="*")
        resps = self.GwGetContract(req)
        for resp in resps:
            print resp
            self.InsertContract(resp)
            
    def OnPing(self, response):
        print "OnPing"
        print response

    def OnTick(self, response):
        #print "OnTick"
        #print response
        
        #
        # save tick
        #
        resp = self.InsertTick(response)
        
    def OnError(self, response):
        print "OnError"
        print response
            
    def OnLog(self, response):
        print "OnLog"
        print response
    
    def OnTrade(self, response):
        print "OnTrade"
        print response
    
    def OnOrder(self, response):
        print "OnOrder"
        print response
            
    def OnPosition(self, response):
        print "OnPosition"
        print response

    def OnAccount(self, response):
        print "OnAccount"
        print response
        
    def OnStop(self):
        print "OnStop"

if __name__ == '__main__':
    client = DataRecorder()
    BfRun(client,clientId=client.clientId,tickHandler=client.tickHandler,tradeHandler=client.tradeHandler,logHandler=client.logHandler,symbol=client.symbol,exchange=client.exchange)
