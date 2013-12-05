# This Python file uses the following encoding: utf-8
"""
给你一字典a，如a={1:1,2:2,3:3}，输出字典a的key，以','链接，如‘1,2,3'。
"""

a={1:1,2:2,3:3}
d=[]
for i in a.keys():
	d.append(str(i))
print ','.join(d)
