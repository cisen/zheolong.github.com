---
layout: post
title: "Synchronization Mechanism"
modified:
categories: blog
excerpt:
tags: [RCU, lock]
comments: true
share: true
image:
  feature:
  
date: 2015-01-10T16:08:35+08:00
---

# 同步
多线程如何安全地访问资源一直是多线程编程中的一个重要问题。访问同一个资源的两个线程可能互相干扰。例如，一个线程可能会覆盖另一个线程的修改，使得程序进入未知或非法状态。如果错误的资源导致严重的性能问题或崩溃，可以很容易地跟踪和修复。如果只导致很小的错误而未被发现，经过一段时间才出现问题，或者需要对核心代码假设进行全面检查才能发现。

涉及到线程安全时，为了防止线程间互相影响，应尽可能减少共享资源和线程交互，但是当线程间必须进行交互时，需要采用同步技术确保安全。

# 同步技术
下面是常用的同步技术。

## 原子操作
原子操作是针对简单数据类型的同步方式，其优点是不会阻塞竞争的线程。对于简单的操作，比如增大count变量，性能会比锁高很多。

c语言中的“count++”，在未经编译器优化时，生产的汇编代码是

||
|--|
|mov eax,[count]|
|inc eax|
|mov [count],eax|

多进程执行时可能会导致问题，例如

|p1|p2|
|--|--|
|mov eax,[count]|wait|
|wait|mov eax,[count]|
|wait|inc eax|
|wait|mov [count],eax|
|inc eax|wait|
|mov [count],eax|wait|

执行后count值为1，而不是2。

### 单处理器原子操作

如果用一条执行表示“count++”

||
|--|--|
|count++;|inc [count]|

Intel x86指令集支持内存操作数的inc操作，这样“count++;”操作可以在一条指令内完成。因为进程的上下文切换是在总是在一条指令执行完成后，所以不会出现上述的并发问题。对于单处理器来说，一条处理器指令就是一个原子操作。

### 多处理器原子操作

但是在多处理器的环境下，例如SMP架构，这个结论不再成立。我们知道“inc [count]”指令的执行过程分为三步：

1）从内存将count的数据读取到cpu。

2）累加读取的值。

3）将修改的值写回count内存。

这又回到前面并发问题类似的情况，只不过此时并发的主题不再是进程，而是处理器。

Intel x86指令集提供了指令前缀lock用于锁定前端串行总线（FSB），保证了指令执行时不会受到其他处理器的干扰。

||
|--|--|
|count++;|**lock** inc [count]|

使用lock指令前缀后，处理器间对count内存的并发访问（读/写）被禁止，从而保证了指令的原子性。

### x86原子操作实现

Linux的源码中x86体系结构原子操作的定义文件为。

linux2.6/include/asm-i386/atomic.h

文件内定义了原子类型atomic_t，其仅有一个字段counter，用于保存32位的数据。

```
typedef struct { volatile int counter; } atomic_t;
```

其中原子操作函数atomic_inc完成自加原子操作。

```
/**

 * atomic_inc - increment atomic variable

 * @v: pointer of type atomic_t

 *

 * Atomically increments @v by 1.

 */

static __inline__ void atomic_inc(atomic_t *v)

{

    __asm__ __volatile__(

       LOCK "incl %0"

       :"=m" (v->counter)

       :"m" (v->counter));

}
```

其中LOCK宏的定义为。

```
#ifdef CONFIG_SMP

    #define LOCK "lock ; "

#else

    #define LOCK ""

#endif
```

可见，在对称多处理器架构的情况下，LOCK被解释为指令前缀lock。而对于单处理器架构，LOCK不包含任何内容。

### arm原子操作实现

在arm的指令集中，不存在指令前缀lock，那如何完成原子操作呢？

Linux的源码中arm体系结构原子操作的定义文件为。

linux2.6/include/asm-arm/atomic.h

其中自加原子操作由函数atomic_add_return实现。

```
static inline int atomic_add_return(int i, atomic_t *v)

{

    unsigned long tmp;

    int result;

    __asm__ __volatile__("@ atomic_add_return\n"

       "1:     ldrex   %0, [%2]\n"

       "       add     %0, %0, %3\n"

       "       strex   %1, %0, [%2]\n"

       "       teq     %1, #0\n"

       "       bne     1b"

       : "=&r" (result), "=&r" (tmp)

       : "r" (&v->counter), "Ir" (i)

       : "cc");

    return result;

}
```

上述嵌入式汇编的实际形式为

```
1:

ldrex  [result], [v->counter]

add    [result], [result], [i]

strex  [temp], [result], [v->counter]

teq    [temp], #0

bne    1b
```

ldrex指令将v->counter的值传送到result，并设置全局标记“Exclusive”。

add指令完成“result+i”的操作，并将加法结果保存到result。

strex指令首先检测全局标记“Exclusive”是否存在，如果存在，则将result的值写回counter->v，并将temp置为0，清除“Exclusive”标记，否则直接将temp置为1结束。

teq指令测试temp值是否为0。

bne指令temp不等于0时跳转到标号1，其中字符b表示向后跳转。

整体看来，上述汇编代码一直尝试完成“v->counter+=i”的操作，直到temp为0时结束。

使用ldrex和strex指令对是否可以保证add指令的原子性呢？假设两个进程并发执行“ldrex+add+strex”操作，当进程1执行ldrex后设定了全局标记“Exclusive”。此时切换到进程2，执行ldrex前全局标记“Exclusive”已经设定，ldrex执行后重复设定了该标记。然后执行add和strex指令，完成累加操作。再次切换回进程1，接着执行add指令，当执行strex指令时，由于“Exclusive”标记被进程2清除，因此不执行传送操作，将temp设置为1。后继teq指令测定temp不等于0，则跳转到起始位置重新执行，最终完成累加操作！可见ldrex和strex指令对可以保证进程间的同步。多处理器的情况与此相同，因为arm的原子操作只关心“Exclusive”标记，而不在乎前端串行总线是否加锁。

在ARMv6之前，swp指令就是通过锁定总线的方式完成原子的数据交换，但是影响系统性能。ARMv6之后，一般使用ldrex和strex指令对代替swp指令的功能。

### 自旋锁中的原子操作

Linux的源码中x86体系结构自旋锁的定义文件为。

linux2.6/include/asm-i386/spinlock.h

其中__raw_spin_lock完成自旋锁的加锁功能
```

#define __raw_spin_lock_string \

    "\n1:\t" \

    "lock ; decb %0\n\t" \

    "jns 3f\n" \

    "2:\t" \

    "rep;nop\n\t" \

    "cmpb $0,%0\n\t" \

    "jle 2b\n\t" \

    "jmp 1b\n" \

    "3:\n\t"

static inline void __raw_spin_lock(raw_spinlock_t *lock)

{

    __asm__ __volatile__(

       __raw_spin_lock_string

       :"=m" (lock->slock) : : "memory");

}
```

上述代码的实际汇编形式为。

```
1：
lock   decb [lock->slock]
jns    3

2:
rep    nop
cmpb   $0, [lock->slock]
jle    2
jmp    1

3:
```

其中lock->slock字段初始值为1，执行原子操作decb后值为0。符号位为0，执行jns指令跳转到3，完成自旋锁的加锁。

当再次申请自旋锁时，执行原子操作decb后lock->slock值为-1。符号位为1，不执行jns指令。进入标签2，执行一组nop指令后比较lock->slock是否小于等于0，如果小于等于0回到标签2进行循环（自旋）。否则跳转到标签1重新申请自旋锁，直到申请成功。

自旋锁释放时会将lock->slock设置为1，这样保证了其他进程可以获得自旋锁。

### 信号量中的原子操作

Linux的源码中x86体系结构信号量的定义文件为：
linux2.6/include/asm-i386/semaphore.h

信号量的申请操作由函数down实现。

```
/*

 * This is ugly, but we want the default case to fall through.

 * "__down_failed" is a special asm handler that calls the C

 * routine that actually waits. See arch/i386/kernel/semaphore.c

 */

static inline void down(struct semaphore * sem)

{

    might_sleep();

    __asm__ __volatile__(

       "# atomic down operation\n\t"

       LOCK "decl %0\n\t"     /* --sem->count */

       "js 2f\n"

       "1:\n"

       LOCK_SECTION_START("")

       "2:\tlea %0,%%eax\n\t"

       "call __down_failed\n\t"

       "jmp 1b\n"

       LOCK_SECTION_END

       :"=m" (sem->count)

       :

       :"memory","ax");

}
```

实际的汇编代码形式为。

```
lock   decl [sem->count]
js 2

1:
<========== another section ==========>

2:
lea    [sem->count], eax
call   __down_failed
jmp 1
```

信号量的sem->count一般初始化为一个正整数，申请信号量时执行原子操作decl，将sem->count减1。如果该值减为负数（符号位为1）则跳转到另一个段内的标签2，否则申请信号量成功。

标签2被编译到另一个段内，进入标签2后，执行lea指令取出sem->count的地址，放到eax寄存器作为参数，然后调用函数__down_failed表示信号量申请失败，进程加入等待队列。最后跳回标签1结束信号量申请。

信号量的释放操作由函数up实现。

```
/*

 * This is ugly, but we want the default case to fall through.

 * "__down_failed" is a special asm handler that calls the C

 * routine that actually waits. See arch/i386/kernel/semaphore.c

 */

static inline void down(struct semaphore * sem)

{

    might_sleep();

    __asm__ __volatile__(

       "# atomic down operation\n\t"

       LOCK "decl %0\n\t"     /* --sem->count */

       "js 2f\n"

       "1:\n"

       LOCK_SECTION_START("")

       "2:\tlea %0,%%eax\n\t"

       "call __down_failed\n\t"

       "jmp 1b\n"

       LOCK_SECTION_END

       :"=m" (sem->count)

       :

       :"memory","ax");

}
```

实际的汇编代码形式为。

```
lock   incl sem->count
jle     2

1:
<========== another section ==========>

2:
lea    [sem->count], eax
call   __up_wakeup
jmp    1
```

释放信号量时执行原子操作incl将sem->count加1，如果该值小于等于0，则说明等待队列有阻塞的进程需要唤醒，跳转到标签2，否则信号量释放成功。

标签2被编译到另一个段内，进入标签2后，执行lea指令取出sem->count的地址，放到eax寄存器作为参数，然后调用函数__up_wakeup唤醒等待队列的进程。最后跳回标签1结束信号量释放。

## 内存屏障和Volatile变量

为了提高性能，编译器通常会对汇编级代码进行重新排序以使处理器的流水线尽可能满。在此过程中，编译器可能会优化访存指令，如果其认为此优化不会产生错误数据。但是，编译器无法检测出所有内存无关的操作。如果看起来互相独立的变量实际上相互影响，编译器可能会以错误的顺序更新这些变量，产生错误结果。

内存屏障是非阻塞同步技术，用于内存操作以正确顺序进行。内存屏障就像栅栏，会强制处理器将其之前的内存读取和存储操作完成后，才允许执行其后的内存读取和存储操作。

编译器为了优化程序，可能会将变量的值加载到寄存器，对于local variables没什什么问题。如果是多线程共享变量，可能其他线程无法感知到此变量值的变化。volatile关键字迫使编译器每次都从内存中读取变量的值。如果一个变量的值可能会被外部代码改变而编译器无法检测，则需要加volatile关键字。因为内存屏障和volatile会减少编译器的优化，最好只在需要保证正确性的情况下使用。

内存屏障,也称内存栅栏，内存栅障，屏障指令等， 是一类同步屏障指令，使得CPU或编译器在对内存随机访问的操作中的一个同步点，使得此点之前的所有读写操作都执行后才可以开始执行此点之后的操作。

大多数现代计算机为了提高性能而采取乱序执行，这使得内存屏障成为必须。

语义上，内存屏障之前的所有写操作都要写入内存；内存屏障之后的读操作都可以获得同步屏障之前的写操作的结果。因此，对于敏感的程序块，写操作之后、读操作之前可以插入内存屏障。


这种内存操作的重新排序（读取和存储）在单进程的情况下一般没问题，但是在并发程序或设备驱动会导致不可测的行为。顺序约束与硬件相关，由体系结构的内存顺序模型定义。一些体系结构为强制不同的顺序约束提供了多种屏障。

内存屏障通常用于实现操作多设备共享内存的底层机器代码。例如多处理器系统的同步原语和无锁数据结构，以及与硬件通信的设备驱动。

当程序运行在单CPU机器上时，硬件保证所有内存操作以程序的顺序执行，所以内存屏障没有必要。但是，当内存由多个硬件共享，例如多处理器系统中的其他CPU, or 内存映射外设时，乱序访问可能会导致问题。

例如第二个CPU可能会以与程序不同的顺序看到第一个CPU所执行的内存修改。初始时，内存位置x和f的值均为0。当f为0时，处理器#1上的程序循环，然后输出x的值。 处理器 #2上的程序42存入x，然后将1存入f。

Processor #1:

```
while (f == 0);
// Memory fence required here
print x;
```
 
Processor #2:

```
x = 42;
// Memory fence required here
f = 1;
```
你可能只希望输出42；但是，如果处理器#2的存储操作是乱序执行的，有可能f在x之前被更新，输出语句有可能输入0。同样，如果处理器#1的读取操作是乱序执行的，可能在检查f之前就执行输出语句，输出一个不可测的值。可以在处理器#2的f赋值操作之前加入内存屏障以确保x的值在f之前被更新。另一个内存屏障可以加在处理器#1访问x之前以确保在f的值改变之后才读取x的值。

另一个例子[double-checked locking](http://en.wikipedia.org/wiki/Double-checked_locking).

底层架构特定原语
内存屏障是底层原语，是体系结构内存模型的一部分，类似指令集，不同架构间差别很大，因此无法对内存屏障行为进行概括。正确使用内存屏障需要对硬件的结构手册有足够的了解。以下对现今产品的内存屏障进行介绍。
一些架构，例如x86/x64，提供了若干内存屏障指令，包括一条有时称为"full fence"的指令。full fence保证fence之前的所有存取操作都会先于其后的存取操作完成。其他架构，例如Itanium，提供独立的"acquire" and "release" 内存屏障，分别从reader (sink) or writer (source) 的角度解决read-after-write操作的可见性。一些架构提供独立的内存屏障，以控制系统内存和I/O内存的不同组合的顺序。当有多个内存屏障指令可以使用时，需要注意不同内存屏障的代价相差很大。

多线程编程与内存可见性
参见：[内存模型（编程）](http://en.wikipedia.org/wiki/Memory_model_(programming))
多线程编程通常使用高级编程环境提供的同步原语，例如Java和.NET框架，或API，如POSIX线程或Windows API。原语如mutexes或semaphores用于多线程编程中同步对资源的访问。这些原语一般用内存屏障来实现，需要提供所需内存可见性语义。在这种环境下，一般没有必要显示使用内存屏障。

每个API或编程环境包含自己的高级内存模型，定义了内存可见性语义。虽然程序员一般无需在高级语言环境下使用内存屏障，但需要尽可能了解其内存可见性语义。但是可能因为缺乏说明文档而难以理解内存可见性语义。

正如编程语言语义与机器语言操作码定义在不同的抽象层次上，编程环境的内存模型与硬件内存模型也定义在不同的抽象层次上。特定语言环境的高级内存可见性语义与低级硬件内存屏障语义一般不是简单地对应关系。POSIX线程的特定平台实现可能采用比规定更强的屏障。

乱序执行与编译器重排优化
内存屏障指令只是在硬件层次上解决了乱序问题。为了优化程序，编译器也会重排。虽然导致的结果可能相同，但是通常有必要采用不同的方法禁止编译器对多线程共享数据进行重排优化。注意，这种方法仅对没有同步原语保护的数据有必要。
在C和C++中，volatile关键字使C and C++直接访问memory-mapped I/O。Memory-mapped I/O通常要求源码中的存取以指定的次序没有遗漏得进行。编译器的遗漏或重排会破坏程序与通过memory-mapped I/O访问的设备直接的通信。对于volatile内存地址，C或C++不会重排或忽略对其的存取。关键字volatile并不保证强制cache-consistency的内存屏障。因此仅使用"volatile"对用于线程间通信的变量是不够的。
C11和C++11之前的C和C++标准并没有解决多线程（或多处理器），所以volatile是否有用取决于编译器和硬件。虽然volatile保证volatile存取以源码指定的次序进行，但是编译器会生成代码 (或CPU会重排执行) ，使得volatile存取与non-volatile存取乱序，因此限制了其作为线程间flag或mutex的有用性。这与编译器相关，一些编译器，如gcc不会优化具有volatile和"memory" 标签的in-line assembly code，例如: asm volatile ("" : : : "memory"); (参见compiler memory barrier)。并且由于缓存、缓存一致协议、relaxed memory ordering，并不保证volatile存取从其他处理器或核心看来也是同样的次序。也就是说单独使用的volatile变量，如果作为线程间的标志或者互斥锁，可能根本就是无效的。

某些编程语言和编译器可能提供足够的工具，使得用户可以控制编译器以及硬件对读写操作的重排。Java 1.5中，关键字volatile保证可以避免编译器和硬件对读写操作的重排，这是java 5的新内存模型定义的一部分。C++0x中将会出现一些特别的原子类型和原子操作，具有与Java 5内存模型中的volatile类似的语义。


关于内存屏障更详细的解释
read barriers and write barriers; acquire barriers and release barriers

barriers不是控制"latest"或"freshness"值，而是用于控制内存访问的重排。

Write barriers控制写入次序。因为与CPU的速度相比，写入内存比较慢，因此在“真正写入”内存之前写入会提交到write-request queue。虽然是按序进入队列的，但是在队列中可能会被重排 (因此可能称为“队列”并不合适)，除非使用write barrier 。

Read barriers控制读取次序。因为预读取(CPU会预先读取一块内存) 并且由于写入缓存 (CPU会从write buffer而非内存读取 - 即CPU认为已经写入X = 5，但读取时，会发现在写入缓存中仍等待变成5) ，读取会乱序。

这与编译器的优化无关，'volatile'不会解决这个问题，volatile仅告知cpu从"memory"读取，但并没有告知CPU如何/从何处读取 (即"memory"是从CPU角度理解的memory).

read/write barriers设置block防止read/write队列重排 (read可能不是queue，但是重排的影响是一样的).

什么类型的blocks? - acquire and/or release blocks.

Acquire - eg read-acquire(x) 会将x的读取加入read-queue，并flush the queue (并非真正地flush the queue, 而是添加marker表示不要reorder此marker之前的任何操作，效果如同queue被flush)。而后(代码顺序)读取可以重排，但不是在x的读取之前。

Release - eg write-release(x, 5) 首先会flush (or marker) the queue，然后将write-request加入write-queue。所以之前的写入操作不会在x = 5之后发生，但注意之后的写入操作可能在x = 5之前发生。

注意，read对应acquire，write对应release，但也有可能是不同的组合。

Acquire and Release相当于'half-barriers' or 'half-fences'，仅防止一个方向的重排（读取或写入）。

full barrier (or full fence) 会采取acquire和release - 即没有重排。

对于无锁编程，或者C#或java 'volatile'，真正需要的是read-acquire and write-release.

即

void threadA()
{
   foo->x = 10;
   foo->y = 11;
   foo->z = 12;
   write_release(foo->ready, true);
   bar = 13;
}
void threadB()
{
   w = some_global;
   ready = read_acquire(foo->ready);
   if (ready)
   {
      q = w * foo->x * foo->y * foo->z;
   }
   else
       calculate_pi();
}
这段代码仅仅是为了说明barrier，实际上使用锁会更安全。

After threadA() is done writing foo, it needs to write foo->ready LAST, really last, else other threads might see foo->ready early and get the wrong values of x/y/z. So we use a write_release on foo->ready, which, as mentioned above, effectively 'flushes' the write queue (ensuring x,y,z are committed) then adds the ready=true request to the queue. And then adds the bar=13 request. Note that since we just used a release barrier (not a full) bar=13 may get written before ready. But we don't care! ie we are assuming bar is not changing shared data.

Now threadB() needs to know that when we say 'ready' we really mean ready. So we do a read_acquire(foo->ready). This read is added to the read queue, THEN the queue is flushed. Note that w = some_global may also still be in the queue. So foo->ready may be read before some_global. But again, we don't care, as it is not part of the important data that we are being so careful about. What we do care about is foo->x/y/z. So they are added to the read queue after the acquire flush/marker, guaranteeing that they are read only after reading foo->ready.

In my threadA/B example, we want to ensure that foo->x,y,z is written before foo->ready (otherwise someone might see 'ready == true' before foo was actually ready). On the reading side, you don't want to read x,y,z before it is ready, so you need read_acquire on foo->ready to ensure that the CPU doesn't reorder x,y,z reads before 'if (foo->ready)'. 

Note also, that this is typically the exact same barriers used for locking and unlocking a mutex/CriticalSection/etc. (ie acquire on lock(), release on unlock() ).

So,

I'm pretty sure this (ie acquire/release) is exactly what MS docs say happens for read/writes of 'volatile' variables in C# (and optionally for MS C++, but this is non-standard). See http://msdn.microsoft.com/en-us/library/aa645755%28VS.71%29.aspx including "A volatile read has "acquire semantics"; that is, it is guaranteed to occur prior to any references to memory that occur after it..."

I think java is the same, although I'm not as familiar. I suspect it is exactly the same, because you just don't typically need more guarantees than read-acquire/write-release.

And lastly, note that lock-free programming and CPU memory architectures can be actually much more complicated than that, but sticking with acquire/release will get you pretty far.


## 锁

锁用于保护临界区代码，锁的类型包括：

|Lock|Description|
|--|--|
|Mutex|只允许一个线程同时获取，也就是同时只允许一个线程进入临界区，其他线程会挂起，等待holder释放Mutex|
|Recursive lock|Recursive lock是Mutex的变种，允许一个线程在释放之前多次获取，其他线程阻塞直到此线程释放同样的次数，可用于递归迭代，也可以用于多个函数分别获取锁的情况|
|Read-write lock|shared-exclusive lock，适用于读多写少的情况。没有写者时，读者可以同时执行读操作；写者需要阻塞等待所有的读者释放锁；读者需要阻塞等待所有写者释放锁|
|Distributed lock|分布式锁进程级别的互斥访问。不同于mutex，分布式锁不阻塞进程。在无法获取锁时由进程决定是否继续。|
|Spin lock|spin lock在无法获取锁时会重试直到获取锁，适用于等待锁的时间较小的多处理器系统，在这种系统中，重试比阻塞线程更有效，因为阻塞线程会导致上下文切换和线程数据结构的更新|
|Double-checked lock|Double-checked lock是为了解决获取锁前需要检测获取条件的损耗，但是这种锁不是很安全，尽量不要使用|
|RCU||

注意：大多数的锁包含内存屏障以保证进入临界区之前所有存取指令已经执行完成。

## Conditions
另一种信号量，当条件成立时，允许signal其他线程。Conditions通常用于告知资源可用或确保任务以特定的次序完成。当线程检测condition时, 如果condition非true，线程就会阻塞直到其他线程改变condition。condition与mutex的不同之处在于允许多个线程获取condition。

## 无锁编程

## CAS

## 比较

A memory barrier is a method to order memory access. Compilers and CPU's can change this order to optimize, but in multithreaded environments, this can be an issue. The main difference with the others is that threads are not stopped by this.
A lock or mutex makes sure that code can only be accessed by 1 thread. Within this section, you can view the environment as singlethreaded, so memory barriers should not be needed.
a semaphore is basically a counter that can be increased (v()) or decreased (p()). If the counter is 0, then p() halts the thread until the counter is no longer 0. This is a way to synchronize threads, but I would prefer using mutexes or condition variables (controversial, but that's my opinion). When the initial counter is 1, then the semaphore is called a binary semaphore and it is similar to a lock.
A big difference between locks and semaphores is that the thread owns the lock, so no other thread should try to unlock, while this is not the case for semaphores.
