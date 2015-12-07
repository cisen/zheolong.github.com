---
layout: post
title: "Read Lines From File"
modified:
categories: blog
excerpt:
tags: []
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
