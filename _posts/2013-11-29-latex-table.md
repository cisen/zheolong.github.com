---
layout: post
title: "latex table"
description: ""
category: LaTex
tags: []
---
{% include JB/setup %}

<!-- 目录 -->
* toc
{:toc}

<!-- 正文 -->

## 参考资料 ##

[LaTeX/Tables](http://en.wikibooks.org/wiki/LaTeX/Tables)

## 表格第一行居中 ##
表格模式设置左对齐然后第一行用`\multicolumn{1}{|c|}{文本内容}`就可以了

{% highlight latex %}
\begin{table}[h!]
  \centering
  \caption{实验所用性能指标}
  \label{tab:performance-indicators}
  \begin{tabular}[c]{|l|l|}
  \hline
  \multicolumn{1}{|c|}{评价指标} & \multicolumn{1}{|c|}{含义}\\
  \hline
  队列长度 & 配置实验算法的队列瞬时数据包个数 \\
  \hline
  丢包率 & 所丢失数据包数量占所发送数据包的比率\\
  \hline
  有效吞吐量 & 网络单位时间内成功地传送数据的数量\\
  \hline
  平均时延 & 所测量数据包从网络的一端传送到另一个端所需时间的平均值\\
  \hline
  时延抖动 & 不同数据包之间的时延差异\\
  \hline
\end{tabular}
\end{
{% endhighlight %}

## 单元格垂直居中 ##

>array package loaded. p{...} aligns the content toward the top, m{...} aligns the content toward the center, while b{...} aligns it toward the bottom.

p表示顶部对齐，m表示中部对齐，b表示底部对齐

原先`\begin{tabular}[c]{|l|l|l|p{6.5cm}|}`的效果:

![vertical_top_align](/assets/images/LaTex/table/vertical_top_align.jpg)

将`p`改为`m`后的效果:

![vertical_mid_align](/assets/images/LaTex/table/vertical_mid_align.jpg)

参见array包的文档第二页：

![array_package_options](/assets/images/LaTex/table/array_package_options.jpg)

<!-- 代码块(注意修改语言) -->
{% highlight c %}
c code
{% endhighlight %}
