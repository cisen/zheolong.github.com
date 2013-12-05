---
layout: post
title: "latex references"
description: ""
category: LaTex
tags: []
---
{% include JB/setup %}

<!-- 目录 -->
* toc
{:toc}

<!-- 正文 -->

本blog关于latex参考文献。

## url太长，导致间距被拉大 ##

解决方法：

在.bls
{% highlight latex %}
\RequirePackage{url} % hyperref works too
\urlstyle{same}  % (sf also works, for something more subtle than tt)
{% endhighlight %}

在JabRef中
{% highlight c %}
\url{http://www.example.com/~lev/my%20long%20url}
{% endhighlight %}

<!-- 代码块(注意修改语言) -->
{% highlight c %}
c code
{% endhighlight %}
