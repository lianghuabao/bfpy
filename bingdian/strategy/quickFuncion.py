# coding=utf-8
#creat by Bingdian(QQ:251859269)
def cross(ma1,ma2):
    if ma1[1]<ma2[1] and ma1[2]>ma2[2] or \
       ma1[0]<ma2[0] and ma1[1]==ma2[1] and ma1[2]>ma2[2]:#处理恰好 相等
       return True
    else:
       return False