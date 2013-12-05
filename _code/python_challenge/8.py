# This Python file uses the following encoding: utf-8
"""
给你一个list L, 如 L=[0,1,2,3,4], 输出L的中位数（若结果为小数，则保留一位小数）。
"""
def mid(L):
	n = len(L)
	L.sort()
	if n%2==0:
		return float(L[n/2]+L[n/2-1])/2
	else:
		return L[n/2]
L = [0,1,2,3,4]
print mid(L) 
