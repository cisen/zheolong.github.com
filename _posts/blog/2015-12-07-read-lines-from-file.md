---
layout: post
title: "Read Lines From File"
modified:
categories: blog
excerpt:
tags: []
comments: true
share: true
counter: true
image:
  feature:
date: 2015-12-07T16:43:59+08:00
---

本篇博客探讨的如何利用c/c++语言读取文件中的各行，通过比较各种方式的优缺点，对不同的场景选择不同的方法。

## 读取文件各行的方法

### gets & fgets

```
#include <stdio.h>

char *gets(char *s);
char *fgets(char *s, int size, FILE *stream);
```

gets是最简单的方法，但是gets无法限制读取的数据量，可能导致缓冲区越界，LSB已经废弃了该函数。

fgets能够设置每次读取的数据量上限，但是仍然有两个缺陷：

1. 对于二进制文件，无法获取实际所读取的数据量；
2. 无法定义行分隔符；
3. 每次读取一行可能导致效率不高，尤其是对于每行数据较少的情况。

对于fgets，在使用BSD libc的情况下，如果在读到文件尾（EOF）之后还需要读取后续增加的数据，那么需要主动调用clearerr来清除EOF和ERR标记，否则，即使有新数据追加到文件，但是利用fgets读取时，仍然会直接检测到EOF，导致无法读取新数据。对于Glibc来说没有这个问题。

### getline & getdelim

```
#define _GNU_SOURCE
#include <stdio.h>

ssize_t getline(char **lineptr, size_t *n, FILE *stream);
ssize_t getdelim(char **lineptr, size_t *n, int delim, FILE *stream);
```

getline和getdelim会自动对缓冲区扩容，不会造成缓冲区越界，两者都会返回所读取的数据量，支持二进制文件，并且getdelim可以自定义行分隔符，其缺点在于

1. 目前只有GNU C编译器支持这两个函数，使得其无法跨编译器；
2. 每次读取一行可能导致效率不高，尤其是对于每行数据较少的情况。

### fread

```
#include <stdio.h>

size_t fread(void *ptr, size_t size, size_t nmemb, FILE *stream);
```

可以利用fread自己编写行读取函数，其优点是

1. 跨编译器；
2. 可以设置数据量上限，不会造成缓冲区越界；
3. 返回所读取的数据量，支持二进制文件；
4. 每次读取尽量多的数据，减少整个文件读取涉及的系统调用次数，提高效率；
5. 行分隔逻辑可以自己定义，所以可以添加自定义的行分隔符。

当然，缺点就是需要自己编写行分隔逻辑，比其他利用c标准库的方法都要困难一些，造成bug的几率也会较高。

### fstream

采用c++而不用c的主要考虑是类型安全、面向对象，但是这取决于你的项目整体对文件的操作是否都可以使用fstream，如果可以，那么请毫不犹豫得使用fstream，其效率不会比c的标准库行数慢，所耗内存也不会比c的标准库函数多太多。

```
while (std::getline(fs, line))
{}
```

在上面的代码中没有必要用```fs.good()```检测读取是否成功，对于```good```，c++的文档如下：

> The function returns true if none of the stream's error flags (eofbit, failbit and badbit) are set.

需要注意的是，eof等标志位是在尝试读取失败以后才被设置的，而非之前，所以请在读取之后检测。

错误的方式如下：

```
while (!somestream.eof()) {
    read_data();
    process_data();
}
```

很可能导致最后一行被读取两次。对于为何这种通过检测```eof```来结束循环的方式不正确，请参考这篇博客[Reading files](http://coderscentral.blogspot.tw/2011/03/reading-files.html)

## 行分隔符

如果在unix下读取dos格式的文件，因为dos格式所用的换行符是```\r\n```，所以仅仅去掉```\n```是不够的，还需要去掉```\r```，否则对于文本文件，在打印每一行时，会因为```\r```而打印不出期望的结果。

例如，```cout << "ab\r"<< "c" << endl;```会打印出```cb```而非```abc```，因为```\r```在unix中代表回到当前行的头部开始打印，所以后面的c会“覆盖”掉a。

## wide I/O vs byte I/O

| 函数 | 对应的wide char版本 |
|-----| -------------------|
|getc/putc | getwc/putwc   |
|gets/puts | 无            |
|fgets/fputs| fgetws/fputws|
|getline/getdelim | 无     |
|fread/fwrite | 无         |

还有很多，参见
[Wide character](https://en.wikipedia.org/wiki/Wide_character)，
[c Programming/C Reference/wchar.h](https://en.wikibooks.org/wiki/C_Programming/C_Reference/wchar.h)

byte char是用8bits。

> c++中的char类型是8-bits，对应ASCII（或扩展的ASCII）字符集，而java中的char类型默认是16 bits，unicode字符集（unicode的0-127对应ASCII字符）。

而```wchar_t```的具体表示取决于实现（编译器）。刚开始引入这个概念是因为ISO 10646和Unicode正在竞争（现在处于合作状态），与其决定是具体是哪种编码方案，不如定义一个抽象类型（和一些函数），而具体后面用什么编码是实现者自己选。

如果使用Windows的编译器，```wchar_t```是16-bits，编码方式为UTF-16 Unicode。在Linux平台上，```wchar_t```一般是32-bits，编码方式为UCS-4/UTF-32 Unicode。但是在理论上，Windows的编译器可以使用32-bits，而Linux的编译器可以使用16-bits。

然而，无论具体实现如何，```wchar_t```的思想是要足够表示Unicode的一个字符，即一个code point。对于I/O，在输入时，数据会从外部表示转化为```wchar_t```，这样应该更好操作数据，而在输出时，可以转化为任何你想要的编码。

用于I/O时，```wchar_t```对可移植是不友好的。

如果用char的操作函数来读取行而非```wchar_t```，那么对于UTF-8编码的文件，应该没有什么问题，因为其兼容了ASCII，也没有大小端问题；如果是UTF-16编码的文件，每个字符都是用两个字节表示，那么用char就会很麻烦，因为换行符\n也是两个字节。

## multibyte char vs wide char

multibyte char，其bits数不固定。multibyte char和wide char之间可以转化，使用如下这些C标准库函数：mbstowcs, mbtowc, wcstombs, wctomb。

一般在国际化的工作中，multibyte char一般表示一些传统的编码方式（除Unicode以外），这些编码方式可能会用一个或多个bit来表示一个字符，例如Shift-jis, jis, euc-jp, euc-kr和Chinese encodings。

大部分的传统编码需要一种状态机模型（或者，更简单的，页交换模型（page swapping model））来处理，在文本流中后退很复杂且容易出错。而UTF-8或UTF-16没有这个问题，UTF-8可以用bitmask来检测，UTF-16可以用一定区间的替代对检测，所以前进后退没有那么复杂。
