---
layout: post
title: "Userspace RCU"
modified:
categories: blog
excerpt:
tags: []
comments: true
share: true
counter: true
image:
  feature:
date: 2015-01-12T10:17:09+08:00
---

## lock & lock-free

|Lock|Description|
|---|---|
|Mutex|只允许一个线程同时获取，也就是同时只允许一个线程进入临界区，其他线程会挂起，等待holder释放Mutex|
|Recursive lock|Recursive lock是Mutex的变种，允许一个线程在释放之前多次获取，其他线程阻塞直到此线程释放同样的次数，可用于递归迭代，也可以用于多个函数分别获取锁的情况|
|Read-write lock|shared-exclusive lock，适用于读多写少的情况。没有写者时，读者可以同时执行读操作；写者需要阻塞等待所有的读者释放锁；读者需要阻塞等待所有写者释放锁|
|Distributed lock|分布式锁进程级别的互斥访问。不同于mutex，分布式锁不阻塞进程。在无法获取锁时由进程决定是否继续。|
|Spin lock|spin lock在无法获取锁时会重试直到获取锁，适用于等待锁的时间较小的多处理器系统，在这种系统中，重试比阻塞线程更有效，因为阻塞线程会导致上下文切换和线程数据结构的更新|
|Double-checked lock|Double-checked lock是为了解决获取锁前需要检测获取条件的损耗，但是这种锁不是很安全，尽量不要使用|
|RCU|读几乎无代价，写会延迟，在写很少且不要求数据一致的情况下高效|

题外话：futex减少非竞争状态下的系统调用

## RCU

每种锁都有特点，决定了适用的场景，RCU适用于写操作很少（注意，不是写者少）、不要求数据一致的情况下（如果写者很多会造成不一致的情况，一般情况下写者多于一个，要求一致性的场景下RCU不适用）

### RCU特点
RCU机制是在02年加入内核的，特点就是允许同时读写

|类型|特点|
|---|---|
|互斥锁 | 读者写者一视同仁，互斥访问 |
|读写锁 | 没有写的情况下，可以同时读 |
|RCU |  一写多读同时 |

写者在更新之前会检测在此之前的读操作都完成了，否则写者就等待，此时写者持有最新版本，正在读的读者会得到旧的版本。写者更新完后还需要释放旧版本数据占用的空间。

### RCU三机制

* 发布-订阅机制（用于插入）
* 等待已经存在的读者完成读取操作（用于删除）
* 维护最新数据的多个版本（对于读者）

#### 发布-订阅

	  1 struct foo {
	  2   int a;
	  3   int b;
	  4   int c;
	  5 };
	  6 struct foo *gp = NULL;
	  7 
	  8 /* . . . */
	  9 
	 10 p = kmalloc(sizeof(*p), GFP_KERNEL);
	 11 p->a = 1;
	 12 p->b = 2;
	 13 p->c = 3;
	 14 gp = p;
	 
10-14可能被编译器优化或CPU乱序执行，比如11、12完成，然后执行了14，那么新的读者就会读取到未完全初始化的数据（p->c没有初始化）

需要用内存屏障以保证CPU执行完11、12、13以后再执行14.

	  1 p->a = 1;
	  2 p->b = 2;
	  3 p->c = 3;
	  4 rcu_assign_pointer(gp, p);
	  
用rcu_assign_pointer发布新数据，强制编译器和CPU在初始化p的成员以后执行发布操作。

读者也需要，  

	  1 p = gp;
	  2 if (p != NULL) {
	  3   do_something_with(p->a, p->b, p->c);
	  4 }
	
这段代码初看可能觉得不会导致乱序问题，眼见不一定为实，the DEC Alpha CPU [PDF] and value-speculation compiler optimizations可能会在取p之前，取到p->a，p->b，p->c。

	  1 rcu_read_lock();
	  2 p = rcu_dereference(gp);
	  3 if (p != NULL) {
	  4   do_something_with(p->a, p->b, p->c);
	  5 }
	  6 rcu_read_unlock();
	  
rcu_dereference保证在执行4时可以读取到初始化过的值。

rcu_read_lock和rcu_read_unlock定义的read-size section，目的是。不会循坏或阻塞。

理论上，这两个操作可以用于RCU保护的数据结构。内核里用在了struct list_head和struct hlist_head/struct hlist_node上

	  1 struct foo {
	  2   struct list_head list;
	  3   int a;
	  4   int b;
	  5   int c;
	  6 };
	  7 LIST_HEAD(head);
	  8 
	  9 /* . . . */
	 10 
	 11 p = kmalloc(sizeof(*p), GFP_KERNEL);
	 12 p->a = 1;
	 13 p->b = 2;
	 14 p->c = 3;
	 15 list_add_rcu(&p->list, &head);
	 
15行需要同步机制的保护，防止同时添加，可以加锁，这个锁只会使写者互斥，不会导致RCU读者阻塞。

	  1 rcu_read_lock();
	  2 list_for_each_entry_rcu(p, head, list) {
	  3   do_something_with(p->a, p->b, p->c);
	  4 }
	  5 rcu_read_unlock();
	  
为何list_add_rcu的同时list_for_each_entry_rcu时不会导致segfault

单向循环链表

```
struct foo {
  struct hlist_node *list;
  int a;
  int b;
  int c;
};
HLIST_HEAD(head);

/* . . . */

p = kmalloc(sizeof(*p), GFP_KERNEL);
p->a = 1;
p->b = 2;
p->c = 3;
hlist_add_head_rcu(&p->list, &head);
```
```
rcu_read_lock();
hlist_for_each_entry_rcu(p, q, head, list) {
  do_something_with(p->a, p->b, p->c);
}
rcu_read_unlock();
```
	  
为何需要传递两个指针

Category	Publish	Retract	Subscribe
Pointers	rcu_assign_pointer()	rcu_assign_pointer(..., NULL)	rcu_dereference()
Lists	list_add_rcu() 
list_add_tail_rcu() 
list_replace_rcu()	list_del_rcu()	list_for_each_entry_rcu()
Hlists	hlist_add_after_rcu() 
hlist_add_before_rcu() 
hlist_add_head_rcu() 
hlist_replace_rcu()	hlist_del_rcu()	hlist_for_each_entry_rcu()

何时释放已经被删除或替换的数据元素，如何知道所有对此元素的读者都退出了

#### 等待已有读者完成
等待事情完成有很多机制，引用计数、读写锁、事件，RCU的优势在于可以等待20000个不同的事情，无需track每个事情，无需担心性能损失、扩展性限制、死锁、内存泄露，这些在track的策略中会出现。

RCU read-side critical section
保护任意非阻塞或sleep的代码段

（看图）


等待临界区（包括内存操作）完成。如图在Grace Period之后进入的reader可能会跨越Grace Period。

等待reader：

1. 修改，例如替换链表中的元素
2. 等待已经进入的RCU read-side临界区完成，例如，用synchronize_rcu()原子操作）。后进入的RCU read-size临界区无法获取到已经被移除的元素指针（在Grace Period之前的可以获得）
3. 清空旧的元素


可以对照下面的代码


	  1 struct foo {
	  2   struct list_head list;
	  3   int a;
	  4   int b;
	  5   int c;
	  6 };
	  7 LIST_HEAD(head);
	  8 
	  9 /* . . . */
	 10 
	 11 p = search(head, key);
	 12 if (p == NULL) {
	 13   /* Take appropriate action, unlock, and return. */
	 14 }
	 15 q = kmalloc(sizeof(*p), GFP_KERNEL);
	 16 *q = *p;
	 17 q->b = 2;
	 18 q->c = 3;
	 19 list_replace_rcu(&p->list, &q->list);
	 20 synchronize_rcu();
	 21 kfree(p);
		
19、20、21就是三个步骤，16-19就是read-copy-update，允许同时读取的。


对于synchronize_rcu()，需要等待RCU read-side临界区都完成，但是rcu_read_lock和rcu_read_unlock在未配置PREEMPT的内核里不会有任何代码产生，那如何识别

trick：read-side临界区不可block或sleep

所以CPU进行上下文切换时，可以保证read-side临界区已经完成，CPU只要执行一次上下文切换，那么synchronize_rcu可以返回

	  1 for_each_online_cpu(cpu)
	  2   run_on(cpu);
    
用上面代码表现synchronize_rcu，对每个cpu进行上下文切换，保证read-side临界区都完成。对于non-CONFIG_PREEMPT 和 CONFIG_PREEMPT 内核，已经禁止临界区抢占，所以没什么问题。

对于CONFIG_PREEMPT_RT 实时 (-rt) 内核不奏效。
这种情况下不能使用禁止抢占的策略，需要用其他策略以保证实时性。

内核里实际代码很复杂，需要处理中断、NMI、CPU热插拔等，同时要保证性能和扩展性。

#### 如何保持更新的多版本

deletion

	  1 struct foo {
	  2   struct list_head list;
	  3   int a;
	  4   int b;
	  5   int c;
	  6 };
	  7 LIST_HEAD(head);
	  8 
	  9 /* . . . */

	  1 p = search(head, key);
	  2 if (p != NULL) {
	  3   list_del_rcu(&p->list);
	  4   synchronize_rcu();
	  5   kfree(p);
	  6 }

（图）

图中没有画tail->head的指针

replacement


  
