---
layout: post
title: "latex tips"
description: ""
category: LaTex 
tags: []
---
{% include JB/setup %}

<!-- 目录 -->
* toc
{:toc}

<!-- 正文 -->

## 注释 ##

* `%`注释一行文字，`%`后面的文字不予编译
* `\iffalse...\fi`注释一段文字，被包含的文字不予编译
* `\begin{comment} ... \end{comment}`包含被注释的文字, 但是需要在引言区包括相应的宏包, 即`\usepackage{verbatim}`.

<!-- 代码块(注意修改语言) -->
{% highlight c %}
c code
{% endhighlight %}
