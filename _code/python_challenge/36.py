#coding=utf-8
"""
给你一个整数list L, 如 L=[2,-3,3,50], 求L的一个非连续子序列，使其和最大，输出最大子序列的和。
这里非连续子序列的定义是，子序列中任意相邻的两个数在原序列里都不相邻。
例如，对于L=[2,-3,3,50]， 输出52（分析：很明显，该列表最大非连续子序列为[2,50]).
"""
import pdb
import sys
import math

def maxFeiLianXuSubSeq(L):
	#pdb.set_trace()
	if len(L)<=0:
		return 0 

	L2 = []
	for i in range(len(L)+2):
		L2.append(-sys.maxint)

	max_total = -sys.maxint

	for i in range(0,len(L)):
		tmp = max(L2[0:i+1:])
		tmp = max(tmp,L[i])
		for j in range(0,i+1):
			tmp = max(tmp, L2[j]+L[i])
		L2[i+2] = tmp 
		max_total = max(L2[i+2],max_total)
	return max_total
		

L=[2,-3,3,50]
print maxFeiLianXuSubSeq(L)
