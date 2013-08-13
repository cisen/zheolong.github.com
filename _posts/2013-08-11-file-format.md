---
layout: post
title: "file format"
description: ""
category: LaTex 
tags: []
---
{% include JB/setup %}

1. .cls 文件

.cls文件为.tex文件的格式文件，比如我们一般使用的article.cls文件，可以通过/documentclass{article}来引用。

可以放在LaTeX文件的同一个目录下，或者放在C:/CTeX/localtexmf/tex/latex下的一个目录（可以自己建立）。


2. .sty 文件

.sty文件是LaTeX的宏集，定义文档结构和外观

使用/usepackage{xxx}导入

 

3. BibTeX

.bib文件：是参考文件的条目文件

.bst文件：BibTeX处理.bib文件后，生产.bbl文件，.bst文件 是bib文件输出的格式文件

.bbl文件：bibtex处理 bib文件后，生产.bbl文件 
