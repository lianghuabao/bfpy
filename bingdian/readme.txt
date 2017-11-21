


升级至20160613版SDK


Key Features

1.处理实盘网关tick为0的数据
2.策略开发:分离为单独的模块,开发时值只需要考虑策略怎么运行
3.周期bar,通过改为使用都周期数据 
4.内置周期转换函数，支持tick转换成任意周期bar数据
5.client中断重连:自动同步仓位,补全数据 
6.交易时机:支持tick, bar开盘 收盘
7.下单函数:开/平/反手,已处理上期所平今昨问题
8.支持上交所平仓拆分今昨
9.支持可用仓位计算
9.指标计算:talib样例
10.定单管理:支持时长和价差两种条件自动撤单, 支持连续追单
11.支持 多种策略应用于相同的合约,互相隔离,仓位/订单互不影响
12.支持bfPeriod各周期交易



文件说明：

SDK----------------------bfpy SDK库 ，修改bftraderclient.py 中 _tryconnect,增加client.reconnect 变量
Template-----------------策略基库母板
DataRecoderMulti---------xiaoge的多周期数据入库程序（支持夜盘跨00:00:00）
tablib均线交叉.py--------多策略隔离样例
tablib_macd.py-----------talib指标模板

by Bingdian