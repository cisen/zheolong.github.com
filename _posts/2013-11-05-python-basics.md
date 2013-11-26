---
layout: post
title: "Python basics"
description: ""
category: Python 
tags: [Python]
---
{% include JB/setup %}

* toc
{:toc}

## 数据类型 ##

Integer、Float、Boolean、String，但是不需要显示声明

## 赋值语句 ##

{% highlight python %}
variable_int_name = 5
variable_float_name = 5.0
variable_bool_name = True
{% endhighlight %}

## 缩进 空行 ##

语句之间空行，语句中缩进四个空格

## 注释 ##
single line:例子 `# 单行注释`

multi-line:例子 `""" 多行注释 """`

## 数学运算 ##

`+` `-` `*` `/` `%`

Exponentiation(`**`)

## 输入 ##

{% highlight python %}
name = raw_input("My name is:")
{% endhighlight %}

## 输出 ##

{% highlight python %}
total = 1.0
# 带格式
print("%.2f" % total)

print("%.2f %.2f" % (total,total))

# 不带格式
print total
{% endhighlight %}

## 字符串类型 ##

1. 用`''`或`""`包围，特殊字符用`\`转义
2. 访问字符串中某个字符`Fifth_letter = "MONTY"[4]`
3. 有关字符串的函数（注意：中间两个是特定于字符串的，所以使用方式与其他不同）

   `len() ` e.g.`len(string)`
   
   `lower()` e.g.`string.lower()`
   
   `upper()` e.g.`string.upper()`
   
   `str()` e.g.`str(non-string)`
   
4. concatenation：
   `"dest" + "src"`

5.
{% highlight python %}
# 访问
for letter in 'word':
    print letter

{% endhighlight %}

## 时间 ##

{% highlight python%}
from datetime import datetime
now = datetime.now()
print now
print now.month  #int类型
print now.day    #int类型
print now.year   #int类型

#输出：
2013-11-05 13:10:07.870952
11
6
2013
{% endhighlight %}

## 逻辑运算 ##
例子：
{% highlight python%}
# `and` `or` `not`
True and True
True or True
not True
{% endhighlight %}

## 分支 ##
{% highlight python%}
def greater_less_equal_5(answer):
	if answer > 5:
		return 1
	elif answer < 5:
		return -1
	else:
		return 0
{% endhighlight %}

## 函数 ##
{% highlight python %}
# 单个形参
def spam(n):
	eggs = n**2
	return eggs

print spam(10)

# 多个形参
def spam(*args):
	print args

spam("a","b","c")

{% endhighlight %}

## 库函数 ##

### 引入和使用方式 ###

{% highlight python %}
import math

print math.sqrt(2)
{% endhighlight %}

{% highlight python %}
from math import sqrt

print sqrt(2)
{% endhighlight %}

{% highlight python %}
# 尽量不要使用该方式
from math import *

print sqrt(2)
{% endhighlight %}

{% highlight python %}
import math
everything = dir(math) #Sets everything to a list of things from math
from math
print everything
{% endhighlight %}

### 内置的（不需要import，例如前面使用的操作字符串的） ###
{% highlight python %}
# 关于数值
def biggest_number(*args):
	return max(args)
def smallest_number(*args):
	return min(args)
def distance_from_zero(arg):
	return abs(arg)

biggest_number(-10, -5, 5, 10)
smallest_number(-10, -5, 5, 10)
distance_from_zero(-10)

# 返回类型
print type(1)
print type(1.0)
print type("1")
print type({'Name':'QJL'})
print type((1,2))

"""
<type 'int'>
<type 'float'>
<type 'str'>
<type 'dict'>
<type 'tuple'>
"""

# 判断类型
type(1) == int
type(1.0) == float
{% endhighlight %}

## List ##
{% highlight python %}
list = ['a','b','c']
list[0]
list[1]
list[2]
list[0:2]
list[:2]
list[2:]
list.insert(list.index('a'),'x') # 求'a'的索引并在此位置插入'x'
# 插入
list.append('d')
list.append(['x']*5) # 5 times
# 遍历
for number in list:
    # Your code here
	print number**2
for i in range(0, len(list)):
    print list[i]
print range(2)
print range(0,2)
print range(0,4,2)
# 排序
list.sort()
# 删除
list.remove('d') # find 'd' and remove it
list.pop(0) # remove the item at index 0 and return it
del(list[0]) # remove the item at index 0 but won't return it
{% endhighlight %}

## Dictionary ##
{% highlight python %}
map = {'key1' : 1, 'key2' : 2, 'key3' : 3}

# 访问
for key in map:
    print map[key]
# 插入
map['key4'] = 4
# 删除
del map['key4']
{% endhighlight %}
