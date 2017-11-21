# coding=utf-8

import datetime as dt
# re.findall(r'[a-zA-Z]+','rb1610')
# re.findall(r'[0-9]+','rb1610')

# # 日盘
SectionDay = {}
# # 上午
SectionDay['S10_beg'] = dt.time(9, 0, 0)
SectionDay['S10_end'] = dt.time(10, 15, 0)
# # 中午
SectionDay['S20_beg'] = dt.time(10, 30, 0)
SectionDay['S20_end'] = dt.time(11, 30, 0)
# # 下午
SectionDay['S30_beg'] = dt.time(13, 30, 0)
SectionDay['S30_end'] = dt.time(15, 0, 0)

# # 夜盘
SectionEve = {}
# # rb
SectionEve['rb'] = {}
# # 晚上
SectionEve['rb']['S01_beg'] = dt.time(21, 0, 0)
SectionEve['rb']['S01_end'] = dt.time(23, 0, 0)
# # 凌晨
# SectionEve['rb']['S02_beg'] = dt.time(0, 0, 0)
# SectionEve['rb']['S02_end'] = dt.time(2, 30, 0)

# # sr
SectionEve['sr'] = {}
SectionEve['sr']['S01_beg'] = dt.time(21, 0, 0)
SectionEve['sr']['S01_end'] = dt.time(23, 30, 0)
# # i
SectionEve['i'] = {}
SectionEve['i']['S01_beg'] = dt.time(21, 0, 0)
SectionEve['i']['S01_end'] = dt.time(23, 30, 0)

## ag
SectionEve['ag'] = {}
SectionEve['ag']['S01_beg'] = dt.time(21, 0, 0)
SectionEve['ag']['S01_end'] = dt.time.max
SectionEve['ag']['S02_beg'] = dt.time(0, 0, 0)
SectionEve['ag']['S02_end'] = dt.time(2,30,0)
