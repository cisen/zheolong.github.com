---
layout: post
title: "jekyll: code highlight and line number and so on"
description: ""
category: Jekyll
tags: []
---
{% include JB/setup %}

__Highly recommended__{: style="color: red"}: [Jekyll Templates](http://jekyllrb.com/docs/templates/)

-------------------------------------------------------------------------------

Table of Contents
=================

-------------------------------------------------------------------------------

* toc
{:toc}



# enable pygments in _config.yml #
-------------------------------------------------------------------------------

add `pygments: true` to your _config.yml

# code highlight #
{: style="color: #8FBC8F"}

-------------------------------------------------------------------------------

[refer to](http://jekyllrb.com/docs/templates/)

*example*:
<pre><code class="no-highlight">{&#37; highlight ruby &#37;}
def foo
puts 'foo'
end
{&#37; endhighlight &#37;}
</code></pre>

*effect*:
{% highlight ruby %}
def foo
puts 'foo'
end
{% endhighlight %}

# Line numbers #
-------------------------------------------------------------------------------
There is a second argument to `highlight` called `linenos` that is optional.

*example*:
<pre><code class="no-highlight">{&#37; highlight ruby linenos &#37;}
def foo
puts 'foo'
end
{&#37; endhighlight &#37;}
</code></pre>

*effect*:
{% highlight ruby linenos%}
def foo
puts 'foo'
end
{% endhighlight %}

# Post URL #
-------------------------------------------------------------------------------
If you would like to include a link to a post on your site, the `post_url` tag will generate the correct permalink URL for the post you specify.

*example*:
<pre><code class="no-highlight">{&#37; 2013-08-08-htmlprettify-format-htmlcss-code &#37;}
</code></pre>

*effect*:

[htmlprettify-format-htmlcss-code]({% post_url 2013-08-08-htmlprettify-format-htmlcss-code %})

# Gist #
-------------------------------------------------------------------------------
Use the `gist` tag to easily embed a GitHub Gist onto your site:

*example*:

<pre><code class="no-highlight">{&#37; gist 5555251 &#37;}
</code></pre>

*effect*:

{% gist 5555251 %}

You may also optionally specify the filename in the gist to display:

<pre><code class="no-highlight">{&#37; gist 5555251 result.md &#37;}
</code></pre>

The `gist` tag also works with private gists:

<pre><code class="no-highlight">{&#37; gist 931c1c8d465a04042403 &#37;}
</code></pre>

The private gist syntax also supports filenames.


{{ site.time | date_to_xmlschema }}
