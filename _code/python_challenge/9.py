# This Python file uses the following encoding: utf-8
"""
给你两个正整数a和b， 输出它们的最大公约数。
"""
def gcd(a,b):
	if a <= 0 or b <= 0:
		return -1
	if a<b:
		a,b=b,a
	while b != 0:
		a,b = b,a%b
	return a

a=1
b=8
print gcd(a,b) 
