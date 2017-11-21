作者：oneywang,2016.6.13
1.更新支持BfTraderClient
2.后续不再维护，改用golang

2016.6.8
1.针对品种rb1610
2.savebar.py用于收集tick与1分钟bar并保存到datafeed
3.dualcross_1min.py
1)初始时会去取一下仓位并保存
2)OnTick时会尝试到datafeed取最近的60个分钟bar
3)OnBar只有在积累到60个bar以上时，才会真正开始策略判断
4)结束时会取消pending的orders
