---
layout: post
title: "beamer tips"
description: ""
category: 
tags: []
---
{% include JB/setup %}

<!-- 目录 -->
* toc
{:toc}

<!-- 正文 -->

PDF offers a standardized way for transitions and these work in also in Beamer Latex. You can use them in Latex between `\begin{frame}` and `\end{frame}` and they should work with common PDF viewers.

Horizontal blinds pulled away

\transblindshorizontal

Vertical blinds pulled away

\transblindsvertical

Move to center from all sides

\transboxin

Move to all sides from center

\transboxout

Slowly dissolve what was shown before

\transdissolve

Glitter sweeps in specified direction

\transglitter

Sweeps two vertical lines in

\transslipverticalin

Sweeps two vertical lines out

\transslipverticalout

Sweeps two horizontal lines in

\transhorizontalin

Sweeps two horizontal lines out

\transhorizontalout

Sweeps single line in specified direction

\transwipe

Show slide specified number of seconds

\transduration{2}

<!-- 代码块(注意修改语言) -->
{% highlight c %}
c code
{% endhighlight %}
