---
layout: post
title: "HTMLPrettify: format HTML,CSS code"
description: "A plugin for sublime to format HTML and CSS files"
category: Sublime
tags: [Sublime,HTMLPrettify,HTML,CSS,format]
---
{% include JB/setup %}

## Install HTMLPrettify ##

建议先启用Package Control，作用是安装插件时很方便，启用方法：菜单栏 – View – Show Console，贴入以下代码并回车，然后重启Sublime。如果你所在的网络无法启用，则无法使用，手动搜索下载。


	import urllib2,os; pf='Package Control.sublime-package'; ipp=sublime.installed_packages_path(); os.makedirs(ipp) if not os.path.exists(ipp) else None; urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler())); open(os.path.join(ipp,pf),'wb').write(urllib2.urlopen('http://sublime.wbond.net/'+pf.replace(' ','%20')).read()); print('Please restart Sublime Text to finish installation')


Ctrl+Shift+P（菜单 – Tools – Command Paletter），输入 install 选中Install Package并回车，输入或选择你需要的插件回车就安装了（注意左下角的小文字变化，会提示安装成功），安装其它插件也是这个方法，非常快速。

## Use HTMLPrettify ##

1. 打开一个.html或.css文件（其他类型的文件不可以）
2. Ctrl+Shift+P（菜单 – Tools – Command Paletter），输入 HTMLPrettify 选中HTMLPrettify并回车
