#coding=utf-8
"""
给你一个整数list L, 如 L=[2,-3,3,50], 求L的一个连续子序列，使其和最大，输出最大子序列的和。
例如，对于L=[2,-3,3,50]， 输出53（分析：很明显，该列表最大连续子序列为[3,50]).
"""
import pdb
import sys
import math

def maxLianXuSubSeq(L):
	if len(L)<=0:
		return []
	pre_max = -sys.maxint 
	total_max = pre_max 
	for i in range(0,len(L)):
		pre_max = max(L[i],pre_max+L[i])
		total_max = max(pre_max,total_max)
		
	return total_max 

L=[-1,-3,-3,-50]
print maxLianXuSubSeq(L)
