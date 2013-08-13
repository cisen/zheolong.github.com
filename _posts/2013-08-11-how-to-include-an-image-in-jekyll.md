---
layout: post
title: "how to include images and resources in jekyll"
description: ""
category: jekyll
tags: []
---
{% include JB/setup %}

Including images and resources

Chances are, at some point, you’ll want to include images, downloads, or other digital assets along with your text content. While the syntax for linking to these resources differs between Markdown and Textile, the problem of working out where to store these files in your site is something everyone will face.

Because of Jekyll’s flexibility, there are many solutions to how to do this. One common solution is to create a folder in the root of the project directory called something like assets or downloads, into which any images, downloads or other resources are placed. Then, from within any post, they can be linked to using the site’s root as the path for the asset to include. Again, this will depend on the way your site’s (sub)domain and path are configured, but here some examples (in Markdown) of how you could do this using the site.url variable in a post.

# Including an image asset in a post: #

example:

	… which is shown in the screenshot below:
	![My helpful screenshot]({{ site.url }}/assets/images/screenshot.jpg)

effect:

![My helpful screenshot]({{ site.url }}/assets/images/screenshot.jpg)


# Linking to a PDF for readers to download: #

	… you can [get the PDF]({{ site.url }}/assets/images/mydoc.pdf) directly.

effect:

[get the PDF]({{ site.url }}/assets/images/worldmap.pdf) 

>ProTip™: Link using just the site root URL




