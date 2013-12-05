#coding=utf-8
"""
给你一个字符串a,如果其中包含"LOVE"（love不区分大小写)则输出LOVE，否则输出SINGLE。
"""

"""
import pdb
def find_b_in_a(a,b):
	a = a.lower()
	b = b.lower()
	start = 0
	#pdb.set_trace()
	for i in range(0,len(b)):
		start = a.find(b[i],start,len(a))
		if start == -1:
			return False 
		start += 1
	
	return True

a='LOxVE'
b='love'
ret=find_b_in_a(a,b)
print 'LOVE' if ret else 'SINGLE'
"""

a='LOVE'
print 'LOVE' if 'love' in a.lower() else 'SINGLE'
