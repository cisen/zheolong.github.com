# This Python file uses the following encoding: utf-8
"""
给你一个正整数列表 L, 如 L=[2,8,3,50], 输出L内所有数字的乘积末尾0的个数,...
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
print min(i2,i5)
