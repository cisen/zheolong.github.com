#coding=utf-8
"""
给你一个整数组成的列表L，按照下列条件输出：
若L是升序排列的,则输出"UP";
若L是降序排列的,则输出"DOWN";
若L无序，则输出"WRONG"。
"""

def xulie(L):
	if len(L)<=1:
		return 'UP'
	f = 'NONE'
	for i in range(1,len(L)): 
		if L[i]>L[i-1]:
			if f=='NONE':
				f = 'UP'
			elif f=='DOWN':
				return 'WRONG'
		elif L[i]<L[i-1]:
			if f=='NONE':
				f = 'DOWN'
			elif f=='UP':
				return 'WRONG'
	
	if f == 'NONE':
		return 'UP'
	return f

L=[1,1,0,0]
print xulie(L)
			 
