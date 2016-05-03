---
layout: post
title: "Zookeeper and Zab"
modified:
categories: blog
excerpt:
tags: [ZooKeeper, Zab]
comments: true
share: true
counter: true
image:
  feature:
date: 2016-04-12T21:53:52+08:00
---

本篇意在探究ZooKeeper实现原理，并非一篇使用手册。重点内容为Zab协议的原理（论文）以及其在ZooKeeper中的实现。

## [什么是ZooKeeper](https://cwiki.apache.org/confluence/display/ZOOKEEPER/Index)

ZooKeeper是一个集中式服务，用于保存配置信息、命名，提供分布式同步和组服务（group services）。很多分布式应用中都会用到这些服务，每次实现这些服务，都需要修复很多bug，并且无法避免竞态条件（race condition）。因为实现这些服务非常困难，所以很多应用选择绕开它们，使得应用难以管理，并且不易扩展。即使实现得没有问题，这些服务的不同实现也会使得对应用部署的管理异常困难。

ZooKeeper意在将这些不同的服务抽离成一个集中式协调服务的简单接口。该服务本身是分布式并且高可靠。实现了Consensus、组管理（group management）和存在协议（presence protocols），应用本身就不需要实现这些了，只需要利用ZooKeeper的组件和应用特定的情况结合即可。

## [ZooKeeper概述](https://cwiki.apache.org/confluence/display/ZOOKEEPER/ProjectDescription)

ZooKeeper是通过znode组成的共享的**层次性命名空间**来同步分布式应用的，很像文件系统。与常见文件系统不同的是，ZooKeeper具有对znode进行高吞吐、低延迟、高可用性、**严格有序**访问的特性。ZooKeeper的高性能使得其可以使用在大型分布式系统中，高可靠性使得大型系统避免单点故障问题，而严格有序使得客户端可以实现精确的同步原语。

ZooKeeper提供的命名空间很像标准的文件系统。命名就是用斜杠“/”分隔的一系列路径元素。ZooKeeper命名空间中的每个znode都是由一条路径表示。每个znode有一个父节点，其路径就是该znode路径的前缀；只有根节点“/”没有父节点。如同标准的文件系统，znode如果有子节点也无法删除。

ZooKeeper和标准文件系统的主要不同点是，znode可以具有相关联的数据（每个文件都是目录，反之亦然），znode所包含的数据是有限的。ZooKeeper是用来存储协调数据的：状态信息、配置、位置信息等。这种**元信息**通常都是以B或KB为单位。ZooKeeper内部设置了是否超过1M的检查，防止被用来存储大的数据。

![image]({{ site.url }}/images/blog/zookeeper/zookeeper-architecture.png)

服务本身是在一组机器上复制的，这些机器保持了数据的**内存快照**，并将**事务日志**（transactoin logs）和**快照**（snapshots）保存在**持久性介质**中。因为数据保持在内存中，ZooKeeper能够获得很高的吞吐量和较低的时延。内存数据库的缺点是所能管理的数据受限于内存大小，这是要保持znode所存数据尽量少的另一个原因。

组成ZooKeeper服务的所有机器都知道所有机器的地址。只要多数服务器可用，ZooKeeper服务就可用。客户端也必须知道服务器列表，并使用这个列表建立ZooKeeper服务的句柄。

客户端只连接到一个ZooKeeper服务器。客户端保持**TCP连接**，用于发送请求，接收响应，获取watch事件，发送**心跳包**。如果与服务端的TCP连接断开，客户端会连接另一个服务器。当客户端第一次连接ZooKeeper服务时，第一个ZooKeeper服务器会为客户端建立一个**会话**（session）。如果客户端需要连接到另一个服务器，会与新服务器重建此会话。

Read请求会在客户端连接到的服务器本地处理。如果通过read请求对zonde设置watch，也是在ZooKeeper服务器本地监测的。Write请求会被转发到其他服务器，通过consensus以后才能产生响应。Sync请求也会被转发给另一个服务器，但是不会经过consensus。所以，服务器越多，read请求的吞吐量会越高，write请求的吞吐量会越低。

顺序性对ZooKeeper来说是很重要的；几乎就是强迫症了。所有update都是完全顺序的。ZooKeeper实际上会用一个反映顺序的数字标记每个update，我们称此数字为**zxid**（ZooKeeper Transaction Id）。每个update都会有**唯一**的zxid。Read（和watch）会参照update的顺序。处理read请求的服务器会根据其最后处理的zxid对read响应进行标记。

## [Zab](https://cwiki.apache.org/confluence/display/ZOOKEEPER/Zab)

关于Zab，有两篇论文可以参考，2008年的“[A simple totally ordered broadcast protocol][zab]”和2012年的“[ZooKeeper’s atomic broadcast protocol: Theory and practice][zab-theory-practice]”，前者从理论上解释了Zab协议要满足什么需求，为何需要发明Zab协议而不用其他协议（主要对比Paxos），协议的概述（两个状态）；后者是理论到实践，给出了关键过程的伪代码，介绍了详尽的实现细节。

### [A simple totally ordered broadcast protocol][zab]

注意：此部分对照原版英文论文去看更好，翻译本身无法达到原版的流畅度。

#### 翻译用的术语

* deliver 递交（客户端已经可以看到这条消息的结果）
* propose 提出（leader接收到消息，记录日志，并发出消息给其他quorum成员，等待ack）

#### ABSTRACT

本文是对ZooKeeper使用的一种完全有序广播协议——Zab协议的概述。从理论上来说，Zab很容易理解，也很容易实现，并且性能很高。在本文中，我们会给出ZooKeeper对Zab协议的需求，如何使用Zab协议，以及Zab协议是如何工作的。

#### Introduction

在Yahoo!公司，我们开发了一种高性能、高可用的协调服务——ZooKeeper，很多大型应用可以利用ZooKeeper进行协调任务，例如**选主**（leader election）、**状态传播**（status propagation）和**集合**（rendezvous）。此服务实现了一种层次空间的数据节点——znode，客户端可以利用znode实现协调任务。我们发现此服务很容易扩展性能，能够满足Yahoo!的线上大规模（web-scale）关键应用的要求。ZooKeeper没有使用锁（locks），而是实现了一种**无等待（wait-free）共享数据对象**，并且严格保障对这些对象的**顺序性**操作。客户端利用这种保障实现各自的协调任务。通常，ZooKeeper的一个主要前提是对于应用来说，update的顺序性比其它协调技术（例如，**阻塞**）更重要。

为了满足这些需求，ZooKeeper采用了一种**完全有序**的广播协议（totally ordered broadcast protocol）：Zab。在实现我们的客户端保障时，完全有序的广播是很重要的；并且在每个服务器上保持ZooKeeper状态的**副本**（replicas）也是有必要的。这些副本通过完全有序的广播协议来保持一致，例如**复制状态机**（replicated state-machines）。本文关注点在于ZooKeeper对这种协议的需求及其实现的概述。

一般ZooKeeper集群包含3至7台机器，虽然从设计角度来讲可以支持更多的机器，但是这个规模已经提供所需的性能和冗余。ZooKeeper集群如果有2f+1个机器，可以容忍f个机器的服务崩溃。

因为应用对ZooKeeper的使用很密集，并且同时有数十个或数千个客户端并发请求，所以需要很高的吞吐。设计ZooKeeper是为了应对读写比大于2:1的场景；但是ZooKeeper的写入吞吐也很高，所以也可以用于读写比较低的场景。ZooKeeper的read请求是在本地处理（不经过quorum），所以read的吞吐量可以随着服务器数的增加而增加。write的吞吐量却会受到广播协议吞吐的限制，所以需要广播协议具有高吞吐。

![Figure 1]({{ site.url }}/images/blog/zookeeper/zab-article-figure-1.png)

#### Requirements

对于广播协议，ZooKeeper有以下需求：

* **可靠递交（Reliable delivery）**：如果消息m被一台服务器递交，那么最终会被其他正常的服务器递交。（这里的递交指的是递交给客户端）
* **完全有序（Total order）**：如果消息a在消息b之前被一台服务器递交，那么每个服务器都应该在递交消息b之前递交消息a。
* **因果有序（Causal order）**：如果消息a在因果关系上先于消息b，那么消息a在顺序上必须先于消息b。

为了正确性，ZooKeeper还需要前缀属性：

**前缀属性（Prefix property）**：如果leader L递交的最后一条消息是m，那么leader L在m之前提出（propose）的消息也必须已经递交。

注意，一个进程可以多次被选为leader，但是为了保证前缀属性，每次必须看作新的leader。（因为propose的消息未必会被最终commit，如果不看作新的leader，那么就会违背前缀属性）

有了这三条保障，就可以维护ZooKeeper数据库的正确副本。

1. 可靠递交和完全有序保证了所有副本的状态一致。
2. 因果有序保证了从使用Zab的应用角度来看，副本的状态是一致的。
3. leader根据接收到的请求来对数据库进行更新。

Zab考虑了两种因果有序：

1. 如果两条消息a和b从同一个server发送，消息a在消息b之前被提出，我们称消息a在因果关系上先于消息b；
2. Zab假设同时只有一个leader可以commit提议。如果leader变了，之前提出的消息在因果关系上先于新leader提出的消息。

我们的故障模型是crash-fail with stateful recovery。不假设具有同步的时钟，但是假设服务器看到的时间都以几乎一样的速率流逝（我们用timeout来检测故障）。组成Zab的进程具有持久化的状态，因此进程可以在故障后重启，并从持久化的状态中恢复。这意味着进程可能具有部分有效的状态，例如缺少很多最新的transaction，或者更麻烦的是，如果有未递交的transaction，需要删除。

我们保证能应对f个服务器故障的情况，但是也要处理其他的相关可恢复性故障，例如，断电。为了从这些故障中恢复，我们需要在消息被递交前，将其记录在组成quorum的服务器磁盘上。（因为非技术的、务实的、面向运维的原因，在我们的设计中没有包含UPS设备、冗余/专用网络设备、NVRAM诸如此类的设备。）

虽然没有假设Byzantine故障，但是我们通过摘要（digest）来检测数据损坏（data corruption）。我们也在协议数据包里增加了额外的元数据，用于完好性检查（sanity check）。如果检测到数据损坏或完好性检查失败，那么我们会放弃服务器处理。

运行环境的幂等实现和协议自身的实际问题，使得对于我们的应用难以实现完全的Byzantine-tolerant系统。达到真正的幂等实现是很难的，不只是编程资源的问题。目前，大部分的运行问题，都是实现的bug或者是其他非实现问题，例如，网络配置错误。

ZooKeeper使用in-memory数据库，并且将transaction log和定期的snapshot写入磁盘。ZooKeeper的transaction log也作为数据库的write-ahead transaction log，所以transaction仅被写入磁盘一次。因为数据库是内存型的，并且我们使用千兆网卡，那么瓶颈就在写入时的磁盘I/O。为了减轻磁盘I/O瓶颈，我们会对transaction进行批量写入。这种批量发生在副本而非协议层，所以其实现更接近数据库的group commit，而非message packing。我们选择不采用message packing来降低延迟，同时仍可以通过批量磁盘I/O获得packing的好处。

crash-fail with stateful recovery模型意味着，当服务器恢复时，它会读取snapshot，并重现此后已经递交的transaction。所以在恢复期间，原子多播（atomic broadcast）不需要保证至多一次递交。我们采用幂等transaction意味着只要保持了重启顺序，transaction的多次递交也没有关系。这是完全有序的一种妥协。具体来说，如果a在b之前被递交，那么故障之后，a被重新递交，b会在a之后被递交。

其他性能需求：

* 低延迟
* 突发性高吞吐
* 平滑的故障处理

#### Protocol

Zab包含两种模式：recovery和broadcast。当服务启动或leader故障后，Zab变成recovery模式。当出现leader，并且一个quorum的服务器已经与leader同步，那么recovery模式结束。同步状态包括保证leader与新服务器具有相同的状态。

一旦leader具有一个quorum的同步follower，就会开始广播消息。只有leader可以通过初始化广播协议来执行广播，其他不是leader的服务器需要把请求转发给leader。将从recovery模式中选出的leader同时作为处理写请求和协调广播协议的leader，我们消除了将消息从写请求leader转发到广播协议leader的延迟（还有将写请求leader和广播协议leader分开的设计？）

如果leader还在广播消息时，一个Zab服务器上线，此服务器会以recovery模式启动，发现leader并与之同步，并且开始参与消息广播。服务处于broadcast模式，直到leader故障或不再具有一个quorum的follower。任何quorum的follower都足以使得leader和服务保持活跃（active）。例如，由三个服务器组成的Zab服务，其中一个是leader，其它两个是follower，服务状态会变成broadcast模式。如果其中一个follower故障，因为leader仍具有一个quorum，所以服务不会中断断。如果此follower恢复了，而另一个follower故障，也不会导致服务中断。

#### Broadcast

![Figure 2]({{ site.url }}/images/blog/zookeeper/zab-article-figure-2.png)

原子多播服务运行时使用的协议，称为broadcast模式，类似于简单的2PC（two-phase commit）：leader提出请求，收集投票（vote），最后提交（commit）。图2示出了协议的消息流。我们可以简化2PC是因为我们没有abort操作；follower要么回应请求，要么拒绝leader。没有abort操作意味着只要一个quorum的服务器回应了提议，就可以commit，不需要等待所有的服务器回应。但是简化的2PC自身无法处理leader故障的问题，所以需要加入recovery模式以处理leader故障。

广播协议采用FIFO（TCP）通道（channel）。使用FIFO通道，使得保持顺序性非常容易。消息在FIFO通道中是顺序投递的；只要按照投递的顺序进行处理，那么就可以保证顺序性。

leader会为想要递交的消息广播一个提议。在提出消息前，leader会给其分配一个单调递增的唯一id，称为zxid。因为Zab保证因果顺序，所以递交的消息也会按zxid有序。广播过程会将消息的提议放入为了每个follower建立的FIFO通道里，等待被发送给follower。当follower收到提议时，先将其写入磁盘，如果可以就先批量，只要提议已经落盘，马上给leader发送ACK。当leader收到一个quorum的ACK，leader会广播COMMIT，并在本地递交消息。当follower收到COMMIT以后就递交消息。

注意，如果follower将ACK广播给其他follower，那么leader可以不发送COMMIT。这种改变不但会加重网络负载，也会需要全连通的通信网络，而不是简单的星型拓扑，从管理TCP连接的角度看，星型拓扑更简单。在客户端保持这个通信网络图并跟踪ACK在我们的实现中也会非常麻烦。

#### Recovery

这个简单的广播协议工作得很好，直到leader故障或者失去了一个quorum的follower。此时，有必要通过一个recovery过程来选取新的leader，并将所有服务器带到一个正确的状态。对于leader选举，我们需要一种算法，选举成功的概率比较大。leader选举协议不仅需要leader学习到自己是leader，也需要一个quorum同意这个决定。如果选举阶段错误地结束，服务器将无法进行下一步操作，最终会超时，并重新开始选举。在我们的实现中，有两种不同的leader选举实现策略。如果存在一个quorum的正常服务器，最快的选举策略会在几百毫秒内完成选举。

recovery过程的复杂性部分在于，某个时刻，大量的提议还在网络中传输。in-flight提议的最大数量可以配置，但是默认是100个。为了这个协议在leader故障的情况下正常运转，需要保证两点：不能忘记已经递交的消息，需要忽略已经被跳过的消息。

在一个服务器上被递交的消息必须最终被所有机器递交，无论这个机器是否故障。如果leader递交了消息，然后就挂了，而其他服务器都没有收到COMMIT。因为leader已经递交了该消息，那么某个客户端可能已经看到了该消息中的transaction产生的结果，那么这个transaction最终必须被其他服务器递交，才能保证客户端看到服务的一致状态。

![Figure 3]({{ site.url }}/images/blog/zookeeper/zab-article-figure-3.png)

![Figure 4]({{ site.url }}/images/blog/zookeeper/zab-article-figure-4.png)

相反的，跳过的消息必须被忽略。如果leader产生一个提议，而在其他服务器接收到这个提议前，leader挂了。例如，在图3中，其他服务器都没有看到提议3，所以在图4中，当服务器1恢复后，需要丢掉提议3。如果服务器1成为新leader，并在消息100000001和100000002之后提交3，那么就会违背顺序性保障。

记录已经递交的消息是通过对leader选举协议的简单改进来实现的。如果leader选举协议保证新的leader具有一个quorum的服务器中最高的提议号（proposal number），那么最新选举的leader就会包含所有已经提价的消息。在提议任何新的消息之前，新选举的leader会首先保证其transaction log里所有的消息都被一个quorum的follower递交。注意，使得新leader具有最高的zxid是一种优化，这样新的leader就不需要从一组follower中找出谁的zxid最高，然后从该follower获取丢失的transaction。

所有正常工作的服务器要么是leader，要么是在following一个leader。leader保证其follower看到所有提议，并且递交所有已经提交的提议。为了实现这种保证，leader需要为每个新连接的follower保存其未接收到的PROPOSAL在队列里，并保存这些提议对应的COMMIT（直到最后提交的消息）到队列中。当所有这些消息已经被放入队列后，leader就将此follower加入广播列表，用于未来的PROPOSAL和ACK。

跳过已经提议但是未递交的消息也很容易。在我们的实现中，zxid是一个64位数字，其低32位用作简单的计数器。每个提议都会增加该计数器。高32位是epoch。每次选举出新的leader，它就会从最新的zxid中获取epoch，增加epoch，然后使用此epoch和置为0的计数器组成的zxid。使用epoch来标记leadership的更替，并且对于此epoch，需要一个quorum的服务器认同一个服务器为leader，这样可以防止多个leader发出了zxid相同的提议。这种方案的优势在于我们可以跳过leader故障期间的实例，然后加速并简化recovery过程。如果曾经挂掉的服务器重启启动，其包含一个未递交的提议，epoch是先前的，那么它不会成为新leader，因为每个可能的quorum都有更新epoch的提议，所以zxid也更高。当该server连接作为follower时，对于follower最新提议的epoch，leader检查该epoch对应的最新提交的提议，并告知follower将其transaction log（即，忘记）截断到此epoch对应的最后提交的提议。

## ZooKeeper中的Zab源码分析

此部分直接使用了ZooKeeper在Github上trunk分支的代码，如果后续有更多改进，只需要关注关键部分代码即可。

我们只关注Zab的两个主要过程：recovery和broadcast。当leader故障（没有leader也算）或者失去了一个quorum的follower，就会进行recovery过程，包括选举leader和获取一个quorum的follower并使之与leader同步，随后就是正常的broadcast过程，类似于简单的2PC（无abort操作）。

### leader election

我们一路跟踪代码下去即可，不用考虑其他太多的代码分支，大概知道意思即可。

1 ./src/java/main/org/apache/zookeeper/server/quorum/QuorumPeerMain.java

```java
quorumPeer.start()
```

2 ./src/java/main/org/apache/zookeeper/server/quorum/QuorumPeer.java

```java
@Override
public synchronized void start() {
    if (!getView().containsKey(myid)) {
        throw new RuntimeException("My id " + myid + " not in the peer list");
     }
    loadDataBase();
    startServerCnxnFactory();
    try {
        adminServer.start();
    } catch (AdminServerException e) {
        LOG.warn("Problem starting AdminServer", e);
        System.out.println(e);
    }
    startLeaderElection();
    /* 主要过程就在这里，因为QuorumPeer继承了
       ZooKeeperThread，所以此处调用的其实是
       QuorumPeer的run()函数 */
    super.start(); 
}
```


3 ./src/java/main/org/apache/zookeeper/server/quorum/QuorumPeer.java

```java
@Override
public void run() {
    
    ...
    
    try {
        /*
         * Main loop
         */
        while (running) {
            /* Server的状态一共四种：LOOKING, FOLLOWING, LEADING, OBSERVING，
            刚启动时为LOOKING状态 */
            switch (getPeerState()) {
            case LOOKING:
                LOG.info("LOOKING");
	
                if (Boolean.getBoolean("readonlymode.enabled")) {
                    LOG.info("Attempting to start ReadOnlyZooKeeperServer");
	
                    ...
                    
                } else {
                    try {
                       reconfigFlagClear();
                        if (shuttingDownLE) {
                           shuttingDownLE = false;
                           startLeaderElection();
                           }
                           
                        /* LE为leader election的缩写，
                        makeLEStrategy()是获取一种选主策略，
                        上述论文中也提到了有两种选主策略，
                        对应代码中就是LeaderElection和
                        FastLeaderElection，如果不显示配置，
                        默认会采用FastLeaderElection，
                        lookForLeader会返回新的vote */
                        setCurrentVote(makeLEStrategy().lookForLeader());
                    } catch (Exception e) {
                        LOG.warn("Unexpected exception", e);
                        setPeerState(ServerState.LOOKING);
                    }                        
                }
                break;
            case OBSERVING:
                try {
                    LOG.info("OBSERVING");
                    setObserver(makeObserver(logFactory));
                    observer.observeLeader();
                } catch (Exception e) {
                    LOG.warn("Unexpected exception",e );
                } finally {
                    observer.shutdown();
                    setObserver(null);  
                   updateServerState();
                }
                break;
            case FOLLOWING:
                try {
                   LOG.info("FOLLOWING");
                    setFollower(makeFollower(logFactory));
                    follower.followLeader();
                } catch (Exception e) {
                   LOG.warn("Unexpected exception",e);
                } finally {
                   follower.shutdown();
                   setFollower(null);
                   updateServerState();
                }
                break;
            case LEADING:
                LOG.info("LEADING");
                try {
                    setLeader(makeLeader(logFactory));
                    leader.lead();
                    setLeader(null);
                } catch (Exception e) {
                    LOG.warn("Unexpected exception",e);
                } finally {
                    if (leader != null) {
                        leader.shutdown("Forcing shutdown");
                        setLeader(null);
                    }
                    updateServerState();
                }
                break;
            }
            start_fle = Time.currentElapsedTime();
        }
    } finally {
        ...
    }
}
```

4 ./src/java/main/org/apache/zookeeper/server/quorum/FastLeaderElection.java

```java
/**
     * Starts a new round of leader election. Whenever our QuorumPeer
     * changes its state to LOOKING, this method is invoked, and it
     * sends notifications to all other peers.
     */
    public Vote lookForLeader() throws InterruptedException {
        ...
        
        if (self.start_fle == 0) {
           self.start_fle = Time.currentElapsedTime();
        }
        try {
            HashMap<Long, Vote> recvset = new HashMap<Long, Vote>();

            HashMap<Long, Vote> outofelection = new HashMap<Long, Vote>();

            int notTimeout = finalizeWait;

            /* 
            synchronized(this){
                logicalclock.incrementAndGet();
                updateProposal(getInitId(), getInitLastLoggedZxid(), getPeerEpoch());
            }

            LOG.info("New election. My id =  " + self.getId() +
                    ", proposed zxid=0x" + Long.toHexString(proposedZxid));
            sendNotifications();

            /*
             * Loop in which we exchange notifications until we find a leader
             */

            while ((self.getPeerState() == ServerState.LOOKING) &&
                    (!stop)){
                /*
                 * Remove next notification from queue, times out after 2 times
                 * the termination time
                 */
                Notification n = recvqueue.poll(notTimeout,
                        TimeUnit.MILLISECONDS);

                /*
                 * Sends more notifications if haven't received enough.
                 * Otherwise processes new notification.
                 */
                if(n == null){
                    if(manager.haveDelivered()){
                        sendNotifications();
                    } else {
                        manager.connectAll();
                    }

                    /*
                     * Exponential backoff
                     */
                    int tmpTimeOut = notTimeout*2;
                    notTimeout = (tmpTimeOut < maxNotificationInterval?
                            tmpTimeOut : maxNotificationInterval);
                    LOG.info("Notification time out: " + notTimeout);
                } 
                else if (self.getCurrentAndNextConfigVoters().contains(n.sid)) {
                    /*
                     * Only proceed if the vote comes from a replica in the current or next
                     * voting view.
                     */
                    switch (n.state) {
                    case LOOKING:
                        // If notification > current, replace and send messages out
                        if (n.electionEpoch > logicalclock.get()) {
                            logicalclock.set(n.electionEpoch);
                            recvset.clear();
                            if(totalOrderPredicate(n.leader, n.zxid, n.peerEpoch,
                                    getInitId(), getInitLastLoggedZxid(), getPeerEpoch())) {
                                updateProposal(n.leader, n.zxid, n.peerEpoch);
                            } else {
                                updateProposal(getInitId(),
                                        getInitLastLoggedZxid(),
                                        getPeerEpoch());
                            }
                            sendNotifications();
                        } else if (n.electionEpoch < logicalclock.get()) {
                            if(LOG.isDebugEnabled()){
                                LOG.debug("Notification election epoch is smaller than logicalclock. n.electionEpoch = 0x"
                                        + Long.toHexString(n.electionEpoch)
                                        + ", logicalclock=0x" + Long.toHexString(logicalclock.get()));
                            }
                            break;
                        } else if (totalOrderPredicate(n.leader, n.zxid, n.peerEpoch,
                                proposedLeader, proposedZxid, proposedEpoch)) {
                            updateProposal(n.leader, n.zxid, n.peerEpoch);
                            sendNotifications();
                        }

                        if(LOG.isDebugEnabled()){
                            LOG.debug("Adding vote: from=" + n.sid +
                                    ", proposed leader=" + n.leader +
                                    ", proposed zxid=0x" + Long.toHexString(n.zxid) +
                                    ", proposed election epoch=0x" + Long.toHexString(n.electionEpoch));
                        }

                        recvset.put(n.sid, new Vote(n.leader, n.zxid, n.electionEpoch, n.peerEpoch));

                        if (termPredicate(recvset,
                                new Vote(proposedLeader, proposedZxid,
                                        logicalclock.get(), proposedEpoch))) {

                            // Verify if there is any change in the proposed leader
                            while((n = recvqueue.poll(finalizeWait,
                                    TimeUnit.MILLISECONDS)) != null){
                                if(totalOrderPredicate(n.leader, n.zxid, n.peerEpoch,
                                        proposedLeader, proposedZxid, proposedEpoch)){
                                    recvqueue.put(n);
                                    break;
                                }
                            }

                            /*
                             * This predicate is true once we don't read any new
                             * relevant message from the reception queue
                             */
                            if (n == null) {
                                self.setPeerState((proposedLeader == self.getId()) ?
                                        ServerState.LEADING: learningState());

                                Vote endVote = new Vote(proposedLeader,
                                        proposedZxid, proposedEpoch);
                                leaveInstance(endVote);
                                return endVote;
                            }
                        }
                        break;
                    case OBSERVING:
                        LOG.debug("Notification from observer: " + n.sid);
                        break;
                    case FOLLOWING:
                    case LEADING:
                        /*
                         * Consider all notifications from the same epoch
                         * together.
                         */
                        if(n.electionEpoch == logicalclock.get()){
                            recvset.put(n.sid, new Vote(n.leader, n.zxid, n.electionEpoch, n.peerEpoch));
                            if(termPredicate(recvset, new Vote(n.leader,
                                            n.zxid, n.electionEpoch, n.peerEpoch, n.state))
                                            && checkLeader(outofelection, n.leader, n.electionEpoch)) {
                                self.setPeerState((n.leader == self.getId()) ?
                                        ServerState.LEADING: learningState());

                                Vote endVote = new Vote(n.leader, n.zxid, n.peerEpoch);
                                leaveInstance(endVote);
                                return endVote;
                            }
                        }

                        /*
                         * Before joining an established ensemble, verify that
                         * a majority are following the same leader.
                         * Only peer epoch is used to check that the votes come
                         * from the same ensemble. This is because there is at
                         * least one corner case in which the ensemble can be
                         * created with inconsistent zxid and election epoch
                         * info. However, given that only one ensemble can be
                         * running at a single point in time and that each 
                         * epoch is used only once, using only the epoch to 
                         * compare the votes is sufficient.
                         * 
                         * @see https://issues.apache.org/jira/browse/ZOOKEEPER-1732
                         */
                        outofelection.put(n.sid, new Vote(n.leader, 
                                IGNOREVALUE, IGNOREVALUE, n.peerEpoch, n.state));
                        if (termPredicate(outofelection, new Vote(n.leader,
                                IGNOREVALUE, IGNOREVALUE, n.peerEpoch, n.state))
                                && checkLeader(outofelection, n.leader, IGNOREVALUE)) {
                            synchronized(this){
                                logicalclock.set(n.electionEpoch);
                                self.setPeerState((n.leader == self.getId()) ?
                                        ServerState.LEADING: learningState());
                            }
                            Vote endVote = new Vote(n.leader, n.zxid, n.peerEpoch);
                            leaveInstance(endVote);
                            return endVote;
                        }
                        break;
                    default:
                        LOG.warn("Notification state unrecoginized: " + n.state
                              + " (n.state), " + n.sid + " (n.sid)");
                        break;
                    }
                } else {
                    LOG.warn("Ignoring notification from non-cluster member " + n.sid);
                }
            }
            return null;
        } finally {
            try {
                if(self.jmxLeaderElectionBean != null){
                    MBeanRegistry.getInstance().unregister(
                            self.jmxLeaderElectionBean);
                }
            } catch (Exception e) {
                LOG.warn("Failed to unregister with JMX", e);
            }
            self.jmxLeaderElectionBean = null;
        }
    }
}	
```

### 写操作

1 ./src/java/main/org/apache/zookeeper/server/quorum//QuorumPeer.java

```java
case LEADING:
    LOG.info("LEADING");
    try {
        setLeader(makeLeader(logFactory)); // 创建Leader对象
        leader.lead(); // leader的主要过程就在这里
        setLeader(null);
    } catch (Exception e) {
        LOG.warn("Unexpected exception",e);
    } finally {
        if (leader != null) {
            leader.shutdown("Forcing shutdown");
            setLeader(null);
        }
        updateServerState();
    }
    break;
```

2 ./src/java/main/org/apache/zookeeper/server/quorum/Leader.java

```java
void lead() throws IOException, InterruptedException {
    ...
	
    startZkServer(); // 启动ZookeeperServer
    ...
}
```

3 ./src/java/main/org/apache/zookeeper/server/quorum/Leader.java
	
```java
/**
 * Start up Leader ZooKeeper server and initialize zxid to the new epoch
 */
private synchronized void startZkServer() {
    ...
    zk.startup(); // 这个zk是LeaderZooKeeperServer对象
    ...
}
```

4 ./src/java/main/org/apache/zookeeper/server/quorum/LeaderZooKeeperServer.java
	
```java
@Override
public synchronized void startup() {
    super.startup(); // LeaderZooKeeperServer继承了ZooKeeperServer
    if (containerManager != null) {
        containerManager.start();
    }
}
```

5 ./src/java/main/org/apache/zookeeper/server/ZooKeeperServer.java

```java
public synchronized void startup() {
    if (sessionTracker == null) {
        createSessionTracker();
    }
    startSessionTracker();
    setupRequestProcessors(); // 这里会调用不同的ZooKeeperServer派生类自己重写的方法，所以这里按照上面的逻辑，调用的是LeaderZooKeeperServer里的setupRequestProcessors方法
  
    registerJMX();
  
    state = State.RUNNING;
    notifyAll();
}
```

6 ./src/java/main/org/apache/zookeeper/server/quorum/LeaderZooKeeperServer.java

```java
@Override
protected void setupRequestProcessors() {
    /* 多个Processor级联，上游Processor处理完以后会调用下游的
    Processor，firstProcessor在这里没用到，直接从
    prepRequestProcessor开始看 */
    RequestProcessor finalProcessor = new FinalRequestProcessor(this);
    RequestProcessor toBeAppliedProcessor = new Leader.ToBeAppliedRequestProcessor(finalProcessor, getLeader());
    commitProcessor = new CommitProcessor(toBeAppliedProcessor,
            Long.toString(getServerId()), false,
            getZooKeeperServerListener());
    commitProcessor.start();
    ProposalRequestProcessor proposalProcessor = new ProposalRequestProcessor(this,
            commitProcessor);
    proposalProcessor.initialize();
    prepRequestProcessor = new PrepRequestProcessor(this, proposalProcessor);
    prepRequestProcessor.start();
    firstProcessor = new LeaderRequestProcessor(this, prepRequestProcessor);
  	
    setupContainerManager();
}
```

7 ./src/java/main/org/apache/zookeeper/server/PrepRequestProcessor.java

```java
@Override
public void run() {
    try {
        while (true) {
            /* 在QuorumPeer类中，start函数调用了
            startServerCnxnFactory，然后调用
            cnxnFactory.start()，这里的cnxnFactory
            是NIOServerCnxnFactory对象，所以这里的start
            其实就是启动了NIO的actor模型。
            NIOServerCnxnFactory里的AcceptThread，
            是继承自Thread的类，所以会不断调用其run()函数，
            run()函数里调用select，select调用handleIO，
            handleIO里的实际操作是交给了线程池，接着看
            IOWorkRequest，IOWorkRequest的doWork就是线程
            池里线程的实际处理，doWork里会调用cnxn.doIO()，
            接着看NIOServerCnxn的doIO函数，会调用
            readPayload()，readPayload里调用
            readRequest()，readRequest里调用
            zkServer.processPacket(...)，processPacket
            会调用submitRequest，submitRequest会调用
            submitRequest，submitRequest会调用
            firstProcessor.processRequest(...)，
            后面就进入级联的多个Processor处理过程了 */
            Request request = submittedRequests.take();
            long traceMask = ZooTrace.CLIENT_REQUEST_TRACE_MASK;
            if (request.type == OpCode.ping) {
                traceMask = ZooTrace.CLIENT_PING_TRACE_MASK;
            }
            if (LOG.isTraceEnabled()) {
                ZooTrace.logRequest(LOG, traceMask, 'P', request, "");
            }
            if (Request.requestOfDeath == request) {
                break;
            }
            pRequest(request); // 处理请求的过程
        }
    } catch (RequestProcessorException e) {
        if (e.getCause() instanceof XidRolloverException) {
            LOG.info(e.getCause().getMessage());
        }
        handleException(this.getName(), e);
    } catch (Exception e) {
        handleException(this.getName(), e);
    }
    LOG.info("PrepRequestProcessor exited loop!");
}
```

8 ./src/java/main/org/apache/zookeeper/server/PrepRequestProcessor.java

```java
protected void pRequest(Request request) throws RequestProcessorException {
...
            case OpCode.setData:  // 我们只看修改数据的请求怎么实现
                  SetDataRequest setDataRequest = new SetDataRequest();
                  /* pRequest2Txn会将请求变成一条或多条
                  ChangeRecord，然后加入ChangeRecord列表中
                  （下一个Processor会从这个列表里取数据） */
                  pRequest2Txn(request.type, zks.getNextZxid(), request, setDataRequest, true);
                  break;
...
          request.zxid = zks.getZxid();
          nextProcessor.processRequest(request); // 进行下一个Processor
}
```

9 ./src/java/main/org/apache/zookeeper/server/quorum/ProposalRequestProcessor.java

从6中可以看到，下一个Processor是ProposalRequestProcessor

```java
public void processRequest(Request request) throws RequestProcessorException {
    // LOG.warn("Ack>>> cxid = " + request.cxid + " type = " +
    // request.type + " id = " + request.sessionId);
    // request.addRQRec(">prop");
  
  
    /* In the following IF-THEN-ELSE block, we process syncs on the leader.
     * If the sync is coming from a follower, then the follower
     * handler adds it to syncHandler. Otherwise, if it is a client of
     * the leader that issued the sync command, then syncHandler won't
     * contain the handler. In this case, we add it to syncHandler, and
     * call processRequest on the next processor.
     */
  
    if (request instanceof LearnerSyncRequest){
        zks.getLeader().processSync((LearnerSyncRequest)request);
    } else {
        /* 如果是主，对于接到的修改请求，需要先
        nextProcessor（CommitProcessor）来确定是否还有未
        Commit的提议，如果有，就先将当前请求加入
        queuedRequests，如果没有，唤醒CommitProcessor，
        propose queuedRequests中的请求（按顺序应该是最旧的
        那个）。propose请求，主要就是对follower发包。
        前面判断是否还有未在本地Commit的提议时，检测方法是
        检查request的引用计数 */
        nextProcessor.processRequest(request);
        if (request.getHdr() != null) {
            // We need to sync and get consensus on any transactions
            try {
                /* 可以发出提议了 */
                zks.getLeader().propose(request);
            } catch (XidRolloverException e) {
                throw new RequestProcessorException(e.getMessage(), e);
            }
            /* 发完提议以后交给SyncRequestProcessor处理 */
            syncProcessor.processRequest(request);
        }
    }
}
```

10 ./src/java/main/org/apache/zookeeper/server/quorum/Leader.java

```java
/**
 * create a proposal and send it out to all the members
 *
 * @param request
 * @return the proposal that is queued to send to all the members
 */
public Proposal propose(Request request) throws XidRolloverException {
    /**
     * Address the rollover issue. All lower 32bits set indicate a new leader
     * election. Force a re-election instead. See ZOOKEEPER-1277
     */
    if ((request.zxid & 0xffffffffL) == 0xffffffffL) {
        String msg =
                "zxid lower 32 bits have rolled over, forcing re-election, and therefore new epoch start";
        shutdown(msg);
        throw new XidRolloverException(msg);
    }
  
    ByteArrayOutputStream baos = new ByteArrayOutputStream();
    BinaryOutputArchive boa = BinaryOutputArchive.getArchive(baos);
    try {
        request.getHdr().serialize(boa, "hdr");
        if (request.getTxn() != null) {
            request.getTxn().serialize(boa, "txn");
        }
        baos.close();
    } catch (IOException e) {
        LOG.warn("This really should be impossible", e);
    }
    QuorumPacket pp = new QuorumPacket(Leader.PROPOSAL, request.zxid,
            baos.toByteArray(), null);
  
    Proposal p = new Proposal();
              p.packet = pp;
    p.request = request;
  
    synchronized(this) {
       p.addQuorumVerifier(self.getQuorumVerifier());
  
       if (request.getHdr().getType() == OpCode.reconfig){
           self.setLastSeenQuorumVerifier(request.qv, true);
       }
  
       if (self.getQuorumVerifier().getVersion()<self.getLastSeenQuorumVerifier().getVersion()) {
           p.addQuorumVerifier(self.getLastSeenQuorumVerifier());
       }
  
        if (LOG.isDebugEnabled()) {
            LOG.debug("Proposing:: " + request);
        }
  
        lastProposed = p.packet.getZxid();
        /* 这里对request的引用会在另一处处理ack的地方尝试去掉引用 */
        outstandingProposals.put(lastProposed, p);
        /* 数据包没有对request的引用 */
        sendPacket(pp);
    }
    return p;
}
```

11 ./src/java/main/org/apache/zookeeper/server/quorum/ProposalRequestProcessor.java

回到9，交给SyncRequestProcessor以后，其实是放入了SyncRequestProcessor的queuedRequests中，SyncRequestProcessor也是一个线程，其run()里会对queuedRequests进行处理。
	
run里会从queuedRequests取出请求，将transaction log刷磁盘，并调用`nextProcessor.processRequest(i);`，而这里的nextProcessor是AckRequestProcessor。

12 ./src/java/main/org/apache/zookeeper/server/quorum/AckRequestProcessor.java

```java
/**
 * Forward the request as an ACK to the leader
 */
public void processRequest(Request request) {
    QuorumPeer self = leader.self;
    if(self != null)
        leader.processAck(self.getId(), request.zxid, null);
    else
        LOG.error("Null QuorumPeer");
}
```

13 ./src/java/main/org/apache/zookeeper/server/quorum/Leader.java

processAck会调用tryToCommit，这里就会检查得到的ack是否已经满足quorum要求，然后从outstandingProposals移除对应的proposal，让上游得以继续发送新的提议。

[zab]: http://diyhpl.us/~bryan/papers2/distributed/distributed-systems/zab.totally-ordered-broadcast-protocol.2008.pdf
[zab-theory-practice]: http://www.tcs.hut.fi/Studies/T-79.5001/reports/2012-deSouzaMedeiros.pdf
