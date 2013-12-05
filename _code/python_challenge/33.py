#coding=utf-8
"""
给你两个正整数a(0 < a < 100000)和n(0 <= n <=100000000000)，计算(a^n) % 20132013并输出结果
"""

"""
基本思想：(x*y)%z = x%z * y%z
算法：分治   取a相乘直到刚好大于20132013，记录所用a的数量cnt； 然后将n等分为以cnt个a为单位的多份
              
	所有的a	      | a a ... a | a a ... a | …………  | a a ... a  |   a a ...
	每份多少个a    ---cnt---   ---cnt---    ...    ---cnt---   ---n%cnt---
	
	(1)为了防止一份里的a过多，比如a为1，那么多少个a相乘也不能大于20132013，所以给每份a的个数设置一个上限制limit

	(2)如果a本身很大，比如99999，那么每份也就2个a，最后导致递归次数过多，栈溢出
	   所以还需要非递归的方式才可以
	(3)非递归更简单，只是需要注意编码细节，a,n,remain是循环利用的
"""
import pdb

limit = 1000

def digui(a,n):
	#pdb.set_trace()
	if a==0:
		return 0
	ret = 1
	if n >= 1:
		cnt = 0 
		while cnt<limit:
			ret *= a
			cnt+=1
			if ret>=20132013:
				break
		new_a = ret % 20132013
		new_n = int(n/cnt)
		remain = a**(n%cnt) 
		return int(digui(new_a,new_n)*remain)%20132013
	else:
		return 1 

def not_digui(a,n):
	if a==0:
		return 0
	if n == 0:
		return 1
	remain = 1
	
	#pdb.set_trace()
	while n>=1:
		if a == 0:
			return 0
		if a == 1:
			break	
		tmp = 1
		cnt = 0 
		while cnt<limit:
			tmp *= a
			cnt+=1
			if tmp>=20132013:
				break
		remain = ((a**(n%cnt) %20132013) *remain) % 20132013
		a = tmp % 20132013
		n = int(n/cnt)
	
	return remain

a = 20132014 
n = 100000000000 
print digui(a,n)
a = [0,1,2,500,9999,10000,10001,49999,50000,50001,99998,99999,100000]
n = 100000000000 
for i in range(len(a)):
	print not_digui(a[i],n)
	print pow(a[i],n,20132013)
