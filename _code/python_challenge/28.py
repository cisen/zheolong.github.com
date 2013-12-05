#coding=utf-8
"""
给你一个整数列表L,判断L中是否存在相同的数字，
若存在，输出YES，否则输出NO。
"""

L = [1,2,2,3]
#print 'NO' if list(set(L))==L else 'YES'
print 'NO' if len(set(L))==len(L) else 'YES'
