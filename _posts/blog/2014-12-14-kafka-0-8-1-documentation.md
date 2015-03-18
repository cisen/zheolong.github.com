---
layout: post
title: "Kafka 0.8.1 Documentation"
modified:
categories: blog
excerpt:
tags: [Kafka, XFS, Disk Usage, Apparent Size, Df, Du, Preallocatio]
author: zheolong
comments: true
share: true
date: 2014-12-14T12:54:02+08:00
---

## 前言

Apache Kafka is publish-subscribe messaging rethought as a distributed commit log.

Apache Kafka是一个发布订阅消息传送，可以想象为分布式提交的日志

Fast
A single Kafka broker can handle hundreds of megabytes of reads and writes per second from thousands of clients.

迅捷
单个Kafka broker每秒可以处理来自上千台客户端的几百兆字节的读取和写入。

Scalable
Kafka is designed to allow a single cluster to serve as the central data backbone for a large organization. It can be elastically and transparently expanded without downtime. Data streams are partitioned and spread over a cluster of machines to allow data streams larger than the capability of any single machine and to allow clusters of co-ordinated consumers

可扩展
Kafka被设计允许单个集群作为大型机构的中央数据骨干。在不停止服务的情况下，可弹性透明地扩展。数据流被分片，并分布在集群的机器中，使得数据流远远大于单个机器的容量，允许协同的消费者集群。

Durable
Messages are persisted on disk and replicated within the cluster to prevent data loss. Each broker can handle terabytes of messages without performance impact.

可靠性
消息被持久化保存在硬盘上，并在集群内复制，以防止数据丢失。在不损失性能的情况下，每个broker可以处理几T的消息。

Distributed by Design
Kafka has a modern cluster-centric design that offers strong durability and fault-tolerance guarantees.

分布式设计
Kafka采用现今的cluster-centric设计，以提供强大的可靠性和容错性保障。


## Getting Started

### 1.1 Introduction

Kafka是一个分布式，分片，多副本的提交消息服务。提供了消息系统的功能，然而具有独特的设计。

首先来回顾下基本的消息传送术语：
Kafka将消息内容保存在名为“topics”的目录中。
将消息发布到Kafka topic中的进程叫做“producers”。
订阅消息并对消息内容进行处理的进程叫做“consumers”。
Kafka集群由一个或多个servers组成，每个server叫做“broker”。

总的来说，producers通过网络将消息发送到Kafka集群，Kafka集群再将消息转发给consumers。如下图：

clients和servers之间的交互是通过简单、高效、语言无关的TCP协议。官方提供了Java客户端，还有其他开发者提供的多种语言客户端。

#### Topics and Logs

我们深入了解下Kafka的抽象概念--topic（话题）
topic是目录或内容名，消息会发送到相应的topic。对于每个topic，Kafka集群维护了一个分片的日志，如下图所示：

每个partition是连续追加到提交日志的有序的、不可变的消息序列，partition中的每条消息会分配一个顺序id，即“offset”，其唯一得标记partition中的每条消息。

对于已经发布的消息，无论消息是否已被消费，Kafka集群都会将其保存一段时间，这个时间是可以配置的。例如，如果“log retention”设定为2天，那么在一条消息在发布后的两天内是可消费的，之后会被丢弃已释放空间。Kafka的性能
不受数据大小的影响，所以可以保存大量数据。

实际上，以每个消费者为基础的元数据只有消费者在日志中的位置，即“offset”。消费者控制对应的offset：消费者通常会随着消息的读取线性地更新它的offset，但是实际上消费者控制位置，所以以任何顺序消费消息。例如，可以消费者可以将消费位置重置到旧的offset，以重新处理消息。

这些特征综合起来看，Kafka消费者成本很低——启动和停止都不会对集群和其它消费者造成很大的影响。例如，可以使用命令行工具，“tail”任何topic的内容，而不会改变任何现存的consumers。

日志的partitions有几个目的。第一，允许日志通过多台服务器进行线性扩展，而不会受限于单个服务器的容量。每个单独的分区受限于所在服务器的容量。但是topic可以具有很多分区，所以可以处理任意数量的数据。

#### 分布

日志的partition分布在多台服务器上，每个服务器处理一份partitions。考虑到容错性，每个patition会在若干台服务器上备份。

对于每个partition，有一个服务器作为“leader”，没有或更多服务器作为“follwers”。leader处理对该分片的读写请求，而followers只是被动地复制leader。如果leader挂了，会有一个follower自动称为新leader。每个服务器会作为其上一些partition的leader，同时作为其余partition的follower，这样集群内是负载均衡的。

#### Producers

producer发布消息到其指定的topic，也负责选定要发往的partition。可以用round-robin以均衡负载，或者根据语义分片函数（例如基于消息中的key）。关于分片，后面会有更详细的讲解。

#### Consumers

消息队列一般具有两种模型：排队和发布订阅。在排队中，一群consumers会从服务器读取消息，而每个消息被发送到其中之一；在发布-订阅中，消息被广播到所有consumers。Kafka提出了实现这两种模型的consumer抽象概念——consumer group。

consumers标记自己属于一个group，发布到topic的每条消息会被发送到每个订阅group的一个consumer实例。consumer实例可以在多个独立的进程或机器上。

如果所有的consumer实例具有相同的group，这就像传统的队列，在consumers直接均衡负载。

如果所有的consuemr实例具有不同的group，这就像发布-订阅系统，所有消息被广播给所有consumers。

然而，我们发现，一般情况下，topic一般有少数consumer groups，每个代表“逻辑订阅者”。每个group由多个consumer实例构成，以提高性能和容错性。与发布-订阅相比，订阅者只是从单个进程变成了一组消费者。

Kafka比传统的消息系统具有更强的顺序保障。
传统的消息队列将消息按序保存在服务器上，如果多个消费者从队列中消费，服务器按存储的顺序递交消息。然而，虽然服务器按序递交消息，但消息本身是异步传递给consumers，所以到达多个consumers可能是乱序的。即，在并发消费时，消息的顺序丢失。消息队列处理此问题的方法是使用“exclusive consumer”，仅允许一个消费者去消费，但是如此就没有并发可言了。

相比之下，Kafka做得更好。利用topic中的partitions，Kafka可以同时提供顺序保障和多个consumer进程之间的负载均衡。这是通过将topic的partitions分配给group中的consumers，以便每个partition仅被该group中的一个consumer消费。如此保证该consumer是此partition的唯一reader，并且按序消费数据。因为有很多partitions，所以仍然可以在多个consumer实例之间均衡负载。注意，consumer实例的数量不能多于partition的数量。

Kafka仅提供partition内的消息有序，而非同一个topic的所有partitons。单partition有序，结合按key发布数据，对于大多数应用已经足够。然而，如果需要全局有序（topic的所有数据都有序），那么此topic只能有一个partition，这意味着只能有一个消费者。

#### Guarantees

Kafka能够提供以下保障：
消息可以按照其被发送到topic-partition的顺序被保存。即，由同一个prducer发送的消息M1、M2，如果M1先于M2被发送，那么在服务器上，M1的offset比M2要小，也就是说，M1在日志文件的更靠前位置。

consumer实例以消息存储的顺序消费消息。

对于replication因子为N的topic，可以容忍N-1个服务器故障，而不会丢失已提交的消息。

文档的设计部分给出了这些保障的更多细节。

### 1.2 使用案例

下面是Apache Kafka几个常用案例的说明。想对这些领域有一个大概了解，请看这篇博客。

#### 队列

将Kafka用于传统消息队列的替代。消息brokers用于多种目的（解耦数据生产和处理，缓存未处理的消息等等）。相比于多数消息系统，Kafka吞吐量更大，内置分片，多副本，容错性，对于大型消息处理应用是不错的解决方案。

依我们的经验来看，消息队列相对低吞吐，但是要求端到端延迟低，而且依赖Kafka提供的强可靠性。

在此领域，Kafka可与传统消息系统ActiveMQ和RabbitMQ相提并论。

#### 网站活动跟踪

最初的使用案例是通过一组实时的发布-订阅源重建用户活动跟踪管道。网站活动（页面浏览、搜索或者其他用户动作）被发布到中心topics，每个topic对应一种活动类型。这些源可用于多种使用订阅场景，包括实时处理、实时监测，以及载入Hadoop或离线数据存储系统，用于离线处理和报告。

活动跟踪产生的数据量比较大，因为对于每次用户网页浏览，都会产生活动消息。

#### Metrics

Kafka常用于运行监测数据。这涉及到聚合从分布式应用中得到的数据，以产生运行数据的集中订阅源。

#### Log Aggregation

许多人将Kafka替代日志聚合作为解决方案。日志聚合通常从服务器上收集物理日志文件，并将其放入中心位置（文件服务器或HDFS）进行处理。Kafka抽象了文件细节，将日志或事件数据抽象为消息流。允许低延迟的处理，支持多数据源和分布式数据消费。相比于以日志为中心的系统如**Scribe**或**Flume**，Kafka提供了同样高的性能、更强的可靠性（因为副本）、耕地的端到端延迟。

#### 流处理

许多用户最终会做阶段性的数据处理，其中，从保存原始数据的topi消费的数据被聚合、浓缩或转移到新的Kafka topic以供进一步消费。例如，文章推荐的处理流程会从RSS源爬取文章内容，并将其发布到名为“articles”的topic；进一步处理会使文章内容标准化或将其复制到净化的文章内容topic；最后阶段会尝试匹配内容与用户。这从独立topics产生了一副实时数据流图。**Storm**和**Samza**是用于实现这种转变的流行框架。

#### 事件源

事件源是一类应用设计，其中，状态改变被记录为以时间为序的记录。Kafka对超大量日志数据存储的支持，使其成为此类应用的极佳后端。

#### 提交日志

Kafka可以作为分布式系统的外部提交日志。日志有助于节点间复制数据，并作为故障节点的同步机制以恢复数据。Kafka的日志压缩特性支持此用途。在此用法中，Kafka类似于**Apache BookKeeper**项目。

### 1.3 Quik Start
略过，自己操作即可

### 1.4 	生态系统

在主版本外，有大量与Kafka结合的工具。包括流处理系统、Hadoop整合、监控和部署工具，参见[生态系统页面](https://cwiki.apache.org/confluence/display/KAFKA/Ecosystem)。

### 1.5 升级
#### 从0.8升级到0.8.1

0.8.1与0.8完全兼容，所以升级只需停止服务，升级代码，重启服务即可。

#### 从0.7升级

0.8中加入了副本机制，是我们的首个向后非兼容版本：主要改动涉及API、Zookeeper数据结构、协议以及配置。从0.7迁移到0.8.x需要[特殊工具](https://cwiki.apache.org/confluence/display/KAFKA/Migrating+from+0.7+to+0.8)，可在不停止服务的情况下进行此迁移。

## 2 API

### 2.1 Producer API

```
/**
 *  V: type of the message
 *  K: type of the optional key associated with the message
 */
class kafka.javaapi.producer.Producer<K,V> {
  public Producer(ProducerConfig config);

  /**
   * Sends the data to a single topic, partitioned by key, using either the
   * synchronous or the asynchronous producer
   * @param message the producer data object that encapsulates the topic, key and message data
   */
  public void send(KeyedMessage<K,V> message);

  /**
   * Use this API to send data to multiple topics
   * @param messages list of producer data objects that encapsulate the topic, key and message data
   */
  public void send(List<KeyedMessage<K,V>> messages);

  /**
   * Close API to close the producer pool connections to all Kafka brokers.
   */
  public void close();
}
```

[examples](https://cwiki.apache.org/confluence/display/KAFKA/0.8.0+Producer+Example) of producer api.


### 2.2 High Level Consumer API

```
class Consumer {
  /**
   *  Create a ConsumerConnector
   *
   *  @param config  at the minimum, need to specify the groupid of the consumer and the zookeeper
   *                 connection string zookeeper.connect.
   */
  public static kafka.javaapi.consumer.ConsumerConnector createJavaConsumerConnector(ConsumerConfig config);
}

/**
 *  V: type of the message
 *  K: type of the optional key assciated with the message
 */
public interface kafka.javaapi.consumer.ConsumerConnector {
  /**
   *  Create a list of message streams of type T for each topic.
   *
   *  @param topicCountMap  a map of (topic, #streams) pair
   *  @param decoder a decoder that converts from Message to T
   *  @return a map of (topic, list of  KafkaStream) pairs.
   *          The number of items in the list is #streams. Each stream supports
   *          an iterator over message/metadata pairs.
   */
  public <K,V> Map<String, List<KafkaStream<K,V>>>
    createMessageStreams(Map<String, Integer> topicCountMap, Decoder<K> keyDecoder, Decoder<V> valueDecoder);

  /**
   *  Create a list of message streams of type T for each topic, using the default decoder.
   */
  public Map<String, List<KafkaStream<byte[], byte[]>>> createMessageStreams(Map<String, Integer> topicCountMap);

  /**
   *  Create a list of message streams for topics matching a wildcard.
   *
   *  @param topicFilter a TopicFilter that specifies which topics to
   *                    subscribe to (encapsulates a whitelist or a blacklist).
   *  @param numStreams the number of message streams to return.
   *  @param keyDecoder a decoder that decodes the message key
   *  @param valueDecoder a decoder that decodes the message itself
   *  @return a list of KafkaStream. Each stream supports an
   *          iterator over its MessageAndMetadata elements.
   */
  public <K,V> List<KafkaStream<K,V>>
    createMessageStreamsByFilter(TopicFilter topicFilter, int numStreams, Decoder<K> keyDecoder, Decoder<V> valueDecoder);

  /**
   *  Create a list of message streams for topics matching a wildcard, using the default decoder.
   */
  public List<KafkaStream<byte[], byte[]>> createMessageStreamsByFilter(TopicFilter topicFilter, int numStreams);

  /**
   *  Create a list of message streams for topics matching a wildcard, using the default decoder, with one stream.
   */
  public List<KafkaStream<byte[], byte[]>> createMessageStreamsByFilter(TopicFilter topicFilter);

  /**
   *  Commit the offsets of all topic/partitions connected by this connector.
   */
  public void commitOffsets();

  /**
   *  Shut down the connector
   */
  public void shutdown();
}
```

[examples](https://cwiki.apache.org/confluence/display/KAFKA/Consumer+Group+Example) of high level consumer api.


### 2.3 Simple Consumer API

```
class kafka.javaapi.consumer.SimpleConsumer {
  /**
   *  Fetch a set of messages from a topic.
   *
   *  @param request specifies the topic name, topic partition, starting byte offset, maximum bytes to be fetched.
   *  @return a set of fetched messages
   */
  public FetchResponse fetch(kafka.javaapi.FetchRequest request);

  /**
   *  Fetch metadata for a sequence of topics.
   *
   *  @param request specifies the versionId, clientId, sequence of topics.
   *  @return metadata for each topic in the request.
   */
  public kafka.javaapi.TopicMetadataResponse send(kafka.javaapi.TopicMetadataRequest request);

  /**
   *  Get a list of valid offsets (up to maxSize) before the given time.
   *
   *  @param request a [[kafka.javaapi.OffsetRequest]] object.
   *  @return a [[kafka.javaapi.OffsetResponse]] object.
   */
  public kafak.javaapi.OffsetResponse getOffsetsBefore(OffsetRequest request);

  /**
   * Close the SimpleConsumer.
   */
  public void close();
}
```

对于大多数应用，high level consumer Api够用了。一些应用需要high level consumer不具备的特性（例如，重启consumer时初始化offset）。可以使用low level SimpleConsumer Api，但是逻辑可能有点复杂，可以参考[这个例子](https://cwiki.apache.org/confluence/display/KAFKA/0.8.0+SimpleConsumer+Example).


### 2.4 Kafka Hadoop Consumer API

提供了将数据聚合或导入Hadoop的水平可扩展方案是我们的基本使用案例。为了支持此类案例，我们提供了以Hadoop为基础的consumer，产生很多map tasks以从Kafka集群并发拉取数据。这提供了极快的pull-based Hadoop数据导入性能（仅用少数Kafka服务器就可以跑满网络）。

[hadoop consumer的相关资料](https://github.com/linkedin/camus/)

## 3. Configuration

Kafka使用[属性文件格式](http://en.wikipedia.org/wiki/.properties)中的key-value对作为配置。这些值可以从文件中读取，也可以在程序中设置。

### 3.1 Broker Configs

必要配置如下：
broker.id
log.dirs
zookeeper.connect

Topic级的配置以及默认值会在[后面](https://kafka.apache.org/documentation.html#topic-config)详细说明。

| 属性        | 默认值           | 说明  |
| ------------- |:-------------:| -----:|
| broker.id      |              | broker在集群内的唯一id，非负整数 |
| log.dirs      | /tmp/kafka-logs      |   Kafa数据存储目录，逗号分隔；创建新的partition时，会选择partition数量最少的目录 |
| port | 6667      |    服务端接受客户端连接的端口 |
|zookeeper.connect|设置zk连接字符串，例如hostname1:port1,hostname2:port2,hostname3:port3；zk还可以设置"chroot"路径，可以将kafka的相关数据放在该节点路径下，这样可以允许多个kafka集群或其他zk相关应用连接该zk集群，例如hostname1:port1,hostname2:port2,hostname3:port3/chroot/path，表示将此集群相关数据放在/chroot/path路径下，注意在启动kafka集群前，必须创建该路径，并且consumers也必须使用此连接字符串 |
| message.max.bytes	| 1000000 | 服务端可接收的消息大小上限，与consumers的maximum fetch size相配合，否则producers有可能发送过大消息，导致消费不了 | 
|num.network.threads|3|处理网络请求的线程数|
|num.io.threads|8|用于执行请求的I/O线程数，应至少超过硬盘数|
|background.threads|4|用于各种后台处理任务的线程数，例如文件删除|
|queued.max.requests|500|在网络线程停止对新请求的读取前，可排队等候I/O线程的最大请求数|
|host.name|null|broker的主机名。 If this is set, it will only bind to this address. If this is not set, it will bind to all interfaces, and publish one to ZK.|
|advertised.host.name|null|If this is set this is the hostname that will be given out to producers, consumers, and other brokers to connect to.|
|advertised.port|null|The port to give out to producers, consumers, and other brokers to use in establishing connections. This only needs to be set if this port is different from the port the server should bind to.|
|socket.send.buffer.bytes|100 * 1024|socket的发送缓冲区大小SO_SNDBUFF|
|socket.receive.buffer.bytes|100 * 1024|socket的接收缓冲区大小SO_RCVBUFF|
|socket.request.max.bytes|100 * 1024 * 1024|服务端可接收的请求大小上限，防止服务端内存耗尽，需比**java heap**更小|
|num.partitions|1|topic的默认partition数，如果topic创建时没有设置partition count|
|log.segment.bytes|1024 * 1024 * 1024|单个log文件大小上限，可以针对各个topic设置|
|log.roll.hours|24 * 7|log文件rol的时间上限|
|log.cleanup.policy|delete|This can take either the value delete or compact. If delete is set, log segments will be deleted when they reach the size or time limits set. If compact is set log compaction will be used to clean out obsolete records. This setting can be overridden on a per-topic basis (see the per-topic configuration section).|
|log.retention.{minutes,hours}|7 days|文件保存时间，过时则清理|
|log.retention.bytes|-1|文件保存大小，过大则清理|
|log.retention.check.interval.ms|5 minutes|retention检测周期|
|log.cleaner.enable	|false|This configuration must be set to true for log compaction to run.|
|log.cleaner.threads	|1|The number of threads to use for cleaning logs in log compaction.|
|log.cleaner.io.max.bytes.per.second|None|The maximum amount of I/O the log cleaner can do while performing log compaction. This setting allows setting a limit for the cleaner to avoid impacting live request serving.|
|log.cleaner.dedupe.buffer.size|500 * 1024 * 1024|The size of the buffer the log cleaner uses for indexing and deduplicating logs during cleaning. Larger is better provided you have sufficient memory.|
|log.cleaner.io.buffer.size|512*1024|The size of the I/O chunk used during log cleaning. You probably don't need to change this.|
|log.cleaner.io.buffer.load.factor|0.9|The load factor of the hash table used in log cleaning. You probably don't need to change this.|
|log.cleaner.backoff.ms|15000|The interval between checks to see if any logs need cleaning.|
|log.cleaner.min.cleanable.ratio|0.5|This configuration controls how frequently the log compactor will attempt to clean the log (assuming log compaction is enabled). By default we will avoid cleaning a log where more than 50% of the log has been compacted. This ratio bounds the maximum space wasted in the log by duplicates (at 50% at most 50% of the log could be duplicates). A higher ratio will mean fewer, more efficient cleanings but will mean more wasted space in the log. This setting can be overridden on a per-topic basis (see the per-topic configuration section).|
|log.cleaner.delete.retention.ms|1 day|The amount of time to retain delete tombstone markers for log compacted topics. This setting also gives a bound on the time in which a consumer must complete a read if they begin from offset 0 to ensure that they get a valid snapshot of the final stage (otherwise delete tombstones may be collected before they complete their scan). This setting can be overridden on a per-topic basis (see the per-topic configuration section).|

在scala类kafka.server.KafkaConfig.中有更多broker配置相关的细节。

#### Topic级别的配置
与topic相关的配置既有全局配置，也有可选的per-topic配置覆盖全局配置。未设置per-topic配置时默认使用全局配置。可以在创建topic时通过设置一个或多个--config选项来设置per-topic配置。这个例子创建一个topic，名为my-topic，并设定了其最大消息大小和flush频率。

```
 > bin/kafka-topics.sh --zookeeper localhost:2181 --create --topic my-topic --partitions 1 
        --replication-factor 1 --config max.message.bytes=64000 --config flush.messages=1
```

也可以创建topic以后通过alter topic命令来设定这些配置。此例子更新了my-topic的最大消息大小。

```
> bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic my-topic 
    --config max.message.bytes=128000
```

要删除这些配置可以执行下面的命令

```
 > bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic my-topic 
    --deleteConfig max.message.bytes
```

以下是topic级别的配置，这些配置对应的服务器默认配置为**服务器默认属性**列。修改服务器默认配置会修改那些没有特定配置的topic的配置。


| 属性        | 默认值           | 服务器默认属性  |  说明  |
| ------------- |-------------| -----|:----|
|cleanup.policy	| delete	| log.cleanup.policy	| A string that is either "delete" or "compact". This string designates the retention policy to use on old log segments. The default policy ("delete") will discard old segments when their retention time or size limit has been reached. The "compact" setting will enable log compaction on the topic.|
| delete.retention.ms	|86400000 (24 hours)|	log.cleaner.delete.retention.ms|	The amount of time to retain delete tombstone markers for log compacted topics. This setting also gives a bound on the time in which a consumer must complete a read if they begin from offset 0 to ensure that they get a valid snapshot of the final stage (otherwise delete tombstones may be collected before they complete their scan).|
|flush.messages	|None|	log.flush.interval.messages	|This setting allows specifying an interval at which we will force an fsync of data written to the log. For example if this was set to 1 we would fsync after every message; if it were 5 we would fsync after every five messages. In general we recommend you not set this and use replication for durability and allow the operating system's background flush capabilities as it is more efficient. This setting can be overridden on a per-topic basis (see the per-topic configuration section).|
|flush.ms	|None	|log.flush.interval.ms|	This setting allows specifying a time interval at which we will force an fsync of data written to the log. For example if this was set to 1000 we would fsync after 1000 ms had passed. In general we recommend you not set this and use replication for durability and allow the operating system's background flush capabilities as it is more efficient.|
|index.interval.bytes	|4096|log.index.interval.bytes|This setting controls how frequently Kafka adds an index entry to it's offset index. The default setting ensures that we index a message roughly every 4096 bytes. More indexing allows reads to jump closer to the exact position in the log but makes the index larger. You probably don't need to change this.|
|max.message.bytes	|1,000,000|message.max.bytes|This is largest message size Kafka will allow to be appended to this topic. Note that if you increase this size you must also increase your consumer's fetch size so they can fetch messages this large.|
|min.cleanable.dirty.ratio	|0.5|	log.cleaner.min.cleanable.ratio|	This configuration controls how frequently the log compactor will attempt to clean the log (assuming log compaction is enabled). By default we will avoid cleaning a log where more than 50% of the log has been compacted. This ratio bounds the maximum space wasted in the log by duplicates (at 50% at most 50% of the log could be duplicates). A higher ratio will mean fewer, more efficient cleanings but will mean more wasted space in the log.
|retention.bytes|	None|	log.retention.bytes|	This configuration controls the maximum size a log can grow to before we will discard old log segments to free up space if we are using the "delete" retention policy. By default there is no size limit only a time limit.|
|retention.ms	|7 days	|log.retention.minutes|	This configuration controls the maximum time we will retain a log before we will discard old log segments to free up space if we are using the "delete" retention policy. This represents an SLA on how soon consumers must read their data.|
|segment.bytes	|1 GB	|log.segment.bytes|	This configuration controls the segment file size for the log. Retention and cleaning is always done a file at a time so a larger segment size means fewer files but less granular control over retention.|
|segment.index.bytes|	10 MB|	log.index.size.max.bytes|	This configuration controls the size of the index that maps offsets to file positions. We preallocate this index file and shrink it only after log rolls. You generally should not need to change this setting.|
|segment.ms	|7 days	|log.roll.hours|	This configuration controls the period of time after which Kafka will force the log to roll even if the segment file isn't full to ensure that retention can delete or compact old data.

### 3.2 Consumer Configs

必要的consumer配置如下：
group.id
zookeeper.connect

| 属性        | 默认值           | 说明  |
| ------------- |:-------------:| -----:|
|group.id|	|	A string that uniquely identifies the group of consumer processes to which this consumer belongs. By setting the same group id multiple processes indicate that they are all part of the same consumer group.|
|zookeeper.connect|		|Specifies the ZooKeeper connection string in the form hostname:port where host and port are the host and port of a ZooKeeper server. To allow connecting through other ZooKeeper nodes when that ZooKeeper machine is down you can also specify multiple hosts in the form hostname1:port1,hostname2:port2,hostname3:port3. The server may also have a ZooKeeper chroot path as part of it's ZooKeeper connection string which puts its data under some path in the global ZooKeeper namespace. If so the consumer should use the same chroot path in its connection string. For example to give a chroot path of /chroot/path you would give the connection string as hostname1:port1,hostname2:port2,hostname3:port3/chroot/path.|
|consumer.id	|null| Generated automatically if not set.|
|socket.timeout.ms|	30 * 1000	|The socket timeout for network requests. The actual timeout set will be max.fetch.wait + socket.timeout.ms.|
|socket.receive.buffer.bytes|	64 * 1024	|The socket receive buffer for network requests|
|fetch.message.max.bytes|	1024 * 1024	|The number of byes of messages to attempt to fetch for each topic-partition in each fetch request. These bytes will be read into memory for each partition, so this helps control the memory used by the consumer. The fetch request size must be at least as large as the maximum message size the server allows or else it is possible for the producer to send messages larger than the consumer can fetch.|
|auto.commit.enable|	true|	If true, periodically commit to ZooKeeper the offset of messages already fetched by the consumer. This committed offset will be used when the process fails as the position from which the new consumer will begin.|
|auto.commit.interval.ms|	60 * 1000|	The frequency in ms that the consumer offsets are committed to zookeeper.|
|queued.max.message.chunks|	10|	Max number of message chunks buffered for consumption. Each chunk can be up to fetch.message.max.bytes.|
|rebalance.max.retries|	4|	When a new consumer joins a consumer group the set of consumers attempt to "rebalance" the load to assign partitions to each consumer. If the set of consumers changes while this assignment is taking place the rebalance will fail and retry. This setting controls the maximum number of attempts before giving up.|
|fetch.min.bytes|	1	|The minimum amount of data the server should return for a fetch request. If insufficient data is available the request will wait for that much data to accumulate before answering the request.|
|fetch.wait.max.ms	|100|	The maximum amount of time the server will block before answering the fetch request if there isn't sufficient data to immediately satisfy fetch.min.bytes|
|rebalance.backoff.ms	|2000|	Backoff time between retries during rebalance.|
|refresh.leader.backoff.ms|	200|	Backoff time to wait before trying to determine the leader of a partition that has just lost its leader.|
|auto.offset.reset|	largest| What to do when there is no initial offset in ZooKeeper or if an offset is out of range: (1)smallest : automatically reset the offset to the smallest offset (2)largest : automatically reset the offset to the largest offset (3)anything else: throw exception to the consumer|
|consumer.timeout.ms	|-1|	Throw a timeout exception to the consumer if no message is available for consumption after the specified interval|
|client.id|	group id value|	The client id is a user-specified string sent in each request to help trace calls. It should logically identify the application making the request.|
|zookeeper.session.timeout.ms |	6000|	ZooKeeper session timeout. If the consumer fails to heartbeat to ZooKeeper for this period of time it is considered dead and a rebalance will occur.|
|zookeeper.connection.timeout.ms|	6000|	The max time that the client waits while establishing a connection to zookeeper.|
|zookeeper.sync.time.ms |	2000|	How far a ZK follower can be behind a ZK leader|

在scala类kafka.consumer.ConsumerConfig.中有更多consumer配置相关的细节。

### 3.3 Producer Configs

必要的consumer配置如下：

* metadata.broker.list
* request.required.acks
* producer.type
* serializer.class

| 属性        | 默认值           | 说明  |
| ------------- |:-------------:| -----:|


## 4. Design
### 4.1 Motivation
### 4.2 Persistence
#### Don't fear the filesystem!
pagecache-centric design

#### Constant Time Suffices