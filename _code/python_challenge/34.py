#coding=utf-8
"""
生活在当代社会，我们要记住很多密码，银行卡，qq，人人，微博，邮箱等等。小P经过一番思索之后，发明了下面这种生成密码方法：
给定两个正整数a和b, 利用a / b我们会到的一个长度无限的小数(若a / b不是无限小数，
比如1/2=0.5,我们认为0.5是0.5000000...，同样将其看做无限长的小数），小P将该小数点后第x位到第y位的数字
当做密码，这样，无论密码有多长，小P只要记住a,b,x,y四个数字就可以了，牢记密码再也不是那么困难的事情了。
现在告诉你a,b,x,y（0 < a,b <= 20132013, 0 < x <= y < 100000000000),请你输出密码。
例如：a = 1, b = 2, x = 1, y = 4, 则 a / b = 0.5000000..., 输出小数点后第1到4位数字，即5000
"""
import pdb
import math

limit = 1000

#先除后乘
def password_1(a,b,x,y):
	#pdb.set_trace()
	t = float(a)/float(b)
	xiaoshu = t - int(t)
	x = x -1
	t = xiaoshu
	s = 6
	while x > s:
		t = t * 10**s
		x = x / s
	t = t * 10**x

	xiaoshu = t - int(t)
	t = xiaoshu
	while y > s:
		t = t * 10**s
		y = y / s
	t = t * 10**y
	
	return t

#先乘后除
def password_2(a,b,x,y):
	#pdb.set_trace()
	ta = a
	x = x -1
	s = 6
	#求a*10^(x-1)
	while x > s:
		ta = ta * 10**s
		a = a - int(float(a)/b) * b
		x = x / s
	t = t * 10**x #t=a*10^(x-1)
	
	t = t - b * int(float(t)/b)

	
	y = y-x
	while y > s:
		t = t * 10**s
		y = y / s
	t = t * 10**y

	t = int(float(t)/b)
	
	return t

#模(通过)
def password_3(a,b,x,y):
	#pdb.set_trace()
	L =[]
	r = a%b
	p = a/b
	
	x = x -1
	s = 16 
	#求a*10^(x-1)
	while x > s:
		a = r * 10 ** s
		r = a % b
		x = x - s 
		y = y - s
		
	a = r * 10 ** x
	r = a % b

	y = y - x

	while y > s:
		a = r * 10 ** s
		elm = str(int(float(a)/b))
		L.append(elm.rjust(s,'0'))
		r = a % b
		y = y - s 
	a = r * 10 ** y
	elm = str(int(float(a)/b))
	L.append(elm.rjust(y,'0'))
	r = a % b

	return L 

#a = 1 
#b = 2
#x = 1
#y = 4
#
#print "%d" % password_2(a,b,x,y)
#
#a = 20132013 
#b = 8
#x = 1
#y = 1000000000
#
#print "%d" % password_2(a,b,x,y)

a = 1
b = 19 
x = 1
y = 10000000000000
L = password_3(a,b,x,y)
c = 0
for i in L:
	c += len(i)
print c==y-x+1
print ''.join(L) 
