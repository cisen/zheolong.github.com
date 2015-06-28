---
layout: post
title: "Error Codes or Exceptions"
modified:
categories: blog
excerpt:
tags: []
image:
  feature:
date: 2015-06-28T16:59:52+08:00
---

本文观点非原创，多数来自[DAMIEN KATZ的博客](http://damienkatz.net/2006/04/error_code_vs_e.html)

原文标题为Error codes or Exceptions? Why is Reliable Software so Hard?

## 就开个头，别紧张

很少有软件完全正确地进行错误处理，即使很多关键的后端程序也会在高负载的情况下崩溃，而用户程序也只处理了一些常见错误（比如，http请求超时），但是却没有处理其他情况（分配失败，错误数据，I/O错误，文件丢失等）。

这些错误却会造成很严重的后果，比如浏览器崩溃，你在网页上编辑到一半的文档丢失。

就因为将errcode或exception用错了地方吗？为何简单的错误会导致整个软件崩溃？软件的可靠性必须靠软件的完美才可以实现吗？

并不是错误的处理会很难，而是很多错误我们根本没办法处理，比如如何处理内存分配失败？没有办法处理，只是希望这种错误不要造成灾难性的后果。

这个问题不是如何在程序中传递错误信息这种问题了，而是错误产生的根源。

## 遇到危险闪远点

一个操作失败，后面的程序都不执行。这就是异常的方式，不用每一步都写错误检查，异常发生时，当前例程自动（routine）退出，上层调用者捕捉异常并处理，或者传递至上一层。

```
void DoIt() {
	// An exception in Foo means
	// Bar doesn't get called
	Thing thing = Foo();
	Bar(thing);
}
 
Thing Foo() {
	if (JupiterInLineWithPluto) {
		throw new PlanetAlignmentException();
	}
	return new Thing();
}
```

对于这种错误处理方式，可能需要在退出之前释放一些已经申请的资源，或者关闭文件、socket。JAVA中使用finally，C#中使用using，c++中使用栈变量和RAII。

```
void DoIt() {
	Thing thing = Foo();
	thing.CreateTempFiles();
	try {
		Bar(thing);  
		Baz(thing);
	} finally {
		// This gets called regardless
		// of exceptions in Bar and Baz.
		thing.DeleteTempFiles(); 
	}
}
```

为了简化错误处理，我们假设需要将软件恢复到默认状态，这就丢失了目前的所有状态。

## 别急着返回，还有另一条路

有的错误并非exceptional，而是可以预测执行另一个分支的。比如发送请求失败，可以将数据备份下一次发送，或者发送到备份地址，这种情况更适合使用“if”或“switch”，而不是“try/catch”。

Error codes:

```
if (DeliverMessage(msg, primaryHost) == FAILED) {
	if (DeliverMessage(msg, secondaryHost) == FAILED) {
		PutInFailedDeliveryQueue(msg);
	}
}
```

Exceptions:

```
try {
	DeliverMessage(msg, primaryHost);
} catch (FailedDeliveryException e) {
	try {
		DeliverMessage(msg, secondaryHost);
	} catch (FailedDeliveryException e2) {
		PutInFailedDeliveryQueue(msg);
	}
}
```

如果是使用状态码，那么这种处理跟一般的程序没什么区别。

## 原路返回，还要把脚印都擦掉

有些错误处理需要undo以前的操作，如何回滚状态？如何保存以前的状态？如果需要保存的数据非常复杂该怎么办？如果其他进程或例程已经感知到新的状态并且进行了某种操作怎么办？如果回滚过程中产生新的错误怎么办？

这种情况下，错误处理可能比正常的程序逻辑还要复杂，所以最好别使程序设计陷入这种逻辑。

## OO
OO可以解决这种问题吗？OO在很多情况下类似现实世界，但是OO可以使创建的程序更可靠吗？

举个例子，你去图书馆找书，是直接去找书架，还是现在旁边的电脑上搜索一下？

为何要如此模拟现实世界，而不是按照程序本来的思想去完成任务？况且OOP还会带来继承的麻烦。

那么问题出在OO上吗，不是，OO思想本身就会有这种问题，但不是上述问题的根源。

根源的问题还是，如何比较容易得回复到以前的状态。

有没有语言解决了这个问题？ PHP

PHP？这是个玩笑嘛？ NO

新的请求到达服务端，不会因为上次的处理错误而受影响（文件操作除外，数据库操作只要是放在一个事务里就行）。

Java/C++/VB/Ruby/Python也可以像PHP这样运行，但是如果涉及到保存在内存中的数据，那么情况还是和以前一样。

## Don't Undo Your Actions, Just Forget Them

### Make a Copy of Everything Up Front

对要修改的原始数据备份，在对备份完成操作后，将其与原始数据进行swap。
虽然比较耗存储，但是简单有效。

### Immutable Objects

例如Java里的String，只能创建新的，而无法修改旧的，但是String是比较简单的类型。

c++支持const，但是也是在尝试修改的时候提醒我们，并没有使得创建这种程序更简单，对于复合类型更是难上加难。

假设我们有一个house，里面有bathroom，bathroom里有toilet，以此类推。我们需要clean每个object，下面是classic, mutable-object implementation

```
void DoIt(House house) {
	...
	house.Clean();
	...
}
 
class House {
	Bathroom bathroom;
	Bathroom bedroom;
	...
	void Clean() {
		bathroom.Clean();
		bedroom.Clean();
		...
	}
}
 
class Bathroom {
	Toilet toilet;
	Mirror mirror;
	...
	void Clean() {
		toilet.Flush();
		mirror.Clean();
		...
	}
}
 
class Toilet {
	int poops;
	...
	void Flush() {
		poops = 0;
	}
}

```

immutable版本如下

```
void DoIt(House house) {
	...
	house = house.Clean();
	...
}
 
class House {
	Bathroom bathroom;
	Bedroom bedroom;
	...
	House Clean() {
		// make a new copy of the house
		// with the cleaned contents
		house = new House ;
		house.bathroom = bathroom.Clean();
		house.bedroom = bedroom.Clean();
		...
		return house;
	}
}
 
class Bathroom {
	Toilet toilet;
	Mirror mirror;
	..
	Bathroom Clean() { 
		// make a new copy of the bathroom
		// with the cleaned contents
		bathroom = new Bathroom;
		bathroom.toilet = toilet.Flush();
		bathroom.mirror = mirror.Clean();
		...
		return bathroom;
	}
}
 
class Toilet {
	int poops;
 
	Toilet Flush() {
		// make a new copy of the toilet
		// with no poop
		Toilet toilet = new Toilet;
		toilet.poops = 0;
		return toilet;
	}
}
```

第二个版本更加robust，不会造成half-cleaned状态，但是也更加复杂。

### Keep Object Mutation to a Single Operation

尽可能隔离操作，使得会出错的操作集中在一个操作里，尽可能进行“原子”操作。

### Use a Functional Language

无副作用是函数式语言最重要的特点，LISP、Haskell、Erlang，lamda是必须要了解的，可以不了解monads。

Erlang是动态的，并且是“scripty”，其伟大之处就是将immutability, messaging, pattern matching, processes and process hierarchy这些概念协调起来，使得通过遵守几种简单的设计原则就可以实现严格的并发和可靠性。

## 到底说明了什么

不要使程序处于未定义状态（例如，半初始化），在某些情况下可以回滚，但是大部分情况下应尽可能使用“原子”操作，避免Mutation（destructive updates），尽可能得使用“遇到危险闪远点”的策略。








