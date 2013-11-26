---
layout: post
title: "shell programming: grammar"
description: ""
category: Shell 
tags: []
---
{% include JB/setup %}

* toc
{:toc}

## IF ##

**if_elif_else**

{% highlight bash %}
#!/bin/bash
echo -n "word 1:"
read word1
echo -n "word 2:"
read word2
echo -n "word 3:"
read word3

if [ "$word1" = "$word2" -a "$word2" = "$word3" ]
	then 
		echo "Match:word1,2,&3"
	elif	[ "$word1" = "$word2" ]
	then 
		echo "Match:word1,&2"
	elif	[ "$word2" = "$word3" ]
	then 
		echo "Match:word2,&3"
	elif	[ "$word1" = "$word3" ]
	then 
		echo "Match:word1,&3"
	else
		echo " No Match "
fi
{% endhighlight %}

**if_else**

{% highlight bash %}
#!/bin/bash
if [ $# -eq 0 ]
	then 
		echo "Usage: out [-v] filenames..." 1>&2
		exit 1
fi

if [ "$1" = "-v" ]
	then 
		shift
		less -- "$@"
	else
		cat -- "$@"
fi
{% endhighlight %}

**Inks**
{% highlight bash %}
#!/bin/bash
#Indentify links to a file
#Usage: lnks file [directory]

if [ $# -eq 0 -o $# -gt 2 ]; then 
	echo "Usage: lnks file [directory]" 1>&2
	exit 1
fi 

if [ -d "$1" ]; then 
	echo "First argument connot be a directory." 1>&2
	echo "Usage: lnks file [directory]" 1>&2
	exit 1
else
	file="$1"
fi

if [ $# -eq 1 ]; then 
	dir="."
	elif [ -d "$2" ]; then
		dir="$2"
	else
		echo "Optional second argument must be a directory." 1>&2
		echo "Usage: lnks file [directory]" 1>&2
		exit 1
fi

#Check that file exists and is an ordinary file:
if [ ! -f "$file" ]; then
	echo "lnks: $file not found or is special file" 1>&2
	exit 1
fi

#Check link count on file
set -- $(ls -l "$file")
linkcnt=$2
if [ "$linkcnt" -eq 1 ]; then 
	echo "lnks: No other hard links to $file" 1>&2
	exit 0
fi

#Get the inode of the given file
set $(ls -i "$file")
inode=$1

#Find and print the files with that inode number
echo "lnks: using find to search for links..." 1>&2
find "$dir" -xdev -inum $inode -print

{% endhighlight %}




## FOR ##


**for**
{% highlight bash %}
#!/bin/bash
for arg   #与for arg in "$@"同义 
do
	echo "$arg"
done
{% endhighlight %}

**for_in**
{% highlight bash %}
#!/bin/bash
echo "------EXAMPLE 1------"
for fruit in apples bananas oranges pears
do 
	echo $fruit
done
echo "Done"

echo "------EXAMPLE 2 Show Dirs------"
for file in * #对于当前目录下所有文件和目录
do
	if [ -d $file ]; then #如果$file是目录就输出
		echo $file
	fi
done
{% endhighlight %}

**whos**
{% highlight bash %}
#!/bin/bash

if [ $# -eq 0 ]; then
	echo "Usage: whos id..." 1>&2
	exit 1
fi

for id
do
	#gawk从/etc/passwd中提取第1个和第5个字段，可通过man gawk查看其用法
	gawk -F: '{print $1,$5}' /etc/passwd | grep -i "$id"
done
{% endhighlight %}

## WHILE ##

**while**
{% highlight bash %}
#!/bin/bash
number=0
while [ "$number" -lt 10 ]
do
	echo -n "$number"
	((number += 1))
done 
echo
{% endhighlight %}

## UNTIL ##

**example 1**
{% highlight bash %}
#!/bin/bash
#until的一个简单实例，猜名字
secretname=qjl
name=noname
echo "Try to guess the secret name"
echo
until [ $name = $secretname ]
do
	echo -n "Your guess:"
	read name
done
echo " Bingo! "
{% endhighlight %}

**example 2**
{% highlight bash %}
#!/bin/bash
#UNIX/WORLD, III:4
#锁定终端，直到输入正确的口令

trap '' 1 2 3 18
stty -echo  #防止显示键盘输入的字符
echo -n "Key:"
read key_1
echo
echo -n "Again:"
read key_2
echo
key_3=
if [ "$key_1" = "$key_2" ]; then
	tput clear	#清屏
	until [ "$key_3" = "$key_2" ]
	do
		read key_3
	done
else
	echo "locktty:keys do not match" 1>&2
fi
stty echo
{% endhighlight %}

## CASE ##

**case**
{% highlight bash %}
#!/bin/bash
echo -n "Enter A,B,or C:"
read letter
case "$letter" in
	a|A)
		echo "You entered A"
		;;
	b|B)
		echo "You entered B"
		;;
	c|C)
		echo "You entered C"
		;;
	[1234567890])
		echo "You entered a single number"
		;;
	?)
		echo "You entered a single letter or number"
		;;
	*)	
		echo "You did not entered a single letter or number"
		;;
esac
{% endhighlight %}

**case menu**
{% highlight bash %}
#!/bin/bash
#menu interface to simple commands

echo -e "\n  COMMAND MENU\n" #-e选项使得echo将\n解释为换行，而不是两个普通字符 
echo "  a. Current data and time"
echo "  b. Users currently logged in"
echo "  c. Name of the working directory"
echo -e "  d. Contents of the working directory\n"
echo -n "Enter a, b, c, or d:"
read answer
echo

#
case "$answer" in
	a)
		date
		;;
	b)	
		who
		;;
	c)
		pwd
		;;
	d)	
		ls
		;;
	*)
		echo "There is no selection:$answer"
		;;
esac
{% endhighlight %}


**safedit**
{% highlight bash %}
#!/bin/bash
PATH=/bin:/usr/bin #设置PATH是为了保证脚本中调用的是系统目录中的标准工具，而不是用户自己的，以免引起混淆
script=$(basename $0) #储存脚本被调用时的命令，脚本被改名后具有自适应性
echo $0
case $# in
	0)
		vim
		exit 0
		;;
	1)
		if [ ! -f "$1" ]; then  #-f表示文件存在而且是普通文件
			vim "$1"
			exit 0
		fi
		if [ ! -r "$1" -o ! -w "$1" ]; then #-r和-w表示文件可读和可写
			echo "$script: check permissions on $1" 1>&2
			exit 1
		else
			editfile=$1
		fi
		if [ ! -w "." ]; then	#检查工作目录的写权限
			echo "$script: backup cannot be created in the working directory" 1>&2
			exit 1
		fi
		;;
	*)
		echo "Usage: $script [file-to-edit]" 1>&2
		exit 1
		;;
esac

tempfile=/tmp/$$.$script  #以shell进程的PID号+脚本名为临时文件名，防止覆盖
cp $editfile $tempfile
if vim $editfile #通过vim的返回来决定如何处理
	then 
		mv $tempfile bak.$(basename $editfile) #创建备份文件
		echo "$script: backup file created"
	else
		mv $tempfile editerr
		echo "$script: edit error--copy of"\
			"original file is in editerr" 1>&2
fi
{% endhighlight %}

## SELECT ##

**select**
{% highlight bash %}
#!/bin/bash
PS3="Choose your favorite fruit："
select fruit in apple pear STOP
do
	if [ $fruit = STOP ]; then
		break
	else
		echo $fruit
	fi
done
{% endhighlight %}

## HERE ##

**here**
{% highlight bash %}
#!/bin/bash
#Here文档
#grep -i表示不区分大小写
grep -i "$1" << +
Alex June 22
Barbara February 3
Darlene May 3
+
{% endhighlight %}




****
{% highlight bash %}
{% endhighlight %}
****
{% highlight bash %}
{% endhighlight %}
****
{% highlight bash %}
{% endhighlight %}
