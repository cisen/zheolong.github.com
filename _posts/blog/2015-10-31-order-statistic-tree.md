---
layout: post
title: "Order Statistic Tree"
modified:
categories: blog
excerpt:
tags: []
comments: true
share: true
counter: true
image:
  feature:
date: 2015-10-31T20:45:50+08:00
---

## Order statistic tree

顺序统计树是二叉查找树（或者更普遍的B树），除了插入、查找、删除外，还支持两种操作：

* Select(i) —— 查找树中的第*i*个最小元素；
* Rank(x) —— 查找元素*x*在树中的次序。

两个操作的平均时间为O(log n)；当使用自平衡树作为基础数据结构时，在最坏的情况下时间也是O(log n)。

为了将普通的查找树变为顺序统计树，树节点需要多存储一个值，即以其为根的子树的节点总数。所有对树的修改操作都需要修改此值，以保证下式成立：

```size[x] = size[left[x]] + size[right[x]] + 1```

其中，```size[nil] = 0```。

Select操作的伪代码如下：

```
function Select(t, i)
    // Returns the i'th element (zero-indexed) of the elements in t
    r ← size[left[t]]
    if i = r
        return key[t]
    else if i < r
        return Select(left[t], i)
    else
        return Select(right[t], i - (r + 1))
```

Rank操作的伪代码如下：

```
function Rank(T, x)
    // Returns the position of x (one-indexed) in the linear sorted list of elements of the tree T
    r ← size[left[x]] + 1
    y ← x
    while y ≠ T.root
         if y = right[y.p]
              r ← r + size[left[y.p]] + 1
         y ← y.p
    return r
```

顺序统计树可以加入一些薄记信息以保持平衡（例如，加入树的高度信息得到顺序统计AVL树，或者颜色信息得到红黑顺序统计树）。或者，在权重均衡模式中加入大小字段。

有些顺序统计树是通过最小最大堆加入隐式数据结构来构造的。


