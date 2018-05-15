---
layout: post
title: "Consensus Algorithms"
modified:
categories: blog
excerpt:
tags: [Consesus, Paxos, Zab, Raft, Viewstamped Replication]
comments: true
share: true
counter: true
image:
  feature:
date: 2016-05-03T10:24:19+08:00
---

## Consesus Algorithms

一致性算法常用在数据库事务提交、选主、状态机复制、原子广播等。

## paxos vs zab vs raft

### 参考资料

|协议|英文原版|中文注解版|参考源码|
|---|---|---|---|
|paxos|[The Part-Time Parliament][lamport-paxos] | [paxos]({{ site.url }}/images/blog/consensus_algorithms/lamport-paxos.pdf) |[libpaxos](https://bitbucket.org/sciascid/libpaxos.git)|
|zab | [A simple totally ordered broadcast protocol][zab] | | |
|raft| [In Search of an Understandable Consensus Algorithm (Extended Version)][raft] | [raft]({{ site.url }}/images/blog/consensus_algorithms/lamport-paxos.pdf) | |
|VR  |[Viewstamped Replication Revisited][VR] | | |

说实在的，lamport的原版论文不难理解。虽然大多数说法是lamport用了paxos的隐喻导致原版论文难以理解，但是每个人看问题的角度不一样，而且，原版论文其实比多数翻译要读起来顺畅多了，总体花费的时间更少才是。

在原版论文上做的笔记，有对单个问题点的解析，也有横向算法的比较，应该对你有实际的帮助。最好将这几篇论文对照看下。

### 算法比较

1. paxos的论文刚开始隐喻了paxos小岛，其实在论文的single-decree parliament之前，根据对paxos的parliament策略叙述的时候，就已经交代了整个paxos算法的大格局。原文在提出三个约束条件的后面会有一段证明，这段证明也没那么难，看懂了，对于理解paxos算法还是很有帮助的。

    paxos是每个点（除了观察者之类特殊点）都可以提议，也就是多点提议，同时进行；而且每个点同时提出的提议也可以是多个，比如点A提出了1，2两个提议，那么提议2可以在提议1之前被通过，然后提议1才通过，这个在paxos里是可以的，至于为何这样都不会破坏不一致，还是去看原版论文。

2. zab的论文比paxos的偏实际一些，毕竟zab算法本身就偏实际一些，选主以后，leader进行提议。看懂了paxos，看zab就是小菜一碟了。看zab的时候侧重于实现，所以最好结合zookeeper的源码看，zookeeper选主部分的代码还是比较容易跟进去的，但是进行提议的时候（write操作）会有多个Processor，这几个processor是级联的，这儿看代码可能会有些晕（有点多级回调的意思），但是多看几遍还是可以的。

    需要注意的是，zab这种简化的算法，即使是leader，同时也只能有一个提议已经发出，而没有得到确定，也就是in-flight（网络中）的提议只有一个（对于paxos的单点也可以同时发出多个提议）。

3. 看懂zab以后，raft简直就是不能再简单了，只是把zab很多实现（没有写到zab论文的）用论文的方式表现出来了（画了很多图，结构等），帮助你理解。

    之所以前面要看zab的源码实现，就是因为raft跟zab很像。raft论文里基本是跟paxos在对比，与zab比较起来，也有一些细微的不同，但个人觉得，zab更优秀，看完这些论文就能体会出来，raft为了使得算法容易理解，牺牲了一些zab里的优化。

4. Viewstamped Replication (VR) 这篇可以稍微看看，zab和raft里都提到了这个算法。

[lamport-paxos]: http://research.microsoft.com/en-us/um/people/lamport/pubs/lamport-paxos.pdf

[zab]: http://diyhpl.us/~bryan/papers2/distributed/distributed-systems/zab.totally-ordered-broadcast-protocol.2008.pdf

[zab-theory-practice]: http://www.tcs.hut.fi/Studies/T-79.5001/reports/2012-deSouzaMedeiros.pdf

[raft]: https://ramcloud.atlassian.net/wiki/download/attachments/6586375/raft.pdf

[VR]: http://pmg.csail.mit.edu/papers/vr-revisited.pdf


### 其他算法

还有很多其他同步的算法，但有区别于上面的consensus算法，比如ad-hoc consensus策略，或者分布式事务里要求同步到所有节点。

### [Raft真的优于其他算法吗](https://www.quora.com/If-Raft-is-as-good-as-the-papers-claim-why-do-Zookeeper-and-others-implement-other-consensus-algorithms-Why-not-use-Raft)

Zookeeper development started in 2007, while the first drafts of the Raft algorithm were published in 2013. That said, Zookeeper’s Zab algorithm is actually fairly similar to Raft at a high level. It is not quite as simple as Raft, but it already works well and is supported by its own proof of correctness. Any simplicity advantage of replacing Zab with Raft in Zookeeper would be vastly outweighed by the years of work needed to implement, optimize, test, and mature a new algorithm.

However, the story for MongoDB is quite different. MongoDB implements a set of ad-hoc consensus strategies that don’t come with formal proofs and, in practice, fail to provide the guarantees that they claim. Replacing this with something like Raft would be an important improvement, and some developers are working on this, but it’s unclear if this work will be merged upstream.

This sounds really embarrassing for the MongoDB developers—and it should—but MongoDB is not at all an isolated case. If you actually apply rigorous tests to almost any software other than Zookeeper that claims to provide distributed consensus, you find that it doesn’t work. (Even for software that claims to be based on a Raft implementation.)

The moral is that distributed consensus, like secure cryptography, is a really complicated problem that programmers can’t just code their way out of without turning to the academic literature. Formal proofs are tangibly important in practice. Hopefully the simplicity and understandability of Raft will promote improvement in this area; it provides an excellent theoretical foundation. But for now it seems the only way to build a reliable distributed system is to just use Zookeeper.