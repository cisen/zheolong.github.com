---
layout: post
title: "how to include math formula in jekyll"
description: ""
category: jekyll
tags: []
---
{% include JB/setup %}


当markdown解析引擎为kramdown时

example:

{% highlight latex %}
$$ 
e^x = \sum_{n=0}^\infty \frac{x^n}{n!} = \lim_{n\rightarrow\infty} (1+x/n)^n 
$$
{% endhighlight %}

effect： 

$$ 
e^x = \sum_{n=0}^\infty \frac{x^n}{n!} = \lim_{n\rightarrow\infty} (1+x/n)^n 
$$
