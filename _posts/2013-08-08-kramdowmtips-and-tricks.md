---
layout: post
title: "Kramdowm: tips and tricks"
description: ""
category: Jekyll 
tags: []
---
{% include JB/setup %}

* toc
{:toc}

# What is Kramdowm #
转换器：markdown->HTML，除了支持markdown最基本的语法，还对其进行了扩展。

# Typical Configuration #
Change in `_config.yml`

	markdown: kramdown
	...
	kramdown:
		auto_ids: true
		footnote_nr: 1
		entity_output: as_char
		toc_levels: 1..6
		use_coderay: false
		parse_block_html: true

# Create TOC #

The Table of Content work easily with just : (and with some css adjustment)

	* toc
	{:toc}

# Inline Attributes #
{: style="color: red"}
	
	This is *red*{: style="color: red"}.

	**This is a test**
	{: style="text-align: center"}

	Title
	=====
	{: .big .thin}

[learn more](http://kramdown.rubyforge.org/converter/html.html)

# Markdown in HTML Block #

declare inner markdown usage in HTML block

	{::options parse_block_html="true" /}
	<div>
		test **test**
	</div>
	

If "true", then show:
{::options parse_block_html="true" /}
<div>
	test **test**
</div>
	
If "false", then show:
{::options parse_block_html="false" /}
<div>
	test **test**
</div>
