# This Python file uses the following encoding: utf-8
"""
输出100以内的所有素数，素数之间以一个空格区分
"""
import math
def isPrime(n):
	if n <= 1:
		return False
	if n == 2:
		return True
	for j in range(2,int(math.sqrt(n))+1):
		if(n%j==0):
		    return False
	return True

ret = []
for i in range(2,100):
	if isPrime(i):
		ret.append(str(i))
print ' '.join(ret)
