#coding=utf-8
"""
给你两个正整数a,b,  输出它们公约数的个数。
"""

import pdb
def comDivNum(a,b):
	if a==0 or b==0:
		return -1
	c = 1
	m = min(a,b)
	for i in range(2,m+1):
		if a%i==0 and b%i==0:
			c+=1
	return c

print comDivNum(0,2)
print comDivNum(1,0)
print comDivNum(1,2)
print comDivNum(2,2)
print comDivNum(4,8)
	
