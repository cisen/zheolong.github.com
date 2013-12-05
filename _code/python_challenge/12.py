# This Python file uses the following encoding: utf-8
"""
给你一个正整数列表 L, 如 L=[2,8,3,50], 判断列表内所有数字乘积的最后一个非零数字的奇偶性,
奇数输出1,偶数输出0. 如样例输出应为0
"""
def count25(n):
	a,b=0,0
	while n>=2:
		if n%2==0:
			n=n/2
			a+=1
		else:
			break
	while n>=5:
		if n%5==0:
			n=n/5
			b+=1
		else:
			break
	
	return a,b

L=[2,8,3,50]
i2=0
i5=0
for i in L:
	a,b=count25(i)	 
	i2+=a 
	i5+=b 
if i2>i5:
	print 0
else:
	print 1
