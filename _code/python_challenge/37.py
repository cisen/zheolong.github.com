#coding=utf-8
"""
给你直角三角形的两个直角边的边长a,b,请你求出其斜边边长，结果保留小数点后三位小数。
如a=3, b =4, 则输出5.000。
"""
import pdb
import sys
import math

a=3
b=4

print "%.3f" % math.sqrt(float(a**2+b**2))

