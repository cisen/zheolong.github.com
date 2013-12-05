# This Python file uses the following encoding: utf-8
"""
给你一个list L, 如 L=[2,8,3,50], 对L进行升序排序并输出,
如样例L的结果为[2,3,8,50]
"""

def rank_list(L):
	for i in range(len(L)):
		for j in range(len(L)-1,i-1,-1):
			if(L[j]<L[j-1]):
				L[j],L[j-1] = L[j-1],L[j]
	return L
L=[2,8,3,50]
print rank_list(L)
