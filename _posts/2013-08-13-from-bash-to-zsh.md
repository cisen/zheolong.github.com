---
layout: post
title: "from bash to zsh"
description: ""
category: Shell
tags: []
---
{% include JB/setup %}

oh-my-zsh is an open source, community-driven framework for managing your ZSH configuration. It comes bundled with a ton of helpful functions, helpers, plugins, themes, and few things that make you shout…

>"OH MY ZSHELL"

# Setup #

-------------------------------------------------------------------------------

`oh-my-zsh` should work with any recent release of [zsh](http://www.zsh.org/), the minimum recommended version is __4.3.9__.

For Ubuntu:

1. Clone the repository

`git clone git://github.com/robbyrussell/oh-my-zsh.git ~/.oh-my-zsh`

2. OPTIONAL Backup your existing ~/.zshrc file (ps:if you have no ~/.zshrc, please skip this)

`cp ~/.zshrc ~/.zshrc.orig`

3. Create a new zsh config by copying the zsh template we’ve provided.

`cp ~/.oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc`

4. Set zsh as your default shell:

`chsh -s /bin/zsh`

5. Start / restart zsh (open a new terminal is easy enough…)

# Env Variables #
{: style="color: salmon"}

-------------------------------------------------------------------------------

You might need to modify your PATH in ~/.zshrc if you’re not able to find some commands after switching to Oh My Zsh.

# Usage & Themes & Update #

-------------------------------------------------------------------------------

refer to [oh-my-zsh README](https://github.com/robbyrussell/oh-my-zsh/blob/master/README.textile)
