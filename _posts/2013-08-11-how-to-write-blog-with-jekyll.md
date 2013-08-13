---
layout: post
title: "how to write blog with jekyll"
description: ""
category: jekyll
tags: []
---
{% include JB/setup %}

I assumed that you have already installed jekyll and configure it properly.

# Create Page #

{% highlight bash %}
$rake page name="pages/about"
Creating new page: ./pages/about/index.html

$rake page name="pages/about.md"
Creating new page: ./pages/about.md

$rake page name="about.md"
Creating new page: ./about.md
{% endhighlight %}
# Create Post #

{% highlight bash %}
$ rake post title="name_of_new_post"
{% endhighlight %}

# Test Locally #

{% highlight bash %}
$ jekyll serve
# => A development server will run at http://localhost:4000/

$ jekyll serve --watch
# => As above, but watch for changes and regenerate automatically.
{% endhighlight %}
open a browser, you will see the locally updated blog in `http://localhost:4000/`.

# Push to GitHub #

{% highlight bash %}
$ git add .
$ git commit -m "first post"
$ git push origin gh-pages
{% endhighlight %}
you will see the globally updated blog in `http://your_github_username.github.com/`.


