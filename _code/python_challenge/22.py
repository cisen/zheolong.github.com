#coding=utf-8
"""
给你两个时间st和et(00:00:00<=st <= et<=23:59:59), 请你给出这两个时间间隔的秒数。
如：st="00:00:00", et="00:00:10", 则输出10.
"""
import string
st = "00:01:00"
et = "00:01:10"

"""
st_n1 = string.atoi(st[0:2]) 
st_n2 = string.atoi(st[3:5]) 
st_n3 = string.atoi(st[6:8]) 
et_n1 = string.atoi(et[0:2]) 
et_n2 = string.atoi(et[3:5]) 
et_n3 = string.atoi(et[6:8]) 
print ((((et_n1-st_n1)*60) + et_n2 - st_n2) * 60 + et_n3 - st_n3)
"""
# 上面的分割方法也可以，不过这个题用split更简单

st1,st2,st3 = st.split(":")
et1,et2,et3 = et.split(":")
print (int(et3)-int(st3)) + (int(et2)-int(st2))*60 + (int(et1)-int(st1))*60**2
