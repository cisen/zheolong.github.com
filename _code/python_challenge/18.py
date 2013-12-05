#coding=utf-8
"""
我们经常遇到的问题是给你两个数，要你求最大公约数和最小公倍数。
今天我们反其道而行之，给你两个数a和b，计算出它们分别是哪两个数的最大公约数和最小公倍数。
输出这两个数，小的在前，大的在后，以空格隔开。若有多组解，输出它们之和最小的那组。
"""

import pdb
import math 
def xy(a,b):
	if a==0 or b==0:
		return -1
	# xa = x/a  ,  ya = y/a,   ba=b/a
	ba=b/a
	for xa in range(int(math.sqrt(ba)),0,-1):
		if ba%xa==0:
			break
	return xa*a,ba/xa*a
a=2
b=4
x,y=xy(a,b)
print("%d %d" % (x,y)) 
	
