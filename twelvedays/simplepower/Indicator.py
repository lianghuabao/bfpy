# coding=utf-8

def averageF(n,capcity=10):
    class acc:
        def __init__ (self):
            self.price=[]
            self.ma=[]
        def calc(self,p):
            if len(self.price)>2*n:
                self.price=self.price[-n:]            
            self.price.append(p)
            if len(self.price)<n:
                self.ma.append((sum(self.price)+(n-len(self.price))*self.price[0])*1.0/n)
            else:
                self.ma.append(sum(self.price[-n:])*1.0/n)
                
            if len(self.ma)>2*capcity:
                self.ma=self.ma[-capcity:]     
            return self.ma
        
    return acc().calc
    

def xAverageF(n,capcity=10):
    class acc:
        def __init__ (self):
            self.lastEma=None
        def calc(self,price):
            factor=2.0/(n+1)
            if self.lastEma==None:
                self.lastEma=[price]
            else:
                self.lastEma.append(self.lastEma[-1]+factor*(price-self.lastEma[-1]))
                
            if len(self.lastEma)>2*capcity:
                self.lastEma=self.lastEma[-capcity:]
            return self.lastEma
    return acc().calc
                

def macdF(fast,slow,n,capcity=10):
    class acc:
        def __init__ (self):
            self.emaf=xAverageF(fast)
            self.emaS=xAverageF(slow)
            self.emaN=xAverageF(n)
            self.macdValue=[]
            self.avgMacd=[]
            self.macdDiff=[]
            
        def calc(self,price):
            self.macdValue.append(self.emaf(price)[-1]-self.emaS(price)[-1])
            self.avgMacd.append(self.emaN(self.macdValue[-1])[-1])
            self.macdDiff.append(self.macdValue[-1]-self.avgMacd[-1])
            
            if len(self.macdValue)>2*capcity:
                self.macdValue=self.macdValue[-capcity:]  
            if len(self.avgMacd)>2*capcity:
                self.avgMacd=self.avgMacd[-capcity:]  
            if len(self.macdDiff)>2*capcity:
                self.macdDiff=self.macdDiff[-capcity:]    
                
            return (self.macdValue,self.avgMacd,self.macdDiff)
        
    return acc().calc
    



    
  