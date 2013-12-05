# This Python file uses the following encoding: utf-8
"""
已知矩形长a,宽b,输出其面积和周长，面积和周长以一个空格隔开
"""
def perimeter(a,b):
	if a < 0 or b < 0:
	    return -1	
	return 2*(a+b) 

def area(a,b):
	if a < 0 or b < 0:
	    return -1	
	return a*b 

a=2
b=3
print area(a,b),perimeter(a,b) 
