#coding=utf-8
"""
给你两个整数a和b（-10000<a,b<10000），请你判断是否存在两个整数，他们的和为a，乘积为b。
若存在，输出Yes,否则输出No
例如：a=9,b=15, 此时不存在两个整数满足上述条件，所以应该输出No。
"""
import pdb
import sys
import math

"""
这两个数是x^2+a*x+b=0的两个解
"""
a = 4
b = 4
tmp = a**2-4*b
if tmp<0:
	print 'No'
else:
	tmp = math.sqrt(float(tmp))
	x = (-a + tmp)/2.0 
	if x==int(x):
		print 'Yes'
	else:
		print 'No'
