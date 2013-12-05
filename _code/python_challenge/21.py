#coding=utf-8
"""
给你一个字符串a和一个正整数n,判断a中是否存在长度为n的回文子串。如果存在，则输出YES，否则输出NO。
回文串的定义：记串str逆序之后的字符串是str1，若str=str1,则称str是回文串，如"abcba".
"""

a='cacgyayg'
n=5
def huiwen_substr(a,n):
	for left in range(len(a)-n+1):
		right = left + n -1  
		while left < right:
			if a[left] == a[right]:
				left+=1
				right-=1
			else:
				break
		if left>=right:
			return True
	return False

print 'YES' if huiwen_substr(a,n) else 'NO'
