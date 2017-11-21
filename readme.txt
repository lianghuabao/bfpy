量化宝bftrader lianghuabao BF QQ交流群：571255193，
点击链接加入群【量化宝基于C++CTP架构适合PYTHON和GOLANG编写策略的量化交易中间件】：
https://jq.qq.com/?_wv=1027&k=5KvE0Iz

======

快速上手
======
1. 下载bftrader发布包
下载地址: https://github.com/lianghuabao/lianghuabao/releases
下载地址: http://pan.baidu.com/s/1nvgrNst

2. 安装grpc for python
   2.1 安装python python-2.7.11.msi
   2.2 安装python库,安装包在 python_libs目录下
      2.2.1 pip install six-xxx
      2.2.2 pip install setuptools-xxx
      2.2.3 pip install enum34-xxx
      2.2.4 pip install futures-xxx
      2.2.5 pip install protobuf-xxx
      2.2.6 pip install grpcio-xxx

3. 写策略，调试策略，运行策略
    3.1 运行ctpgateway.exe,datafeed.exe
    3.2 点击ctpgateway的net/netStart,点击datafeed的net/netStart
    3.3 运行datarecorder.py，以连接ctpgateway datafeed
    3.4 点击ctpgateway的ctp/ctpStart
    3.5 可以看到datarecorder.py跑起来啦

    
网友策略列表
======
datarecorder.py：tick收集器，演示BfTraderClient+BfRun的用法
z++/: 1分钟方向策略
xiaoge/: 1分钟动力策略
xiaoge/multi-period: 多周期多品种的数据收集器
oneywang/：1分钟方向策略
bluesky/：1分钟方向策略
bingdian/：1分钟方向策略
laowangcelue/: grpc例子
tao/: 1分钟方向策略
twelvedays/simplepower/:简单震荡策略


（完）
