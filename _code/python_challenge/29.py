#coding=utf-8
"""
给你三个整数a,b,c,  判断能否以它们为三个边长构成三角形。
若能，输出YES，否则输出NO。
"""

a=1
b=2
c=3

print 'YES' if (a+b)>c and (a+c)>b and (b+c)>a else 'NO'
