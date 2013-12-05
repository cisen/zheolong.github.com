#coding=utf-8
"""
给以一个三角形的三边长a,b和c(边长是浮点数),请你判断三角形的形状。
若是锐角三角形，输出R,
若是直角三角形，输出Z，
若是钝角三角形，输出D，
若三边长不能构成三角形，输出W.
"""

a=2
b=3
c=3

l=[a,b,c]
l.sort()
if l[0]+l[1]>l[2]:
	x=l[0]**2
	y=l[1]**2
	z=l[2]**2
	
	if x+y==z:
		print 'Z'
	elif x+y>z:
		print 'R'
	else:
		print 'D'
else:
	print 'W'
