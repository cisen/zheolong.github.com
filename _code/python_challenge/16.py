#coding=utf-8
"""
银行在打印票据的时候，常常需要将阿拉伯数字表示的人民币金额转换为大写表示，现在请你来完成这样一个程序。
在中文大写方式中，0到10以及100、1000、10000被依次表示为：
    零壹贰叁肆伍陆柒捌玖拾佰仟万
以下的例子示范了阿拉伯数字到人民币大写的转换规则：

1	壹圆
11	壹拾壹圆
111	壹佰壹拾壹圆
101	壹佰零壹圆
-1000	负壹仟圆
1234567	壹佰贰拾叁万肆仟伍佰陆拾柒圆

现在给你一个整数a(|a|<100000000), 打印出人民币大写表示
"""

import pdb
def number2chinese(a):
	s = []
	n = 0 # 位数
	c = 0 # 第几次非0
	flag = False #上次是不是加入'零'了
	flag_neg = False if a>=0 else True
	digit2ch = ('零','壹','贰','叁','肆','伍','陆','柒','捌','玖')
	weight2ch = ('圆','拾','佰','仟','万')
	#pdb.set_trace()
	a=abs(a)
	s.append(weight2ch[0])
	while a:
		b = a%10
		if b != 0:
			while n >= 4:
				s.append(weight2ch[4])
				n-=4
			if n!=0:
				s.append(weight2ch[n])
			s.append(digit2ch[b])
			flag = False
			c+=1
		else:
			if not flag and c != 0:
				s.append(digit2ch[0])
				flag = True

		a/=10
		n+=1

	if c == 0:
		#s.append(weight2ch[0])
		s.append(digit2ch[0])

	if flag_neg and c!=0:
		s.append('负')
	
	return s

print ''.join(number2chinese(0)[::-1])
print ''.join(number2chinese(10)[::-1])
print ''.join(number2chinese(100)[::-1])
print ''.join(number2chinese(1000)[::-1])
print ''.join(number2chinese(10000)[::-1])
print ''.join(number2chinese(100000)[::-1])
print ''.join(number2chinese(1000000)[::-1])
print ''.join(number2chinese(10000000)[::-1])
print ''.join(number2chinese(1)[::-1])
print ''.join(number2chinese(11)[::-1])
print ''.join(number2chinese(101)[::-1])
print ''.join(number2chinese(1010)[::-1])
print ''.join(number2chinese(10100)[::-1])
print ''.join(number2chinese(100100)[::-1])
print ''.join(number2chinese(1001000)[::-1])
print ''.join(number2chinese(11000000)[::-1])
print ''.join(number2chinese(-0)[::-1])
print ''.join(number2chinese(-11)[::-1])
print ''.join(number2chinese(-101)[::-1])
print ''.join(number2chinese(-1010)[::-1])
print ''.join(number2chinese(-10100)[::-1])
print ''.join(number2chinese(-100100)[::-1])
print ''.join(number2chinese(-1001000)[::-1])
print ''.join(number2chinese(-11000000)[::-1])
