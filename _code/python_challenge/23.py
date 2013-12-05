#coding=utf-8
"""
一年有多少天，这是个大问题，很值得思考。现在给你一个年份year(year为四位数字的字符串，如"2008","0012"),你输出这一年的天数。如year="2013", 则输出365。
"""
import string
year = '4000'
year = string.atoi(year) 
print '366' if year%400==0 or year%100!=0 and year%4==0 else '365'
