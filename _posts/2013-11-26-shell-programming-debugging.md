---
layout: post
title: "shell programming: debugging"
description: ""
category: Shell
tags: []
---
{% include JB/setup %}

<!-- 目录 -->
* toc
{:toc}

<!-- 正文 -->
引用自：[Shell脚本调试技术](http://www.ibm.com/developerworks/cn/linux/l-cn-shell-debug/)

## echo或print输出 ##
在脚本中使用echo输出变量的值，zsh和ksh可以使用print

## trap ##

**作用** 捕获指定的信号并执行预定义的命令
**语法** `trap 'command' signal`
**解释**
其中signal是要捕获的信号，command是捕获到指定的信号之后所要执行的命令。
可以用kill –l命令看到系统中全部可用的信号名，捕获信号后所执行的命令可以
是任何一条或多条合法的shell语句，也可以是一个函数名。shell脚本在执行时，
会产生三个所谓的“伪信号”，(之所以称之为“伪信号”是因为这三个信号是由
shell产生的，而其它的信号是由操作系统产生的)，通过使用trap命令捕获这三
个“伪信号”并输出相关信息对调试非常有帮助。

<table>
   <tr>
      <td>信号名</td>
      <td>何时产生</td>
   </tr>
   <tr>
      <td>EXIT</td>
      <td>从一个函数中退出或整个脚本执行完毕</td>
   </tr>
   <tr>
      <td>ERR</td>
      <td>当一条命令返回非零状态时(代表命令执行不成功)</td>
   </tr>
   <tr>
      <td>DEBUG</td>
      <td>脚本中每一条命令执行之前</td>
   </tr>
</table>

通过捕获EXIT信号,我们可以在shell脚本中止执行或从函数中退出时，输出某些
想要跟踪的变量的值，并由此来判断脚本的执行状态以及出错原因,其使用方法是：
trap 'command' EXIT　或　trap 'command' 0

通过捕获ERR信号,我们可以方便的追踪执行不成功的命令或函数，并输出相关的
调试信息，以下是一个捕获ERR信号的示例程序，其中的$LINENO是一个shell的内
置变量，代表shell脚本的当前行号。

{% highlight bash %}
$ cat -n exp1.sh
     1  ERRTRAP()
     2  {
     3    echo "[LINE:$1] Error: Command or function exited with status $?"
     4  }
     5  foo()
     6  {
     7    return 1;
     8  }
     9  trap 'ERRTRAP $LINENO' ERR
    10  abc
    11  foo
{% endhighlight %}

输出结果:
{% highlight c %}
$ sh exp1.sh
exp1.sh: line 10: abc: command not found
[LINE:10] Error: Command or function exited with status 127
[LINE:11] Error: Command or function exited with status 1
{% endhighlight %}

**通过捕获DEBUG信号，只需一条trap语句完成全程跟踪**

通过捕获DEBUG信号来跟踪变量的示例程序:

{% highlight bash %}
$ cat –n exp2.sh
     1  #!/bin/bash
     2  trap 'echo “before execute line:$LINENO, a=$a,b=$b,c=$c”' DEBUG
     3  a=1
     4  if [ "$a" -eq 1 ]
     5  then
     6     b=2
     7  else
     8     b=1
     9  fi
    10  c=3
    11  echo "end"
{% endhighlight %}

输出结果:
{% highlight bash %}
$ sh exp2.sh
before execute line:3, a=,b=,c=
before execute line:4, a=1,b=,c=
before execute line:6, a=1,b=,c=
before execute line:10, a=1,b=2,c=
before execute line:11, a=1,b=2,c=3
end
{% endhighlight %}

## tee ##

 在shell脚本中管道以及输入输出重定向使用得非常多，在管道的作用下，一些
 命令的执行结果直接成为了下一条命令的输入。如果我们发现由管道连接起来的
 一批命令的执行结果并非如预期的那样，就需要逐步检查各条命令的执行结果来
 判断问题出在哪儿，但因为使用了管道，这些中间结果并不会显示在屏幕上，给
 调试带来了困难，此时我们就可以借助于tee命令了。

tee命令会从标准输入读取数据，将其内容输出到标准输出设备,同时又可将内容
保存成文件。例如有如下的脚本片段，其作用是获取本机的ip地址：

<!-- 代码块(注意修改语言) -->
{% highlight c %}
c code
{% endhighlight %}

