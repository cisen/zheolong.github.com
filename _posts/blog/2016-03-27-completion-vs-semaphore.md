---
layout: post
title: "Completion vs Semaphore"
modified:
categories: blog
excerpt:
tags: []
comments: true
share: true
counter: true
image:
  feature:
date: 2016-03-27T21:34:05+08:00
---

## 引入completion的原因

参考http://lkml.iu.edu/hypermail/linux/kernel/0107.3/0674.html

在2.4.7版本内核中引入completion时，semaphore没有锁保护。semaphore在SMP架构下会遇到竞态，虽然情况很少（从理论和实现上都是）。当时没有选择修复的原因是：

1. semaphore主要是用在无竞态的情况下，而“wait for completion”默认是用在竞态的情况下。
2. 因为其设计目的（非竞态情况），semaphore相当复杂而且跟体系结构有关，很难修改。

所以引入了“wait for completion”的概念：

```
struct completion event; 
        init_completion(&event); 
        .. pass of event pointer to waker .. 
        wait_for_completion(&event); 
```

这样，改变条件的线程只需要“complete(event)”就行了。

completion有两个优势：

1. 在使用模式为两种状态，完成和未完成的情况下，比semaphore用起来简便些。
2. 只关注是否完成，比semaphore高效一些。

对上面提到的竞态的详细解释如下：

semaphore的竞态在于仅仅保护了semaphore内的访问，而semaphore本身可能被同时访问，可以给semaphore本身加锁，如下：

        cpu #1	cpu #2 
        DECLARE_MUTEX_LOCKED(sem); 
        .. 
        down(&sem);	up(&sem); 
        return; 
                      wake_up(&sem.wait) /*BOOM*/ 
                                        
但是waker在sleeper被唤醒并释放了semaphore的空间以后，仍然能访问semaphore数据结构，导致程序崩溃。

## completion vs semaphore

现在semaphore已经没有问题了。甚至有人还提议用semaphore重新实现completion：http://lwn.net/Articles/277621/ 。

现在高版本的semaphore已经不存在问题了。只是从概念层面，completion 和semaphore 应该被用来不同的场合，completion是用来等待一个条件成力，而semaphore应该是等待一个资源。条件是没有数量的，而资源是有数量的。

上面也提到了，completion的模式更高效一些。参见：http://www.makelinux.net/ldd3/chp-5-sect-4

在实际的使用中，使用completion而非semaphore有两个原因：

1. 多个线程等待某个条件，如果另一个线程调用了complete_all()，那么这些线程都会被唤醒，但是用semaphore唤醒未知数量的线程会难一些。
2. waiter可能会被唤醒并释放semaphore数据结构，而唤醒它的线程还未调用up()，对于completion来说不存在这个问题。
