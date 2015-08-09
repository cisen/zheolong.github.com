---
layout: post
title: "Kafka 0.8.2 Documentation"
modified:
categories: blog
excerpt:
tags: [Kafka, XFS, Disk Usage, Apparent Size, Df, Du, Preallocatio]
author: zheolong
comments: true
share: true
date: 2014-12-14T12:54:02+08:00
---

# [Apache Kafka](https://kafka.apache.org/)

Apache Kafka是一个发布订阅消息系统，可以想象为分布式提交的log。

## 高性能

单个Kafka broker每秒可以处理上千台客户端几百兆字节的读写。

## 可扩展

Kafka被设计为可以使单个集群成为大型机构的中央数据主干。在不停止服务的情况下，可弹性透明地扩展。数据流被分片，并分布在一个集群的机器上，使得数据流远远大于单个机器的容量，并且允许协同的消费者集群。

## 可靠性

消息被持久化保存在硬盘上，并在集群内拷贝，以防止数据丢失。每个broker可以处理几T的消息而不会损失性能。

## 分布式设计

Kafka采用现今的cluster-centric设计，以提供强大的可靠性和容错性保障。


# [Getting Started](https://kafka.apache.org/documentation.html)

## 1.1 Introduction

Kafka是一个分布式、分片、多副本的提交消息服务。以独特的设计提供了消息系统的功能。

首先来回顾下基本的消息系统术语：

* Kafka将消息内容保存在名为*topics*的目录中。
* 将消息发布到Kafka topic的进程称为*producers*。
* 将订阅消息并对消息进行处理的进程称为*consumers*。
* Kafka集群由一个或多个servers组成，将每个server称为*broker*。

总的来说，producers通过网络将消息发送到Kafka集群，Kafka集群再将消息转发给consumers。如下图：

![image]({{ site.url }}/images/blog/kafka-0-8-2-documentation/producer_consumer.png)


clients和servers之间的交互是通过简单、高效、语言无关的[TCP协议](https://cwiki.apache.org/confluence/display/KAFKA/A+Guide+To+The+Kafka+Protocol)。官方提供了Java客户端，还有其他开发者提供的[多种语言客户端](https://cwiki.apache.org/confluence/display/KAFKA/Clients)。

### Topics and Logs

我们深入了解下Kafka的抽象概念--topic（话题）。

topic是目录或feed名称，消息会发送到相应的topic。对于每个topic，Kafka集群维护了一个分片的日志，如下图所示：

![image]({{ site.url }}/images/blog/kafka-0-8-2-documentation/log_anatomy.png)

每个partition是连续追加到提交log的有序的、不可变的消息序列，partition中的每条消息会分配一个顺序id，即*offset*，其唯一标记了partition中的每条消息。

对于已经发布的消息，无论消息是否已经被消费，Kafka集群都会将其保存一段时间，这个时间是可以配置的。例如，如果log retention设定为2天，那么在一条消息在发布后的两天内是可消费的，之后会被丢弃以释放空间。Kafka的性能不受数据大小的影响，所以可以保存大量数据。

实际上，以每个消费者为基础保留的元数据只有消费者在日志中的位置，即“offset”。消费者控制对应的offset：消费者通常会随着消息的读取线性地更新它的offset，但是实际上是消费者控制着位置，所以消费者可以按任意顺序消费消息。例如，消费者可以将消费位置重置到旧的offset，以重新处理消息。

这些特征综合起来看，Kafka消费者成本很低——启动和停止都不会对集群和其它消费者造成很大的影响。例如，可以使用命令行工具，“tail”任何topic的内容，而不会改变任何现存的consumers。

日志的partitions有几个目的。第一，使日志可以通过多台服务器进行线性扩展，而不会受限于单个服务器的容量。虽然每个单独的分片受限于所在服务器的容量，但是topic可以具有很多分片，所以可以处理任意数量的数据。

### 分布式

日志的partition分布在多台服务器上，每个服务器处理一些partitions的数据和请求。考虑到容错性，每个patition会在若干台服务器上备份。

对于每个partition，有一个服务器作为“leader”，其他部分服务器作为“follwers”。leader处理对该分片的读写请求，而followers只是被动地复制leader。如果leader挂了，会有一个follower自动成为新leader。每个服务器会作为其上一些partition的leader，同时作为其余partition的follower，这样集群内是负载均衡的。

### Producers

producer发布消息到其指定的topic，也负责选定要发往的partition。为了负载均衡，可以用round-robin，或者根据语义分片函数（例如基于消息中的key）。关于分片，后面会有更详细的讲解。

### Consumers

消息队列一般具有两种模型：排队和发布订阅。在排队中，一群consumers会从服务器读取消息，而每个消息被发送到其中之一的consumer；在发布-订阅中，消息被广播到所有consumers。Kafka提出了实现这两种模型的consumer抽象概念——consumer group。

consumers将自己标记为属于一个group，发布到topic的每条消息会被发送到每个订阅group的一个consumer实例。consumer实例可以在多个独立的进程或机器上。

如果所有的consumer实例具有相同的group，这就像传统的队列，在consumers之间均衡负载。

如果所有的consuemr实例具有不同的group，这就像发布-订阅系统，所有消息被广播给所有consumers。

然而，我们发现，topic一般有少数consumer groups，每个代表“逻辑订阅者”。每个group由多个consumer实例构成，以提高性能和容错性。与发布-订阅相比，订阅者只是从单个进程变成了一组消费者。

![image]({{ site.url }}/images/blog/kafka-0-8-2-documentation/consumer-groups.png)

Kafka比传统的消息系统具有更强的顺序保障。

传统的消息队列将消息按序保存在服务器上，如果多个消费者从队列中消费，服务器按存储的顺序递交消息。然而，虽然服务器按序递交消息，但消息本身是异步传递给consumers，所以到达多个consumers可能是乱序的。即，在并发消费时，消息的顺序丢失。消息队列处理此问题的方法是使用“exclusive consumer”，仅允许一个消费者去消费，但是如此就没有并发可言了。

相比之下，Kafka做得更好。利用topic中的partitions，Kafka可以同时提供顺序保障和多个consumer进程之间的负载均衡。这是通过将topic的partitions分配给group中的consumers，以便每个partition仅被该group中的一个consumer消费。如此保证该consumer是此partition的唯一读者，并且按序消费数据。因为有很多partitions，所以仍然可以在多个consumer实例之间均衡负载。注意，consumer实例的数量不能多于partition的数量。

Kafka仅提供partition内的消息有序，而非同一个topic的所有partitons。单partition有序，结合按key发布数据，对于大多数应用已经足够。然而，如果需要全局有序（topic的所有数据都有序），那么此topic只能有一个partition，意味着只能有一个消费者。

### Guarantees

Kafka能够提供以下保障：

* 消息可以按照被发送到topic-partition的顺序保存。即，由同一个prducer发送的消息M1、M2，如果M1先于M2被发送，那么在服务器上，M1的offset比M2要小，也就是说，M1在日志文件的位置更靠前。
* consumer实例按照消息存储的顺序消费消息。
* 对于replication factor为N的topic，可以容忍N-1个服务器故障，而不会丢失已提交的消息。

文档的设计部分给出了这些保障的更多细节。

## 1.2 使用案例

下面是Apache Kafka几个常用案例的说明。想对这些领域有一个大概了解，请看[这篇博客](http://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)。

### 队列

用Kafka替代传统消息队列。消息brokers用于多种目的（解耦数据生产和处理，缓存未处理的消息等等）。相比于多数消息系统，Kafka吞吐量更大，内置分片，多副本，容错性，对于大型消息处理应用是不错的解决方案。

依我们的经验来看，消息队列相对低吞吐，但是要求端到端延迟低，而且依赖Kafka提供的强可靠性。

在此领域，Kafka可与传统消息系统[ActiveMQ](http://activemq.apache.org/)和[RabbitMQ](https://www.rabbitmq.com/)相提并论。

### 网站活动跟踪

最初的使用案例是通过一组实时的发布-订阅feed重建用户活动跟踪管道。网站活动（页面浏览、搜索或者其他用户行为）被发布到中心topics，每个topic对应一种活动类型。这些feeds可用于多种使用订阅场景，包括实时处理、实时监测，以及载入Hadoop或离线数据存储系统，用于离线处理和报告。

活动跟踪产生的数据量比较大，因为每次用户浏览网页，都会产生活动消息。

### Metrics

Kafka常用于运行监测数据。这涉及到聚合从分布式应用中得到的数据，以产生运行数据的集中订阅feed。

### 日志聚合

许多人用Kafka替代日志聚合方案。日志聚合通常从服务器上收集物理日志文件，并将其放入中心位置（文件服务器或HDFS）进行处理。Kafka抽象了文件细节，将日志或事件数据抽象为消息流。允许低延迟的处理，支持多数据源和分布式数据消费。与以日志为中心的系统如Scribe或Flume相比，Kafka提供了同样高的性能、更强的可靠性（因为副本）、更低的端到端延迟。

### 流处理

许多用户会进行阶段性的数据处理，其中，从保存原始数据的topics消费数据，这些数据被聚合、丰富或转移到新的Kafka topic以供进一步消费。例如，文章推荐的处理流程会从RSS源爬取文章内容，并将其发布到名为“articles”的topic；进一步处理，对文章内容进行标准化或去重，然后发布到到文章内容更清晰的topic；最后阶段，尝试匹配内容与用户。通过独立的topics生成了一副实时的数据流图。[Storm](https://storm.apache.org/)和[Samza](http://samza.apache.org/)是用于实现这种转变的流行框架。

### 事件源

[事件源](http://martinfowler.com/eaaDev/EventSourcing.html)是一种类型的应用设计，其中，状态变化被记录为以时间为序的records。Kafka对海量日志数据存储的支持，使其成为此类应用的极佳后端。

### 提交日志

Kafka可以作为分布式系统的外部提交日志。日志有助于节点间复制数据，并作为故障节点的同步机制用来恢复数据。Kafka的log compaction支持此用途，类似于[Apache BookKeeper](http://zookeeper.apache.org/bookkeeper/)项目。

## 1.3 Quik Start

此教程假设你是第一次使用，还未部署过Kafka或Zookeeper。

### 步骤1：下载

下载0.8.2.0版本并解压。

```
> tar -xzf kafka_2.10-0.8.2.0.tgz
> cd kafka_2.10-0.8.2.0
```

### 步骤2：启动server

首先启动Zookeeper，可以用kafka安装包里的脚本启动一个伪分布式的单机Zookeeper服务。

```
> bin/zookeeper-server-start.sh config/zookeeper.properties
[2013-04-22 15:01:37,495] INFO Reading configuration from: config/zookeeper.properties (org.apache.zookeeper.server.quorum.QuorumPeerConfig)
...
```

然后启动Kafka服务：

```
> bin/kafka-server-start.sh config/server.properties
[2013-04-22 15:01:47,028] INFO Verifying properties (kafka.utils.VerifiableProperties)
[2013-04-22 15:01:47,051] INFO Property socket.send.buffer.bytes is overridden to 1048576 (kafka.utils.VerifiableProperties)
...
```

### 步骤3：创建topic

创建名为“test”的topic，partition数为1，只有一个replica：

```
> bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic test
```

通过list可以看到所创建的topic：

```
> bin/kafka-topics.sh --list --zookeeper localhost:2181
test
```

当然，如果不想每次都手动创建topic，可以将Kafka server配置为自动创建topic。


### 步骤4：发送消息

Kafka安装包里有一些命令行客户端，可以将文件或标准输入的数据发送到Kafka集群。默认情况下，一行是一条消息。

运行producer，输入一些消息：

```
> bin/kafka-console-producer.sh --broker-list localhost:9092 --topic test 
This is a message
This is another message
```

### 步骤5：启动consumer

利用命令行consumer消费消息，并打印到终端：

```
> bin/kafka-console-consumer.sh --zookeeper localhost:2181 --topic test --from-beginning
This is a message
This is another message
```

如果在不同的终端运行上述命令，那么在producer终端输入消息，就可以看到consumer终端输出消息。

所有的命令行工具都有附加选项；运行的时候不加任何参数就会显示详细的使用文档。

### 步骤6：建立多broker集群

到目前为止我们只运行了一个broker。为了感受下多个brokers的集群，将集群扩展为3个节点（还是在本机上）。

创建每个broker的配置文件：

```
> cp config/server.properties config/server-1.properties 
> cp config/server.properties config/server-2.properties
```

编辑配置文件，设置以下属性：

```
config/server-1.properties:
    broker.id=1
    port=9093
    log.dir=/tmp/kafka-logs-1
 
config/server-2.properties:
    broker.id=2
    port=9094
    log.dir=/tmp/kafka-logs-2
```

broker.id属性是集群中每个节点的唯一永久名称。因为我们将3个broker部署在了同一台机器上，为了防止互相干扰，需要修改端口和log目录。

启动新的brokers：

```
> bin/kafka-server-start.sh config/server-1.properties &
...
> bin/kafka-server-start.sh config/server-2.properties &
...
```

现在创建新的topic，replication factor为3：

```
> bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 3 --partitions 1 --topic my-replicated-topic
```

运行“describe topics”命令：

```
> bin/kafka-topics.sh --describe --zookeeper localhost:2181 --topic my-replicated-topic
Topic:my-replicated-topic	PartitionCount:1	ReplicationFactor:3	Configs:
	Topic: my-replicated-topic	Partition: 0	Leader: 1	Replicas: 1,2,0	Isr: 1,2,0
```

第一行给出了所有partitions的概要。其他行给出了每个partition的具体信息。

* “leader”是负责给定partition所有读写的节点。每个节点都会成为若干个partition的leader。
* “replicas”是拥有此partition的log副本的节点列表，无论是不是leader，或者是不是存活。
* “isr”是“in-sync” replicas集合。是replicas的子集，包含存活并且能追上leader的节点。

在这个例子里，节点1是上述topic的partition 0的leader。

对原来的topic运行此命令：

```
> bin/kafka-topics.sh --describe --zookeeper localhost:2181 --topic test
Topic:test	PartitionCount:1	ReplicationFactor:1	Configs:
	Topic: test	Partition: 0	Leader: 0	Replicas: 0	Isr: 0
```

不出意料，原来的topic没有replicas，并且仅存在于节点0。

再发布一些消息到新的topic：

```
> bin/kafka-console-producer.sh --broker-list localhost:9092 --topic my-replicated-topic
...
my test message 1
my test message 2
^C
```

然后消费消息：

```
> bin/kafka-console-consumer.sh --zookeeper localhost:2181 --from-beginning --topic my-replicated-topic
...
my test message 1
my test message 2
^C
```

现在测试下容错机制。Broker 1是leader，kill掉：

```
> ps | grep server-1.properties
7564 ttys002    0:15.91 /System/Library/Frameworks/JavaVM.framework/Versions/1.6/Home/bin/java...
> kill -9 7564
```

leadership转移到了其中一个slave，节点1已经不在in-sync replica集合里了：

```
> bin/kafka-topics.sh --describe --zookeeper localhost:2181 --topic my-replicated-topic
Topic:my-replicated-topic	PartitionCount:1	ReplicationFactor:3	Configs:
	Topic: my-replicated-topic	Partition: 0	Leader: 2	Replicas: 1,2,0	Isr: 2,0
```

虽然原先写入时的leader挂了，但是消息仍然可以被消费：

```
> bin/kafka-console-consumer.sh --zookeeper localhost:2181 --from-beginning --topic my-replicated-topic
...
my test message 1
my test message 2
^C
```

## 1.4 	生态系统

在主版本外还有大量与Kafka结合的工具。包括流处理系统、Hadoop整合、监控和部署工具，参见[生态系统页面](https://cwiki.apache.org/confluence/display/KAFKA/Ecosystem)。

## 1.5 升级

### 从0.8.1升级到0.8.2

0.8.2与0.8.1完全兼容，所以升级只需停止服务、升级代码、重启服务即可。

### 从0.8升级到0.8.1

0.8.1与0.8完全兼容，所以升级只需停止服务、升级代码、重启服务即可。

### 从0.7升级

0.8中加入了副本机制，是我们的首个向后非兼容版本：主要改动涉及API、Zookeeper数据结构、协议以及配置。从0.7迁移到0.8.x需要[特殊工具](https://cwiki.apache.org/confluence/display/KAFKA/Migrating+from+0.7+to+0.8)，可在不停止服务的情况下进行此迁移。

# 2 API

我们正在重写Kafka的JVM客户端。Kafka 0.8.2包括一个重新编写的Java producer。下一个版本会包括新的Java consumer。这些客户端会取代现有的Scala客户端，但是为了兼容，它们会共存一段时间。这些客户端会通过单独的jar包发布，原先的客户端还是随着server一起打包的。

## 2.1 Producer API

对于所有使用0.8.2的人来说，我们希望你们直接使用新的Java producer。此版本经过线上环境测试，而且与之前的Scala版本相比，更快，特性更多。使用以下maven co-ordinates即可加入客户端jar包依赖：

```
	<dependency>
	    <groupId>org.apache.kafka</groupId>
	    <artifactId>kafka-clients</artifactId>
	    <version>0.8.2.0</version>
	</dependency>
```

如何使用producer的例子，参见[javadocs](http://kafka.apache.org/082/javadoc/index.html?org/apache/kafka/clients/producer/KafkaProducer.html)。

如果对之前的Scala客户端感兴趣，参见[这里](http://kafka.apache.org/081/documentation.html#producerapi)。


## 2.2 High Level Consumer API

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


## 2.3 Simple Consumer API

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


## 2.4 Kafka Hadoop Consumer API

提供了将数据聚合或导入Hadoop的水平可扩展方案是我们的基本使用案例。为了支持此类案例，我们提供了以Hadoop为基础的consumer，产生很多map tasks以从Kafka集群并发拉取数据。这提供了极快的pull-based Hadoop数据导入性能（仅用少数Kafka服务器就可以跑满网络）。

[hadoop consumer的相关资料](https://github.com/linkedin/camus/)

# 3. Configuration

Kafka使用[属性文件格式](http://en.wikipedia.org/wiki/.properties)中的key-value对作为配置。这些值可以从文件中读取，也可以在程序中设置。

## 3.1 Broker Configs

必要配置如下：

* broker.id
* log.dirs
* zookeeper.connect

Topic级的配置以及默认值会在后面详细说明。

| 属性        | 默认值           | 说明  |
| ------------- | ------------- |:-----|
| broker.id      |       --       | broker在集群内的唯一id，非负整数 |
| log.dirs      | /tmp/kafka-logs      |   Kafa数据存储目录，逗号分隔；创建新的partition时，会选择partition数量最少的目录 |
| port | 9092      |    服务端接受客户端连接的端口 |
|zookeeper.connect| null | 设置zk连接字符串，例如hostname1:port1,hostname2:port2,hostname3:port3。<br>zk还可以设置"chroot"路径，可以将kafka的相关数据放在该节点路径下，这样可以允许多个kafka集群或其他zk相关应用连接该zk集群，例如hostname1:port1,hostname2:port2,hostname3:port3/chroot/path，表示将此集群相关数据放在/chroot/path路径下，注意在启动kafka集群前，必须创建该路径，并且consumers也必须使用此连接字符串 |
| message.max.bytes	| 1000000 | 服务端可接收的消息大小上限，与consumers的maximum fetch size相配合，否则producers有可能发送过大消息，导致消费不了 | 
|num.network.threads|3|处理网络请求的线程数|
|num.io.threads|8|用于执行请求的I/O线程数，应至少超过硬盘数|
|background.threads|10|用于各种后台处理任务的线程数，例如文件删除|
|queued.max.requests|500|在网络线程停止对新请求的读取前，可排队等候I/O线程的最大请求数|
|host.name|null|broker的主机名。如果设置，broker会绑定到此地址。如果不设置，broker会绑定到所有接口，然后将其中之一发布到ZK。|
|advertised.host.name|null|如果设置，则此hostname将是producers、consumers和其他brokers连接的hostname。|
|advertised.port|null|发给producers、consumers和其他brokers用于建立连接的端口。只有在不同于server所绑定端口的情况下才需要设置。|
|socket.send.buffer.bytes|100 * 1024|socket的发送缓冲区大小SO_SNDBUFF|
|socket.receive.buffer.bytes|100 * 1024|socket的接收缓冲区大小SO_RCVBUFF|
|socket.request.max.bytes|100 * 1024 * 1024|服务端可接收的请求大小上限，防止服务端内存耗尽，需比**java heap**更小|
|num.partitions|1|topic的默认partition数，如果topic创建时没有设置partition count|
|log.segment.bytes|1024 * 1024 * 1024|单个log文件大小上限，可以针对各个topic设置|
|log.roll.{ms,hours}|24 * 7 hours|log文件rol的时间上限，可以针对各个topic设置|
|log.cleanup.policy|delete | 值可以是delete或compact。如果设置为delete，当达到大小或时间限制值时就会删除log segments。如果设置为compact，就会利用log compaction清除废弃的records。此设置可以被基于topic的设置覆盖 (参见per-topic configuration部分)。|
|log.retention.{ms,minutes,hours}|7 days|文件保存时间，过时则清理|
|log.retention.bytes | -1 | 文件保存大小，过大则清理 |
|log.retention.check.interval.ms | 5 minutes | retention检测周期 |
|log.cleaner.enable	| false | 要运行log compaction，此设置必须为true。 |
|log.cleaner.threads | 1 | log compaction中用于清理logs的线程数。 |
|log.cleaner.io.max.bytes.per.second| Double.MaxValue | 进行log compaction时log cleaner能够占用的最大I/O量。此设置是为了对cleaner进行限制，避免影响线上请求。|
|log.cleaner.dedupe.buffer.size | 500 * 1024 * 1024 | cleaning期间，log cleaner用于索引和去重的缓冲区大小。如果拥有足够的内存，稍微大点比较好。|
|log.cleaner.io.buffer.size | 512*1024 | log cleaning期间使用的I/O块大小。一般不需要更改。|
|log.cleaner.io.buffer.load.factor | 0.9 | 用于log cleaning的哈希表的负载因子。一般不需要更改。|
|log.cleaner.backoff.ms | 15000 | 检测是否有logs需要cleaning的时间间隔。|
|log.cleaner.min.cleanable.ratio | 0.5 | 此配置控制了log compactor将尝试清理log的频率（假设开启了log compaction）。默认情况下，如果一个log的50%已经被compacted，我们会避免清理此log。这个比率限制了log中因为重复导致的空间浪费 (比率为50%，那么至多50%的log是重复的)。更高的比率意味着清理效率高，空间浪费较少。此设置可以被基于topic的设置覆盖 (参见per-topic configuration部分)。|
|log.cleaner.delete.retention.ms | 1 day | 对于log compacted topic，保留delete标记的时间。如果consumer从offset 0开始消费，为了确保其能够得到最后状态的快照，consumer必须在此时间限制内消费完（否则在消费完之前，delete标记会被去除）。|
|log.index.size.max.bytes | 10 * 1024 * 1024 | 每个log segment的offset索引文件最大大小。注意，我们会预先分配一个这么大的sparse file，当log滚动后将其缩小。当offset索引文件满时，即使log segment未达到log.segment.bytes限制，我们也会创建一个新的log segment。此设置可以被基于topic的设置覆盖 (参见per-topic configuration部分)。|
|log.index.interval.bytes | 4096 | 向offset索引文件添加新条目的字节间隔。 当处理fetch请求时，服务器需要线性扫描这么多字节以查找所要获取的数据在log中开始和结束位置。So setting this value to be larger will mean larger index files (and a bit more memory usage) but less scanning. However the server will never add more than one index entry per log append (even if more than log.index.interval worth of messages are appended). In general you probably don't need to mess with this value. |
|log.flush.interval.messages | Long.MaxValue | 强制fsync log之前对一个log partition写入的消息条数。较小值表示刷磁盘频率较高，但是会影响性能。我们通常建议利用replication保证durability，而非依赖单台服务器的fsync，当然可以将此设置看作双重保障。|
|log.flush.scheduler.interval.ms | Long.MaxValue | log flusher检测是否有log需要flush的时间间隔。|
|log.flush.interval.ms | Long.MaxValue | 对log强制fsync的时间间隔。与log.flush.interval.messages结合使用，其中一个条件满足，就会调用fsync。|
|log.delete.delay.ms | 60000 | 从内存segment索引中删除log文件后保留log文件的时间。在无锁的情况下，这段时间允许正在进行的读取不中断。一般不需要修改。|
|log.flush.offset.checkpoint.interval.ms|	60000	|对最后flush log设置检查点的频率，用于加快恢复速度。一般不需要修改。|
|log.segment.delete.delay.ms	|60000	| 从文件系统中删除文件的等待时间。|
|auto.create.topics.enable|	true	| 是否自动创建topic，如果为true，那么对不存在的topic产生消息或获取其meta信息，都会触发topic的自动创建，默认replication factor和partitions数量。|
|controller.socket.timeout.ms|	30000|	从partition management controller到replicas的命令的socket超时时间。|
|controller.message.queue.size|	Int.MaxValue|controller-to-broker-channels的缓冲区大小|
|default.replication.factor|	1	|自动创建的topic的默认replication factor。|
|replica.lag.time.max.ms|	10000|如果follower过了这个窗口时间还未向leader发送任何fetch请求，leader会将其从ISR (in-sync replicas)中去除，并且认为该follower已经挂了。|
|replica.lag.max.messages|	4000| 如果replica落后于leader这么多消息，leader会将其从ISR中去除，并且认为该follower已经挂了。|
|replica.socket.timeout.ms	|30 * 1000|	发往leader用于拷贝数据的网络请求socket超时时间。|
|replica.socket.receive.buffer.bytes|	64 * 1024|	发往leader用于拷贝数据的网络请求socket接收缓冲区。|
|replica.fetch.max.bytes|	1024 * 1024|	replicas发给leader的对每个partiton的fetch请求中，想要获取的消息字节数。|
|replica.fetch.wait.max.ms|	500|	replicas发给leader的fetch请求中，等待数据到达leader的最长时间。|
|replica.fetch.min.bytes|	1|	对于replica发出leader的fetch请求，fetch回应中想要的最少字节数。如果不够，等待replica.fetch.wait.max.ms。|
|num.replica.fetchers|	1|	用于从leader拷贝数据的线程数。增大此值可以增加follower的I/O并发度。|
|replica.high.watermark.checkpoint.interval.ms|	5000|	每个replica保存high watermark到磁盘的频率，保存high watermark用于故障恢复。|
|fetch.purgatory.purge.interval.requests|	1000|	The purge interval (in number of requests) of the fetch request purgatory.|
|producer.purgatory.purge.interval.requests|	1000|	The purge interval (in number of requests) of the producer request purgatory.|
|zookeeper.session.timeout.ms|	6000|	ZooKeeper session超时时间。如果服务器一段时间未发送心跳给Zookeeper，则会被Zookeeper认为已经挂了。|
|zookeeper.connection.timeout.ms|	6000|	客户端等待与zookeeper建立连接的超时时间。 |
|zookeeper.sync.time.ms|	2000|	ZK follower可以落后ZK leader多远。|
|controlled.shutdown.enable|	true|	是否启用broker的受控关闭。如果启用，在关闭前broker会将leader转移到其他brokers。减少了关闭窗口期服务不可用的时间。|
|controlled.shutdown.max.retries|	3| 完成受控关闭过程的最大重试次数，超过这个次数就强制关闭。|
|controlled.shutdown.retry.backoff.ms| 5000 | 关闭重试的退避时间。|
|auto.leader.rebalance.enable|	true|	如果启用，controller会自动尝试在broker之间平衡partition的leadership，通过周期性地将leadership返回给每个partition的"preferred" replica，如果该replica可用的话。|
|leader.imbalance.per.broker.percentage|	10|	允许的每个broker的leader不平衡比例。如果每个broker的不平衡比例超过此配置值，controller会重新平衡leadership。|
|leader.imbalance.check.interval.seconds|	300| 检测leader是否平衡的频率。|
|offset.metadata.max.bytes|	4096|	client与offset一起保存的meta数据大小限制。|
|max.connections.per.ip | Int.MaxValue |broker允许的一个ip地址最大连接数。|
|max.connections.per.ip.overrides| -- | 单个ip或主机名覆盖默认最大连接数。|
|connections.max.idle.ms|600000| 空闲连接超时：服务器socket processor线程关闭超时的空闲连接。|
|log.roll.jitter.{ms,hours} | 0 | 与logRollTimeMillis之差的最大抖动。|
|num.recovery.threads.per.data.dir | 1 | 用于启动时log恢复和关闭时每个数据目录的线程数。|
|unclean.leader.election.enable|	true|	是否可以将非ISR的replica选举为leader，即使可能会损失数据。|
|delete.topic.enable | false | 是否可以删除topic。|
|offsets.topic.num.partitions | 50 | offset commit topic的partition数。在部署以后无法动态修改这个值，所以尽量设置高一些（例如，100-200）。|
|offsets.topic.retention.minutes | 1440 | 时间超过此值的offsets会被标记为删除。log cleaner compacts the offsets topic时会做实际的清除。|
|offsets.retention.check.interval.ms | 600000 | offset manager检测旧offsets的频率。|
|offsets.topic.replication.factor | 3 | offset commit topic的replication factor。为了保证高可用性，设置较高的值（例如，3或4）。当broker数量小于offset topic的replication factor时，创建的offsets topic只有较少的replicas。|
|offsets.topic.segment.bytes|	104857600|offsets topic的segment大小。因为使用了compacted topic，这个值应该相对较小，为了加快log compaction和负载。|
|offsets.load.buffer.size|	5242880| 当broker成为一组consumer groups的offset manager时，就会出现offset负载（即，当成为offsets topic partition的leader时)。当加载offsets到offset manager的缓存时，此配置对应于从offsets segments读取时的batch size (in bytes)。|
|offsets.commit.required.acks| -1| offset commit成功之前需要的ack数量。类似于producer的ack设置。一般不要修改。|
|offsets.commit.timeout.ms|	5000|	offset commit延迟直到超时，或者所需数量的replicas收到offset commit。与producer请求超时类似。|

在scala类kafka.server.KafkaConfig中有更多broker配置相关的细节。

### Topic级别的配置
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
|cleanup.policy	| delete	| log.cleanup.policy	| 字符串，可以是“delete”或“compact”，是用于旧的log segment的retention策略。默认策略“delete”当达到大小或时间限制值时就会删除log segments。如果设置为“compact”，就会利用log compaction清除废弃的records。|
| delete.retention.ms	|86400000 (24 hours)|	log.cleaner.delete.retention.ms|	对于log compacted topic，保留delete标记的时间。如果consumer从offset 0开始消费，为了确保其能够得到最后状态的快照，consumer必须在此时间限制内消费完（否则在消费完之前，delete标记会被去除）。|
|flush.messages	|None|	log.flush.interval.messages	|强制fsync log之前对一个log partition写入的消息条数。例如，如果设置为1，那么每条消息后都会fsync；如果是5，那么每5条消息才会fsync。通常建议不要使用，用replication保证durability，依赖更高效的操作系统后台刷新。此设置可以被基于topic的设置覆盖 (参见per-topic configuration部分)。|
|flush.ms	|None	|log.flush.interval.ms|	强制fsync log的时间间隔。例如，如果设置为1000，那么每当100ms过去就fsync。通常建议不要使用，用replication保证durability，依赖更高效的操作系统后台刷新。|
|index.interval.bytes	|4096| log.index.interval.bytes | 此设置控制了向offset index加入新的index条目的频率。默认设置确保大概4096字节添加一条。更多的index使得读取可以更靠近log的最终位置，但是index文件会变大。一般不需要更改。|
|max.message.bytes	|1,000,000|message.max.bytes|对于topic，Kafka可以接收的消息大小限制。如果增大此值，也需要增大consumer的fetch size。|
|min.cleanable.dirty.ratio	|0.5|	log.cleaner.min.cleanable.ratio|	此配置控制了log compactor将尝试清理该log的频率（假设开启了log compaction）。默认情况下，如果一个log的50%已经被compacted，我们会避免清理此log。这个比率限制了log中因为重复导致的空间浪费 (比率为50%，那么至多50%的log是重复的)。更高的比率意味着清理效率高，空间浪费较少。|
|min.insync.replicas | 1 | min.insync.replicas | 当producer设置request.required.acks为-1时， min.insync.replicas指定了认为写入操作成功前需要多少replica进行ack。如果未达到，producer会抛出异常（NotEnoughReplicas或NotEnoughReplicasAfterAppend）。<br> 当min.insync.replicas和request.required.acks的结合可以获得更高的durability保障。典型场景是，创建replication factor为3的topic，设置min.insync.replicas为2，以request.required.acks为-1进行发送。那么此配置保证producer在多数replica未收到数据时抛出异常。|
|retention.bytes|	None|	log.retention.bytes|此配置控制log大小上限，若log segment超过此值，则会被丢弃。如果使用“delete” retention策略，则会释放其所占用的空间。 By default there is no size limit only a time limit.|
|retention.ms	|7 days	|log.retention.minutes|	此配置控制保留log的时间上限，若保留时间超过此值，则会被丢弃。如果使用“delete” retention策略，则会释放其所占用的空间。这表示consumers必须消费多快的SLA。|
|segment.bytes	|1 GB	|log.segment.bytes|此配置控制了log的segment文件大小。segment size越大，意味着文件个数越少，retention时粒度越粗。|
|segment.index.bytes|	10 MB|	log.index.size.max.bytes|此配置控制index文件的大小。我们预分配index文件，仅当log滚动时才缩小它.通常无需修改。|
|segment.ms	|7 days	|log.roll.hours|	此配置控制了Kafak强制滚动log的周期,即使log segment未满,以确保retention可以删除或compact旧数据。|
|segment.jitter.ms | 0 | log.roll.jitter.{ms,hours} | 与logRollTimeMillis之差的最大抖动。|

## 3.2 Consumer Configs

必要的consumer配置如下：

* group.id
* zookeeper.connect

| 属性        | 默认值           | 说明  |
| ------------- |:-------------:| :----- |
|group.id | -- | 标定此consumer所属消费者组的唯一字符串。|
|zookeeper.connect|	--	|设置zk连接字符串，例如hostname1:port1,hostname2:port2,hostname3:port3。<br>服务器可能设置了Zookeeper chroot路径，可以将相关数据放在该节点路径下，如果是这样，那么consumer也必须在其连接字符串中设置同样的chroot路径。例如，如果给定chroot路径是/chroot/path，那么连接字符串是hostname1:port1,hostname2:port2,hostname3:port3/chroot/path。|
|consumer.id	|null| 如果未设置则自动生成。|
|socket.timeout.ms|	30 * 1000	|网络请求的socket超时时间。实际的超时时间时max.fetch.wait + socket.timeout.ms。|
|socket.receive.buffer.bytes|	64 * 1024	| 网络请求的socket接收缓冲区大小。|
|fetch.message.max.bytes|	1024 * 1024	| 每个fetch请求中，对于每个topic-partition，尝试获取的消息字节数。获取的消息会被放在consumer的内存中，所以此配置可以控制consumer的内存占用。此配置必须至少大于服务器允许的最大消息，否则有可能producer发送了一些consumer无法消费的消息。|
|auto.commit.enable | true | 如果启用，则会定期自动提交offset。|
|auto.commit.interval.ms|	60 * 1000| 自动提交offset的周期。|
|queued.max.message.chunks|	10|	 缓存的等待消费的消息块数。每个块的大小都可能达到fetch.message.max.bytes。|
|rebalance.max.retries|	4|	当新的consumer加入时，组内consumers尝试“均衡”负载，将partitions平均分配给consumers。如果正在分配的同时，consumer集合发生变化，那么此次重新分配会失败，并且重试。此配置表示最大重试次数。|
|fetch.min.bytes|	1	|对于fetch请求，server需要返回的数据的最少字节数。如果没有足够的数据，则会等待fetch.wait.max.ms。|
|fetch.wait.max.ms	|100|	当服务端没有fetch.min.bytes的数据时，在回应fetch请求之前服务端的阻塞时间。|
|rebalance.backoff.ms	|2000|	重新均衡的重试退避时间。|
|refresh.leader.backoff.ms|	200|	为失去leader的partition决定leader的退避时间。|
|auto.offset.reset|	largest| Zookeeper上没有初始offset或offset越界后 (1)smallest : 自动重置为最小offset (2)largest : 自动重置为最大offset (3)anything else: 抛出异常给consumer。|
|consumer.timeout.ms	|-1|	如果指定的时间间隔内没有可消费的消息，向consumer抛出timeout异常。|
|exclude.internal.topics|	true|	是否将内部topics (例如offsets) 暴露给consumer。|
|partition.assignment.strategy|	range|	"range"或"roundrobin"策略，用于将partitions分配给consumer流。|
|client.id|	group id value|	每个请求中的自定义字符串，用于跟踪调用。逻辑上能够识别发出请求的应用。|
|zookeeper.session.timeout.ms |	6000|	ZooKeeper session超时时间。如果consumer一段时间未发送心跳给Zookeeper，则会被Zookeeper认为已经挂了，就会触发重新均衡。|
|zookeeper.connection.timeout.ms|	6000|	客户端等待与zookeeper建立连接的超时时间。|
|zookeeper.sync.time.ms|	2000|	ZK follower可以落后ZK leader多远。|
|offsets.storage | zookeeper | offset存储位置（zookeeper或kafka）。
|offsets.channel.backoff.ms | 1000	| 重连offset通道或重试offset获取/提交请求时的退避时间。|
|offsets.channel.socket.timeout.ms |	10000| 等待offset获取/提交请求回应的超时时间。此超时时间也用于ConsumerMetadata请求，该请求用于询问offset manager。|
|offsets.commit.max.retries|	5|	offset提交重试次数。只用于关闭时offset提交重试。不用于自动提交线程。也不用于提交offsets之前尝试询问offset coordinator。即，如果consumer meta数据请求失败，那么重试次数不受此限制。|
|dual.commit.enabled | true | 如果使用"kafka"作为offsets.storage，那么还可以向ZooKeeper提交offsets (除了Kafka以外)。从基于zookeeper的offset存储到基于kafka的offset存储时会用到此配置。当指定的consumer group已经将offset提交迁移到kafka后，就可以关闭这个配置。|
|partition.assignment.strategy|	range|	"range"或"roundrobin"策略，用于将partitions分配给consumer流。round-robin partition分配器列出所有可用partitions和所有可用consumer线程。然后以round-robin的方式将partition分配给consumer线程。如果所有consumer的订阅是相同的，那么partitions会被均匀分配。（即，所有consumer线程占有的partition数量相差不会超过1。) Round-robin分配的条件是: (a) 在consumer实例之间，每个topic拥有相同数量的流； (b) 对于组内每个consumer实例，订阅的topics集合是相同的。<br> Range partitioning是基于topic的。对于每个topic，以数字顺序列出所有partitions，以词典序列出所有consumer线程。将partitions数除以consumer线程数，来决定分给每个consumer多少partition。如果分配不均匀，那么前几个consumers会多分1个partitoin。|

在scala类kafka.consumer.ConsumerConfig.中有更多consumer配置相关的细节。

## 3.3 Producer Configs

必要的consumer配置如下：

* metadata.broker.list
* request.required.acks
* producer.type
* serializer.class

| 属性        | 默认值           | 说明  |
| ------------- |:-------------:| :----- |
| metadata.broker.list | -- | 用于获取元信息（topics，partitions，replicas）的broker url。用于发送实际数据的socket连接是根据所获取的元信息建立的。格式为host1:port1,host2:port2，可以是brokers的子集，也可以是指向子集的VIP |
| request.required.acks | 0 | 指的是确认produce成功需要的ack数量。<br> * 0, 不需要ack（同0.7），低延迟，但是无法保障可靠性（服务挂了以后会导致数据丢失）<br> * 1, leader副本写成功即可（仅会丢失写入到出故障的leader但未同步到其他副本的数据）<br> * -1，in-sync副本都写成功。但是无法完全避免丢数据，因为in-sync在有些情况下可能只有1个副本。如果想要确保in-sync的副本数不低于一定数量，需要设置topic级别的min.insync.replicas setting |
| request.timeout.ms | 10000 | 在达到指定request.required.acks之前，broker的等待时间，超时后会发送错误给client |
| producer.type | sync | * sync，同步发送 <br> * async，异步发送，交给client的后台线程去发送，可以批量发送以增加吞吐，但是发送失败时会丢弃数据 |
| serializer.class | kafka.serializer.DefaultEncoder | 消息的serializer类。默认的encoder将参数原样返回 | 
| key.serializer.class | -- | key的serializer类，不指定的话与消息的默认serializer行为类似 |
| partitioner.class | kafka.producer.DefaultPartitioner | 消息的partitioner类，默认的partitioner是根据key进行hash来选择partition |
| compression.codec | none | 消息压缩类型，none，gzip，snappy | 
| compressed.topics | null | 指定将以上指定的压缩类型施加到哪些topic上，如果为null，则施加到所有topic上 |
| message.send.max.retries | 3 | 消息发送重试次数（注意：ack丢失的情况下，有可能造成消息重复发送）|
| retry.backoff.ms | 100 | 在每次重试前，producer会刷新相应topic的元信息，以检测是否有新的leader。leader选举需要一些时间，所以此属性指定了producer在刷新元信息之前的等待时间 | 
| topic.metadata.refresh.interval.ms | 600 * 1000 | 在（partition missing，leader不可用）时，producer会刷新topic元信息，还有就是按照该属性的值定期刷新。<br> * 如果此值为负数，那么就不会定期刷新。<br> * 如果设置为0（不建议），每条消息发送完以后都会刷新，如果不发送任何消息，那么就不会刷新元信息 | 
| queue.buffering.max.ms | 5000 | 采用async发送模式时，缓存数据的最长时间。例如设置为100，producer会尝试积累100ms的消息以一次发送，提高吞吐，但是会增加延迟 | 
| queue.buffering.max.messages | 10000 | 采用async发送模式时，在producer必须被阻塞或必须丢弃数据前，其队列中可以缓存的消息最大条数 |
| queue.enqueue.timeout.ms | -1 | 在异步模式下，如果消息缓存已经达到了queue.buffering.max.messages，在丢弃消息之前，producer等待的时间。<br> * 如果设置为0，那么消息要么马上入队列，要么因为队列满而直接返回失败（即，非阻塞）。 <br> * 如果设置为-1，调用会一直阻塞直到入队列成功 |
| batch.num.messages | 200 | 在异步模式模式下，批量发送的消息条数。在达到这个数量，或时间达到queue.buffer.max.ms时发送 |
| send.buffer.bytes | 100 * 1024 | socket的发送缓冲区大小 |
| client.id | "" | client.id是每个请求中加入的用户自定义字符串，用于跟踪调用。在逻辑上应该标识发出请求的应用 |

与producer配置相关的更多细节请参见scala类

kafka.producer.ProducerConfig.

## 3.4 New Producer Configs

我们正在替换旧的producer。新的producer代码在trunk里可以找到，是beta版本。新producer的配置如下

| 名称        | 类型           | 默认值  | 重要程序 | 说明 |
| ------------- |-------------| ----- | ---- | :---- |
| bootstrap.servers | list | -- | high | 用于与Kafka集群建立最初连接的host/port列表。数据将在所有服务器之间进行均衡，而与此处用于引导的服务器无关——此列表仅对用于发现所有服务器集的最初hosts有作用 | 
| acks | string | 1 | high | producer在确认请求已完成前需要leader收到的ack数 <br> * acks = 0 	producer不等待任何ack，record会被立即写入socket buffer，并认为已被发送。在这种情况下，无法确定服务器是否已经收到record，并且retries将不起作用（client无法知道是否发送失败）。收到的对每个record的offset常为-1 <br> * acks = 1 leader会将record写入本地log并回应，而不等待其他server对此record的ack。在这种情况下，如果leader在确认完此record后，其他server复制此record之前挂了，那么此record将丢失 <br> * acks = all leader会等待所有in-sync服务器对此record的ack。至少一台in-sync服务器存活就可以保证record不丢失，这是最强的可用保障 <br> * 其他配置如acks = 2也可用，需要相应数量的acks，这种策略使用得较少|
| buffer.memory | long | 33554432 | high | producer可用于缓存record的内存bytes总数，这些record等待被发送到server。根据block.on.buffer.full指定的偏好，如果发送record的速度大于传输到server的速度，producer将阻塞或抛出异常。 <br> 此设置约等于producer将使用的内存总量，但并非硬约束，因为producer使用的内存并非都用于缓存，还有一些额外的内存用于压缩（如果开启压缩功能），以及保持in-flight请求|
| compression.type | string | none | high | 用于producer产生的所有数据的压缩类型，默认为none（即，不压缩）。有效值为none，gzip或snappy。压缩是针对全批量的数据，所以分批的效果也会影响压缩率（批量数据越多，压缩越好）|
| retries	| int | 0	| high | 设置为大于0的值，client会对可能因暂时的错误而发送失败的record进行重发。注意，此重试与client检测到发送错误而重试没有任何区别。允许重试可能会改变record送达的顺序，因为两条record被发送到同一个partition，第一条发送失败而被重试发送，第二条发送成功，那么第二条可能会比第一条先送达 | 
| batch.size | int | 16384 | medium | 当多条records被发送到同一个partition时，producer会尽量将多条records集中到少数request中，有助于提高client和server的性能。此配置为默认的批量bytes数。<br> 批量的record小于等于此配置。 <br> 发送到server的请求包含多个batch，每个batch只包含要发送到同一个partition的数据。 <br> batch size太小会导致批量不太常见，可能会降低吞吐（batch size为0会关闭批量功能）， batch size太大会导致需要预先分配的内存空间过大，浪费分配而未使用的内存空间 |
| client.id | string | -- | medium | 在发出请求时，此id字符串会传递到server。目的是跟踪请求源，不只使用ip/port，还可以使用包含在请求中的逻辑应用名。应用可以设置任何字符串，因为除了logging和metrics，此字符串没有任何其他作用。|
| linger.ms | long | 0 | medium | 在传输请求之前，producer会将所有record打包到同一个批量请求中。通常，这只会在发送速度大于传输速度的情况下发生。然而，在某些环境下，即使在负载不高，client也希望能减少请求数量。此设置通过加入少量人为的延迟而达到此目的——即，并非立即发出请求，而是等待指定的延迟，以使更多的record被打包到同一个请求中。类似于TCP的Nagle算法。此设置给出了延迟的上限：如果批量的record达到batch.size，请求会被立即发送，而忽略此延迟；如果没有达到batch.size，则等待指定的时间。默认值为0（即，无延迟）。例如，设置linger.ms=5，会减少请求数量，但是会对负载较小的情况下发送的record增加5ms的延迟。|
| max.request.size | int | 1048576 | medium | 请求的大小上限。也是record大小上限的上限。注意，server的record大小上限可能与此值不同。此设置会限制单个请求中的record batch数量，以避免产生过大的请求。 | 
| receive.buffer.bytes | int | 32768 | medium | 读取数据时，TCP的接收缓存大小 |
| send.buffer.bytes | int | 131072 | medium | 发送数据时，TCP的发送缓存大小 |
| timeout.ms | int | 30000 | medium | 此配置控制了server等待follower的ack数达到producer通过acks配置指定的数量的时间，超时时如果仍未达到要求的acks数，server会返回错误。此超时是server端检测的，不包括请求的网络延迟。 |
| block.on.buffer.full | boolean | true | low | 当缓存耗尽时，要么停止接收新的record，要么抛出异常。默认值为true，即阻塞。然而某些场景下，不希望阻塞而是立即返回错误。设置为false，则当发送record而缓存已满时，会抛出BufferExhaustedException异常。|
| metadata.fetch.timeout.ms | long | 60000 | low | 数据第一次发往某topic时，必须获取与该topic相关的meta信息，以了解容纳此topic的partition的服务器。此设置控制在获取到meta信息之前的阻塞时间上限，超时且未成功获取则向client抛出异常。 |
| metadata.max.age.ms | long | 300000 | low | meta信息的强制刷新时间，即使没有检测到partition leadership的变化（通过此变化可以发现新的broker或partition） |
| metric.reporters | list | [] | low | 用作metrics reporters的类列表。实现MetricReporter接口则可以加入到可获取到新metric创建通知的类中。JmxReporter总是被包含，以注册JMX数据。|
| metrics.num.samples | int | 2 | low | 用于计算metrics而维持的样本数 | 
| metrics.sample.window.ms	| long | 30000 | low | metric系统维持了可配置数量的样本，间隔固定的窗口大小。此配置控制窗口大小。例如，保存两个样本，每隔30秒测量一次，窗口超时时，则覆盖旧的窗口 |
| reconnect.backoff.ms | long | 10 | low | 连接失败后，再次尝试重连之前等待的时间，防止client在循环中频繁重连。|
| retry.backoff.ms | long | 100 | low | 重试失败发送请求之前的等待时间，防止在循环中频繁重试。|


# 4. Design
## 4.1 Motivation

设计kafka是为了将其作为大公司所有处理实时数据流的统一平台。为了做到这一点，需要考虑多个常见的使用场景。

具有高吞吐，以支持海量事件流，例如日志聚合。

能够优雅地处理大量的数据积压，以支持来自离线系统的周期性数据负载。

能够进行低延迟的递送，以支持更多的传统消息使用场景。

我们想要支持这些feed的分区、分布式、实时的处理以产生新的、派生的feeds。这促成了我们的分区和consumer模型。

在需要将流导入其他数据系统时，需要保证机器宕机时的容错。

为了支持这些功能，我们的设计中有一些独特的要素，更像数据库log，而非传统的消息系统。下面将概述这些要素。

## 4.2 Persistence
### Don't fear the filesystem!

Kafka严重依赖文件系统进行消息的存储和缓存。“磁盘很慢”的看法使得人们怀疑持久化架构是否能够提供具有竞争力的性能。事实上磁盘可以很慢，也可以很快，取决于使用方式；设计适合的磁盘结构可以与网络一样快。

关于磁盘性能关键的是，在过去的十年内，磁盘驱动的吞吐与磁盘寻道延迟相差很大。JBOD配置，6个7200rpm SATA的RAID-5阵列的顺序写速度为600MB/sec，而随机写速度为100k/sec，大约6000倍的差距。在所有的使用模式中，顺序读写是最可预测的，操作系统对其进行了大量优化。现今的操作体统提供了预读取和延缓写入技术，预读取大量的数据，将小的逻辑写入合并为大的物理写入，详见[ACM Queue article](http://queue.acm.org/detail.cfm?id=1563874)；甚至[在某些情况下顺序写磁盘比随机写内存还有快！](http://deliveryimages.acm.org/10.1145/1570000/1563874/jacobs3.jpg)

为了补偿这种性能差异，现代操作系统在使用内存作为磁盘缓存上越来越激进。现代OS愿意将*所有*空闲内存都用于磁盘缓存，虽然会带来一些内存回收时的性能损失。所有的磁盘读写都会经过这个统一的缓存。除非使用direct I/O，否则无法轻易关闭此特性，即使应用程序在进程内部进行了数据的缓存，此数据也会在OS的pagecache中复制一份。

此外，我们构建在JVM之上，Java内存使用具有以下缺点：

1. 对象的内存开销非常高，常常是存储数据的两倍（或者更高）。
2. Java的垃圾回收会随着堆内数据增加而越来越慢。

基于这些考虑，使用文件系统，依赖pagecache要优于in-memory cache或其他架构——通过对所有空闲内存的自主访问，至少使得可用cache翻倍，通过存储紧凑的byte结构而非独立的对象，可能会使得可用cache再次翻倍。在没有GC损耗的情况下，可以从32GB的机器上获取到28-30GB的cache。此外，即使重启服务，OS的cache也会保持warm，然而进程内cache需要重新构建（10GB cache需要10分钟左右）或者需要在cold cache的情况下启动（很可能会导致低下的初始化性能）。这也简化了代码，因为保持cache和文件系统同步的逻辑现在在OS中，比在进程内的一次性处理更加高效和正确。如果你的应用偏向于顺序读取，则预读取会在每次读取时使cache预先存储有用的数据。

所以设计很简单：不是在内存中保存大量的数据，当内存不足时一次性地存入文件系统，而是将数据立即写入文件系统中的持久log，而不刷入磁盘。实际上表示数据转入内核的pagecache。

这种以pagecache为中心的设计详见有关Vanish设计的[文章](http://varnish.projects.linpro.no/wiki/ArchitectNotes)。

### Constant Time Suffices

消息系统中使用的持久化数据结构常常是per-consumer队列，带有相关的BTree或一般的随机读取数据结构，用于维护消息的meta信息。BTree是一种多用途的数据结构，使得其支持消息系统中的多种transactional和non-transactional语义。当然，代价也很大：BTree操作的时间复杂度为O(logN)。通常O(logN)被认为大体上等同于常量时间，但是对于磁盘操作并非如此。磁盘寻道一次10ms，一块磁盘同时只进行一次寻道，所以限制了并发。所以即使少数的磁盘寻道也会导致很大的开销。因为存储系统将很快的缓存操作与很慢的物理磁盘操作混合起来，在固定cache情况下，观测到的树结构性能对比数据增长为超线性，即数据翻倍会使得性能更差，降幅超过一半。

直觉上，类似loggding的解决方案，持久性队列可以建立在简单的读取和对文件的追加上。这种架构的优点是所有操作都是O(1)，读取也不会阻塞写入或其他读取。这具有明显的性能优势，因为性能与数据量无关——一个服务器可以完全利用几个廉价、低转速1+TB SATA驱动器。虽然寻道性能差，但是这些驱动器对于大量读写的性能可以接受，而且价格降为1/3，容量升为3倍。

在不降低性能的情况下拥有理论上无限的磁盘空间，我们可以提供一些消息系统不太常见的特性。例如，在Kafka中，不会在消息被消费以后立即尝试删除该消息，而是可以将消息保存一段时间（例如，一周）。这使得consumer具有很高的灵活性，我们将会对此进行说明。

## 4.3 Efficiency

我们对提高性能付出了诸多努力。我们最主要的使用场景之一就是处理web活动数据，量非常大：每次page view会产生多次写。此外，我们假设每条消息至少被一个消费者读取（常常被多次读取），因此我们尝试让消费尽可能廉价。

从构建类似系统的经验中我们得知，效率是有效的multi-tenant操作的关键。如果下游基础服务会因为应用程序中的小的bump而很容易变成瓶颈，那么这种小的更改很可能会产生大问题。我们需要保证在基础服务出问题之前应用程序先出问题。对于一个集群上支持数十或数百应用的中心服务，这真的很重要，因为这种服务的使用模式每天都在变化。

在前一小节中我们讨论了磁盘效率。一旦去除了低效的磁盘访问模式，这种系统中还有两种常见的低效因素：过多的小I/O操作，以及过多的字节拷贝。

为了避免，我们的协议是围绕“message set”抽象来构建的，消息组将消息集合在一起。这使得网络请求可以将消息组合在一起，减小rtt的开销，而非一次发送一条消息。server也可以将大量消息一次性写入log，consumer也可以一次性获取大量连续的消息。

这种简单的优化产生了数量级的加速。批量导致更大的网络包，更大的顺序磁盘操作，连续的内存块等等，这些都使得Kafka将随机消息写入的突发流转为流向consumer的顺序流。

另一个低效因素为字节拷贝。低消息发送速率的情况下这不是问题，但是在负载较高情况下影响很大。为了避免，我们在producer、broker、consumer之间采用一种标准化的二进制消息格式（这样数据块在它们之间传输时便不需要被改变）。

broker保存的消息log本质上只是放在一个文件夹下的文件。充满写入磁盘的消息组序列，格式与producer和consumer所使用的格式无异。保持这种格式可以对最重要的操作进行优化：持久性log块的网络传输。针对从pagecache到socket的数据转移，现代Unix操作系统提供了一种高度优化的代码路径；在linux中，这是通过sendfile系统调用实现的。

为了理解sendfile的影响，理解数据从文件转移到socket的常见路径非常重要：

1. 操作系统将数据从磁盘读取到pagecache；
2. 应用从内核空间将数据读取到用户空间缓存；
3. 应用将数据写回到内核空间，进入socket缓存；
4. 操作系统将数据从socket缓存拷贝到NIC缓存，网卡会将其发送出去。

四次拷贝，两次系统调用，显然非常低效。使用sendfile，OS可以直接从pagecache中将数据直接发送到网络。所以在优化的路径中，只有最后NIC缓存的拷贝是必须的。

我们希望的使用场景是多个消费者消费一个topic。使用zero-copy优化，数据仅被拷贝到pagecache一次，在每次消费时被重复使用，而非保存在内存，每次被拷贝到内核空间。这使得消息以接近网络速率限制的速率被消费。

pagecache和sendfile的结合意味着，对于consumers都差不多跟上的Kafka集群来说，不会有太多对磁盘的读取活动，因为大部分数据是从cache中读取的。

关于Java中对sendfile和zero-copy的支持，详见[这篇文章](http://www.ibm.com/developerworks/linux/library/j-zerocopy)。

### End-to-end Batch Compression

在某些情况下，瓶颈不在于CPU或磁盘，而是网络带宽。尤其是对于在不同数据中心之间经过广域网传输消息的数据管道来说。当然，不需要Kafka的支持，用户也可以对其消息进行压缩，但这会导致很低的压缩率，因为大部分冗余是由同类消息之间的重复造成的（例如，JSON中的field名称、web日志中的user agents或一般的字符串）。有效的压缩需要对多条消息进行压缩，而非每次压缩一条消息。

Kafka通过递归的消息组来支持压缩。消息可以聚成一批进行压缩，以此格式被发送到server，此批消息以压缩的格式写入log并维持压缩状态，直到consumer获取到以后才会对其进行解压。

Kafka支持GZIP和Snappy压缩协议。关于压缩，详见[此处](https://cwiki.apache.org/confluence/display/KAFKA/Compression)。

## 4.5 The Consumer

Kafka consumer通过向主导其想要消费的partition的broker发出“fetch”请求来运行。consumer在每个请求中加入log中指定的offset，并接收从该位置起的大块log。consumer就可以自如得控制此位置，通过倒回，可以重新消费已经消费过的数据。

### Push vs. Pull

一个我们最初考虑的问题是，consumer应该从broker拉取数据，还是broker主动推送数据到consumer。在这一点上，Kafka沿用了大多数消息系统采用的传统设计，即，数据被producer推送到broker，而被consumer从broker拉取。一些logging-centric系统，例如Scribe和Flume采用一种不同的基于推送的路径，数据是被推送到下游的。两种方法各有利弊。基于推送的系统在处理各种各样的consumer时有困难，因为broker控制数据被传输的速度。目的是为了使consumer以尽可能快的速度消费数据；但不幸的是，在推送系统中，当consuemr的消费速度低于生产速度时（例如，拒绝服务攻击），consumer可能会被压垮。基于拉取的系统就不会有这个问题，consumer调整拉取的速度。当然consumer可以借助一种backoff的协议表示其不堪重负，虽然可以缓解，但是要完全利用传输速率（不过度传输），需要很多技巧。此前构建这种系统的经验指导我们采用更传统的拉取模型。

基于拉取的系统的另一个优势是适用于批量发送数据给consumer。基于推送的系统需要选择，是立即发出请求，还是积攒一批数据，在不知道下游是否能够立即处理的情况下发送。如果要求低延迟，那么会导致为了传输一次只发送一条消息，即使缓存在consumer端，这会浪费带宽。基于拉取的系统会拉取log中当前位置后的所有可用消息（或达到一次拉取的上限值）。所以可以在不引入不必要延迟的情况下，取得更好的批量效果。

基于拉取的系统的缺点是如果服务端没有数据，consumer会忙等待。为了避免，在拉取请求中有参数可以使consumer的请求阻塞在“long poll”，等待直到数据到达（或者等待一定量的数据到达，以确保大的传输量）。

也可以想一下仅基于拉取的系统。producer将消息写入本地log，broker从producer处拉取数据，consumer从broker拉取数据。可以提出一种”存储-转发”类型的producer。这很有趣，但是我们觉得与我们的目标使用场景相去甚远，其中有数千个producer。我们关于运行持久化数据系统的经验使我们认识到，在运行众多应用的系统中涉及数千块磁盘，并不会使系统更可靠，而且难以运维。在实践中，我们发现可以在不需要producer进行持久化的情况下，以很高的SLA运行大规模pipeline。

### Consumer Position

跟踪*什么*被消费了竟然也是消息系统的一个关键性能点。

大多数消息系统将消息被消费的meta信息保存在broker上。即，当消息被发往consumer时，broker要么立即在本地对此进行记录，要么等待consumer的ack。这是很自然的选择，而且对于单个机器的服务器，确实无法知道还能将状态存在何处。因为许多消息系统中用于存储的数据结构的可扩展性差，这样也是一个务实的选择——因为broker能够什么消息被消费了，可以立即删除此消息，以节约存储空间。

不明显的是，要使broker和consumer就什么被消费这点达成一致不是简单的事情。如果broker在一发送完消息后就将消息标记为已被消费，那么如果消费者没有成功处理该消息（例如，consumer崩溃或请求时间超时等），此消息就相当于丢失了。为了解决此问题，许多消息系统增加一种确认机制，即消息发出后，仅将其标记为已发出而未消费，broker等待consumer的特定确认，已将消息标记为已消费。这种特性解决了消息丢失的问题，但是又产生了新问题。首先，如果消费者消费了消息，而在发出确认之前挂了，那么消息将被重复消费。第二个问题是性能，现在broker必须保持与一条消息有关的多个状态（首先需要锁定该消息，以免被重复发送，其次需要将其标定为已消费，以便删除该消息）。有些棘手的问题需要解决，比如如何处理已经发出但是一直未收到确认的消息。

Kafka的处理方式不同。我们的topic被分为一组绝对有序的partition，每个partition同时仅被一个消费者消费。这意味着consumer对每个partition的位置只是一个整数，即下一条要消费的消息偏移。这使得与消费相关的状态很小，对于每个partition仅一个数字。此状态可被定期检查。使得消息的确认也非常容易。

此决定也有额外的好处。consumer可以倒回到过去的offset对数据进行重新消费。这违反了队列的通常定义，却成为许多consumer必不可少的特性。例如，如果consumer的代码有bug，而且是在消费了一些消息之后才发现，那么在修改bug以后，可以重新消费以前的数据。

### Offline Data Load

可扩展的持久化允许consumer定期消费批量数据，或定期将大块数据载入离线系统，例如Hadoop或关系型数据仓库。

在Hadoop中，我们通过将数据负载分发给独立的map任务而将负载并行化，每个任务对应每个node/topic/partition组合，允许负载的全并行化。Hadoop提供了任务管理，挂了的任务可以重新启动，而不会造成数据重复——只是从原先的位置重启。

## 4.6 Message Delivery Semantics

我们已经了解了一些producer和consumer的运行机制，接着来看下在producer和consumer之间，Kafka提供的语义保障。显然有多种语保障义可以提供：

* 至多一次——消息可能会丢失，但不会被重复递送。
* 至少一次——消息不能丢失，但可能会被重复递送。
* 恰好一次——这是人们真正想要的，消息被递送仅且一次。

可以很容易将此问题分解为两个问题：发布消息和消费消息的durability guarantees。

许多系统声称提供“恰好一次”的递送语义，但最好看下其附加细则，大多数这种声明具有误导性（即，它们不考虑以下情况，consumer或producer可能会挂，或者存在多个consumer进程，或者被写入磁盘的数据不会丢失）。

Kafka的语义很直接。发布消息时我们有消息“已提交”到log的概念。只要发布的消息已提交，那么只要复制该消息的partition所在broker“存活”，那么消息就不会丢失。下一小节将会对“存活”的概念和要处理何种失败进行说明。现在假设broker很完美，不会丢失任何消息，在此假设下理解producer和consumer的保障。如果producer尝试发布一条消息，遇到了网络错误，它无法判断此错误是发生在消息被提交之前还是之后。类似于对具有自动生成key的数据库表进行插入的语义。

对于producer，没有最强的可能语义。虽然在产生网络错误的情况，我们无法判断发生了什么，可以使producer产生一种“主键”，使得发送请求的重试是幂等的。对于replicated系统来说这个特性也很重要，因为甚至（尤其）是在服务器宕机的情况下，这也必须成立。

具有这种特性，producer就可以一直重发消息，直到收到说明已提交的ack，此时我们可以确定消息恰好被发布一次。希望在未来的Kafka版本中加入此特性。

并非所有的使用场景都需要这么强的保障。对于延迟敏感的应用，我们允许producer指定durability等级。如果producer指定要等待消息被提交，这可以接受10ms级别。然而，producer也可以说明，想要完全异步执行发送操作，或者仅等待leader存储了该消息。

现在我们从consumer角度说明下语义。所有replica具有完全相同的log和offset。consumer控制其在log中的位置。如果consumer永远不会崩溃，那么可以将此位置保存在内存中，但是如果此消费者挂了以后，我们希望新的消费者进程来接管这个topic partition，其需要选择合适的位置开始处理。比方说consumer读取了一些消息——其有几种可选的方式来处理消息并更新位置。

1. 读取消息，将位置保存在log中，然后处理该消息。这种情况下，有可能consumer在保存位置之后挂了，而没有输出消息处理的结果。在这种情况下，接管处理的进程会从上次保存的位置开始，即使此位置之前的消息没有被处理。这对应于“至多一次”的语义，因为在consumer发生故障的情况下，消息有可能没被处理。
2. 读取消息，处理消息，保存位置。有可能成功处理了消息，但是在保存位置之前，消费者挂了。在这种情况下，接管的新consumer最初接收的几条消息已经被处理过了。这对应于“至少一次”的语义。在许多情况下，消息具有相同主键，因此其更新是幂等的（对于相同的消息，后来者会覆盖前者）。
3. 那么恰好一次的语义呢（即，真的是你想要的吗）？此处的局限实际上并非消息系统的特征，而是consumer位置和实际上存储输出之间的协调。要达到此目的的典型方法是，在consumer位置和consumer输出的存储之间引入**两阶段提交**。但是通过将consumer的位置和输出存储在一起的方法就可以解决该问题，而且这种解决办法更简单、更常用。这种方式更好，因为consumer要写入的输出系统并不支持两阶段提交。例如，为HDFS输入数据的Hadoop ETL将offset与其读取的数据一起存入HDFS，保证offset和数据要么都被更新，要么都没有更新。我们允许这种模式，对于需要这些更强的语义的许多其他数据系统，或者消息不包含主键无法进行去重。

所以Kafka默认保证至少一次的语义，允许用户通过禁止producer重发并且consumer在处理之前提交位置，实现至多一次的语义。恰好一次的语义需要目的存储系统的协作，而Kafka提供的offset使得此语义的实现并不难。

## 4.7 Replication

Kafka在多个server之间复制每个topic的partition的log（可以对每个topic设置replication factor）。在集群中的一台服务器故障时，这些replica可以自动进行故障切换，所以在故障时消息仍然是可用的。

其他消息系统提供了一些与replication相关的特性，但是，我们认为这是一些附加的东西，并不常用，而且有很大的缺陷：slave不活跃，严重影响吞吐量，需要手动配置等等。Kafka想要默认就使用replication——实际上我们实现的un-replicated的topic也是基于replicated topic，只是其replication factor为1。

replication的基本单元是topic partiton。在无故障的情况下，Kafka中的每个partition有一个leader，零个或多个follower。包括leader在内的所有replicas数量为replication factor。所有的读写都由partition的leader处理。通常情况下，partition的数量比broker的数量多很多，leader是均匀分布在broker上的。follower上的log与leader上的log完全相同——都有相同的offset，相同顺序的消息（当然，在给定时间点上，leader的log尾部存在一些尚未被复制的消息）。

如同普通的Kafka消费者，Follower从leader消费消息，并将消息存入到它们的log中。follower从leader主动拉取的方式，使follower可以对要存入log的消息进行批量。

对于自动处理故障的大多数分布式系统来说，都需要对节点是否“存活”有一个明确的定义。对于Kafka节点的存活有两个条件：

1. 节点能够保持与Zookeeper的会话（通过Zookeeper的心跳机制）
2. 如果是slave节点，必须跟上leader的写入，不能落后“太远”

我们将满足以上两点的节点称为“in sync”，以避免“alive”或“failed”的模糊定义。leader跟踪“in sync”节点组。如果follower死了、卡住或落后，leader会将其从in sync replica列表中移除。落后多远表示落后太远，是由replica.lag.max.messages配置控制的，replica卡住的定义是由replica.lag.time.max.ms配置控制的。

在分布式系统术语中，我们仅处理“fail/recover”模型，也就是说，发生故障时，节点突然停止运行，然后后面恢复运行（也许不知道曾经死过）。Kafka不处理所谓的“Byzantine”故障，其中节点会产生随机或恶意的回应（也许因为bug或攻击）。

仅当partition的所有in sync replica将消息加入到log中后，该消息才被认为是“已提交”。只有已提交的消息才会给消费者。意味着消费者不会因为leader故障而感知到消息丢失。另一方面，producer可以等待或不等待消息被提交，取决于它们对延迟和durability之间折中的偏好，这种偏好是由request.required.acks setting配置控制的。

Kafka保证，只要至少一个in sync replica活着，已提交的消息就不会丢失。

Kafka在出现短暂的节点故障期间仍是可用的，但是出现网络分区的情况下可能会不可用。

### Replicated Logs: Quorums, ISRs, and State Machines (Oh my!)

Kafka partition的核心是replicated log。replicated log是分布式数据系统中最基本的原语，有许多实现方法。replicated log可以在其它系统中用作原语，用来以[状态机](http://en.wikipedia.org/wiki/State_machine_replication)的方式实现其它分布式系统。

replicated log对就一系列值的顺序（通常对log条目进行编号：0,1,2 ...）达成共识的过程进行了建模。有许多方法可以实现，最简单最快速的方法是，leader决定值的顺序。只要leader存活，所有的follower只需要拷贝值和顺序。

当然，如果leader不故障，我们不会需要follower！当leader挂了时，需要从follower中选择一个新的leader。但是follower可能落后或者崩溃，所以需要选择最新的follower。log replication最基本的保障就是如果已经通知client一条消息已提交，如果此时leader故障，那么新leader必须包含这条消息。这会产生一种折中：如果leader在声明一条消息已提交之前等待更多的follower确认这条消息，那么就会有更多的可选leader。

如果在选举新的leader时，选择需要的ack数量和需要比较的log数量，那么就需要涉及到一个保障，即所谓的Quorum。

这种折中的常用方法是对提交决策和leader选举使用多数投票。这不是Kafka采用的方法，但是不妨来讨论下这种方法。假设有2f+1个replica，如果在leader声明消息已提交之前f+1个replica必须收到该消息，如果从至少f+1个replica中选择具有最完整log的follower为新leader，那么，在故障点数量不大于f的情况下，可以确保leader包含所有已提交的消息。因为在f+1个replica中，至少存在一个replica包含所有已提交的消息。此replica的log是最完整的，所以会被选举为新的leader。仍然有很多细节需要讨论（例如，关于log更完整的定义，在leader故障期间确保log一致性或改变replica集合中的server集合），我们暂时先忽略这些。

这种多数投票机制有一个非常好的特点：延迟仅仅取决于最快的服务器。即，如果replication factor是3，那么延迟是由最快的slave决定的。

这类型的算法有很多，包括Zookeeper的Zab、Raft和Viewstamped Replication。与Kafka的实现最类似的学术出版物是微软的[PacificA](http://research.microsoft.com/apps/pubs/default.aspx?id=66814)。

多数投票机制的缺点是，不需要太多节点故障就会造成没有新leader可选。为了容忍一个节点故障，需要三份数据拷贝，为了容忍两个节点故障，需要五份数据拷贝。以我们的经验来看，为了容忍单个故障，仅仅拥有足够的冗余，对于实际系统来说是不够的，每个写入都要5次，需要5倍的磁盘空间，吞吐量会变为原先的1/5，对于大量数据问题来说不是很实用。quorum算法更常用于集群配置共享，如Zookeeper，而不常用于主要数据存储。例如，在HDFS中，namenode的高可用特性构建在基于多数投票的日志上，但是这种开销过大的方法并不用于数据本身。

Kafka采用了一种略微不同的方法来选择quorum集合。不使用多数投票，Kafka动态维护一个能够跟上leader的in-sync replica（ISR）集合。只有这个集合的成员才有资格被选举为leader。只有当所有in-sync replica已经确认，对Kafka partition的写入才算已提交。无论何时ISR改变，都会被保存到Zookeeper。因此，ISR任意一个replica都可以被选举为leader。这是Kafka使用模型的重要因子，即存在许多partition，确保leadership的平衡很重要。利用ISR模型和f+1个replica，Kafka topic可以容忍f个节点故障，而不丢失任何已提交的消息（？？？）。

对于我们想要处理的多数使用场景，我们认为这个折中是合理的。在实践中，为了容忍f个节点故障，多数投票和ISR策略在提交一条消息之前需要等待相同数量的确认（例如，为了容忍一个节点失败，多数quorum需要三个replica和一个确认，而ISR需要两个replica和一个确认）。多数投票机制的一个优势是不需要等待最慢的服务器，但是我们的client可以选择在阻塞时跳过消息确认，因为需要更少的replication，而增加的吞吐和节约的磁盘空间很值得。

另一个重要的设计区别是，Kafka不要求崩溃的节点恢复时需要保证数据完整无损。对于replication算法来说，依赖存储可靠性，在任何故障-恢复场景中都不丢失数据，不违反一致性，也很常见。关于此假设有两个问题，我们不想在每次写入时都为了一致性而调用fsync，因为会使性能降低2到3个数量级。我们的协议要求，即使在节点崩溃时replica丢失了部分未写入磁盘的消息，在重新加入ISR之前，也必须重新完全同步。

### Unclean leader election: What if they all die?

注意，Kafka保障数据不丢失的前提是，至少有一个replica在in-sync集合中。如果一个partition的所有replica挂了，那么数据就丢了。

然后，实际的系统需要应对这种情况，有两种后续的处理可以实现：

1. 等待ISR中的一个replica重新活跃，并选择此replica为leader（希望这个replica的数据没有丢失）。
2. 选择第一个重新活跃的replica为leader，此replica不一定在ISR中。

这是可用性和可靠性之间的折中。我们等待ISR中的replica，那么可能需要等待较长时间。如果这种replica彻底损坏或数据丢失，那么服务就永远不可用了。另一方面，如果不在ISR中的replica重新活跃，将其选为leader，那么虽然可能会丢失一些已提交的消息，但是整个服务还是可用的。在最近的版本中，我们选择第二种策略，如果ISR中的replica都挂了，就选择潜在的非一致replica作为新leader。未来的版本中，我们想要使其可配置，以支持偏向于停止服务而非不一致的使用场景。

这种进退两难的问题不特定于Kafka，其存在于任何基于quorum的方案中。例如，在多数投票方案中，如果多数服务器永久故障，那么必须选择丢失100%的数据，或者违反一致性，选择存活的一个服务器为新的基准。

### Availability and Durability Guarantees

发送消息时，producer可以选择等待多少个replica的ack，0、1或者所有的。注意，“所有replica的ack”并不保证所有的分配的replica都接收了该消息。默认情况下，当request.required.acks=-1时，只要所有的in-sync replica收到了消息就可以确认。例如，如果一个topic只有两个replica，其中一个挂了（即，只有一个in sync replica存活），那么设置request.required.acks=-1的写入会成功。然而，如果存活的replica也挂了，那么该消息会丢失。虽然这保证了partition的最大可用性，但并不是有些用户想要的，有些用户偏向于durability，而非availability。因此，我们提供了两种topic级别的配置，以偏向于durability而非availability。

1. Disable unclean leader election —— 如果所有的replica都不可用了，就一直等待到最新的leader可用为止。
2. 指定最小的ISR大小 —— 仅当ISR大小达到一定的值，partition才接收写入，为了防止仅写入一个replica的消息丢失。这个设置仅在required.acks=-1的情况下生效，并且保证一条消息至少被这个数量的in-sync replica确认。最小ISR大小的值越大，一致性越高，因为保证消息被写入到更多的replica，丢失的可能性降低。但是降低了可用性，因为in-sync replica的数量小于该值，那么对该partition的写入操作都无法进行。

### Replica Management

以上讨论都是关于单个log，即单个topic partition的恢复问题。然而，Kafka集群管理了数百数千个partition。我们以round-robin的方式将partition分散在多个节点上，以避免将大容量topic的所有partition集中在少数节点上。同样，我们也会均衡leadership，以使节点上的leader与partition数量成比例。

优化leader选举过程也很重要，因为在此期间服务不可用。leader选举比较拙劣的实现，会在节点挂掉以后，对此节点包含的所有partition进行重新选举。实际上，我们选举其中一个broker为“controller”。controller检测broker级别的故障，负责为故障broker上受影响的所有partition选举leader。因此，我们可以将许多leader选举的通知打包，使得选举过程更廉价和快速。如果controller故障，那么现存的broker之一变成新的controller。

## 4.8 Log Compaction

log compaction可以保证对于单个topic partition的同一个key，Kafka至少会保留最新的一份数据。可以解决一些使用场景，例如应用程序崩溃或系统故障后的状态恢复，在运行维护期间应用程序重启之后加载cache。

目前为止，我们只说明了数据retention最简单的方法，当数据过期或log达到预定大小后丢弃旧的数据。对于临时性的事件数据，例如日志，因为数据之间没有关联，所以这种方法就可以。然而，很多重要的数据流是按key的、可变的数据（例如，对数据库表的修改）。

我们来看一个实际例子。假设有一个topic包含用户邮件地址；每次用户变更邮件地址，就发送一条消息到此topic，消息的key是用户id。现在假设我们发送了以下消息，用户id是123，每条消息对应一次邮件地址变更（忽略了其他id的消息）：

```
    123 => bill@microsoft.com
            .
            .
            .
    123 => bill@gatesfoundation.org
            .
            .
            .
    123 => bill@gmail.com
```

log compaction给出了一种更粗粒度的retention机制，至少可以保留每个主键的最后一次更新（例如，bill@gmail.com）。通过这种方法，可以保证log保存了每个key的最后值的快照，而不仅仅是最新变更过的key。意味着下游的consumer可以以此topic恢复它们的状态，而不需要Kafka保留所有的变更。

来看几个使用场景。

1. Database change subscription  同一组数据保存在多个系统中再正常不过，这些系统通常都是某种数据库（RDBMS或KV存储）。例如，数据库、cache、search集群、Hadoop集群。对数据库的每次修改都需要反映在cache、search集群、Hadoop中。在仅处理实时更新的系统中只需要最新的log。但是如果想要重新加载cache或者恢复故障search节点，那么就需要完整的数据集。
2. Event sourcing  This is a style of application design which co-locates query processing with application design and uses a log of changes as the primary store for the application.
3. Journaling for high-availability  进行本地计算的进程可以是容错的，通过将其对本地状态的修改记录日志，在此进程故障时，其他进程就可以重新加载这些更改。实际例子就是在流式查询系统中进行统计、聚合或“group by”类型的处理。Samza，实时流式处理框架，就用到这个特性。

在这些使用场景中，主要需要处理变更的实时feed，但是有时候，当机器宕机或数据需要被重新加载或重新处理，就需要做全加载。log compaction能够利用同一个topic支持这两种使用场景的feed。

大意非常简单。如果我们拥有无限的log retention，在以上案例中我们保存每一个变更，那么我们就可以捕获系统从开始到现在的每一个状态。利用这个完整的log，通过重放log的前N个record，可以随时恢复到任意一个点。假设的完整log对于系统来说并不实际，即使对于稳定的数据集，多次更新同一个record，也会使得log持续增大。最简单的log retention机制，丢弃部分旧的数据，可以控制log所占用的空间，但是无法通过log恢复当前的状态——从log的开始无法重做当前的状态，因为旧的更新已经无法获取。

Log compaction是一种针对每条record的细粒度retention机制，而非基于时间的粗粒度retention。思想是选择性地删除同一个主键的旧数据，保证每个主键至少存在最后的状态。

此retention机制是特定于topic的，所以一个集群中，有些topic可以采用大小或时间限制的retention，其他topic可以采用这种compaction的机制。

此功能的灵感来自于LinkedIn最老也是最成功的基础组件——一个数据库changelog缓存服务，[Databus](https://github.com/linkedin/databus)。与多数基于log的存储系统不同，Kafka是为了支持订阅，以及组织数据以进行快速的顺序读写。与Databus不同，Kafka充当了source-of-truth式的存储，在上游数据源无法重放的情况下特别有用。

### Log Compaction Basics

下图显示了Kafka log的逻辑结构，包括每条信息的offset。

![image]({{ site.url }}/images/blog/kafka-0-8-2-documentation/kafka-log-structure.png)

log的头部与传统的kafka log相同，连续的offset，保留了所有消息。log compaction增加了处理log尾部的选择。上图显示了compacted的尾部，注意，log的尾部消息保持了第一次写入时的offset——永远不会改变。注意，所有的offset均表示合法的位置，即使其代表的消息已经被删除；在这种情况下，此offset与其后存在的下一个最高offset并无区别。例如，上图中，36、37和38表示相同的位置，从三者任意位置开始读取，都相当于从38位置开始读取。

Compaction也允许删除。带有key并且payload为空的消息可以作为log的delete标记。此delete标记会导致其之前具有相同key的消息被删除（还有具有相同key的新消息），但是delete标记也会在一段时间后被删除，以释放其所占用的空间。delete不再保留的时间点是“delete retention point”。

compaction是在后台通过周期性地重新拷贝log segment进行的。Cleaning不会阻塞读取，并且可以被限制在一定量的I/O吞吐范围内，以避免影响producer和consumer。实际的compacting过程如下图所示：

![image]({{ site.url }}/images/blog/kafka-0-8-2-documentation/log_compaction.png)


### What guarantees does log compaction provide?

log compaction保证：

1. 任何能够紧追log头部的consumer可以看到写入的每条消息；这些消息具有连续的offset。
2. 消息的顺序性会永远保持。Compaction不会重排消息，只是删除一些。
3. 消息的offset不会变。offset是消息在log位置的永久标识。
4. 任何从offset 0开始的读取过程都至少可以按写入顺序看到所有record的最后状态。在reader在少于delete.retention.ms设定的时间（默认24小时）内到达log头部之前，对删除record的所有delete标记都可见。这很重要，因为删除delete标记与读取同时进行（因此在读者看到之前不要删除delete标记）。
5. 任何从log开头开始的消费过程都至少可以按写入顺序看到所有record的最后状态。在consumer在少于delete.retention.ms设定的时间（默认24小时）内到达log头部之前，对删除record的所有delete标记都可见。这很重要，因为删除delete标记与读取同时进行，因此在消费者看到之前不要删除delete标记）。

### Log Compaction Details

Log compaction 由 log cleaner执行，一批后台线程拷贝log segment文件，删除key出现在log头部的record。每个compactor线程的执行过程如下：

1. 选择头尾比（头部与尾部比例）最高的log
2. 创建log头部中每个key最后offset的简明概要
3. 按照概要从头到尾拷贝相应的数据，相当于去除了前面同一个key的“冗余”数据。将新的，干净的segment文件与原先的segment文件快速互换，因此所需额外磁盘空间就是一个额外的log segment（并非所有拷贝）
4. log头部的概要就是space-compact哈希表。每个条目为24字节，因此8GB的cleaner buffer，一次cleaner迭代可以清理366GB的log头部（假设消息大小为1kB）

注：此处log头部的GB按磁盘的（1000^3）B计算

### Configuring The Log Cleaner

log cleaner默认是关闭的。通过服务端配置可以打开

```
log.cleaner.enable=true
```
就会开启cleaner线程池。要对特定的topic设置log清理，可以增加log-specific特性

```
log.cleanup.policy=compact
```

可以在topic创建时设置，也可以通过alter命令设置。

cleaner配置详见[这里](https://kafka.apache.org/documentation.html#brokerconfigs)。

### Log Compaction Limitations

1. 目前还不能配置保留多少log不被compaction（log的“头部”）。目前，除了最后的segment（即，正在被写入的segment），其他所有的segment都会经过compaction。
2. Log compaction还不能兼容压缩的topic。

# 5. Implementation

## 5.1 API Design

### Producer APIs

Producer API包括2个低级producers —— kafka.producer.SyncProducer和kafka.producer.async.AsyncProducer。

```
class Producer {
	
  /* Sends the data, partitioned by key to the topic using either the */
  /* synchronous or the asynchronous producer */
  public void send(kafka.javaapi.producer.ProducerData<K,V> producerData);

  /* Sends a list of data, partitioned by key to the topic using either */
  /* the synchronous or the asynchronous producer */
  public void send(java.util.List<kafka.javaapi.producer.ProducerData<K,V>> producerData);

  /* Closes the producer and cleans up */	
  public void close();

}
```

目标是通过单一API将producer的功能都暴露给client。新的producer ——

* 可以处理多个producer请求的排队/缓存和批量数据的异步发送 ——
```kafka.producer.Producer```提供了一种功能，可以在序列化和发送请求到合适的kafka broker partition前，对多个produce请求进行batch。batch的大小由几个配置参数控制。当事件进入队列时，它们被缓存在队列中，直到达到```queue.time```或```batch.size```。后台线程（kafka.producer.async.ProducerSendThread）从队列中取出一批数据，由```kafka.producer.EventHandler```将其序列化并发送到合适的broker partition。通过```event.handler```可以插入自定义的event handler。在此producer队列管道的各个阶段，引入回调很有用，或者用于插入自定义logging/tracing代码或自定义monitoring逻辑。通过实现```kafka.producer.async.CallbackHandler```接口，并设置自定义类```callback.handler```配置参数。

* 通过用户指定的```Encoder```对数据进行序列化 ——

```
interface Encoder<T> {
  public Message toMessage(T data);
}
```

默认是空操作```kafka.serializer.DefaultEncoder```

* 通过用户自定义的```Partitioner```提供软件负载均衡 —— 
路由决策受```kafka.producer.Partitioner```的影响。

```
interface Partitioner<T> {
   int partition(T key, int numPartitions);
}
```

partition API参数为key和可用的broker partition数，返回partition id。此id被用作broker_ids和partitions的有序队列的索引，为了给producer的请求选择broker partition。默认的分区策略是```hash(key)%numPartitions```。如果key为null，就随机选择一个broker partition。也可以通过``` partitioner.class ```配置参数插入自定义分区策略。

### Consumer APIs

我们有两个级别的consumer API。低级“简单”API保持到单个broker的连接，并且与发送到服务器的网络请求紧密相关。此API是完全无状态的，每个请求都需要传入offset，允许用户维护meta信息。

高级API隐藏了隐藏了broker的细节，无需了解集群拓扑就可以消费。维护了消费位置的状态。这个API还提供了订阅满足filter表达式的多个topic（即，白名单或黑名单正则表达式）。


#### Low-level API

```
class SimpleConsumer {
	
  /* Send fetch request to a broker and get back a set of messages. */ 
  public ByteBufferMessageSet fetch(FetchRequest request);

  /* Send a list of fetch requests to a broker and get back a response set. */ 
  public MultiFetchResponse multifetch(List<FetchRequest> fetches);

  /**
   * Get a list of valid offsets (up to maxSize) before the given time.
   * The result is a list of offsets, in descending order.
   * @param time: time in millisecs,
   *              if set to OffsetRequest$.MODULE$.LATIEST_TIME(), get from the latest offset available.
   *              if set to OffsetRequest$.MODULE$.EARLIEST_TIME(), get from the earliest offset available.
   */
  public long[] getOffsetsBefore(String topic, int partition, long time, int maxNumOffsets);
}
```

低级API是用于实现高级API，还用于一些离线consumer（例如hadoop consumer），这些consumer对于状态维护有特殊的需求。

#### High-level API

```
/* create a connection to the cluster */ 
ConsumerConnector connector = Consumer.create(consumerConfig);

interface ConsumerConnector {
	
  /**
   * This method is used to get a list of KafkaStreams, which are iterators over
   * MessageAndMetadata objects from which you can obtain messages and their
   * associated metadata (currently only topic).
   *  Input: a map of <topic, #streams>
   *  Output: a map of <topic, list of message streams>
   */
  public Map<String,List<KafkaStream>> createMessageStreams(Map<String,Int> topicCountMap); 

  /**
   * You can also obtain a list of KafkaStreams, that iterate over messages
   * from topics that match a TopicFilter. (A TopicFilter encapsulates a
   * whitelist or a blacklist which is a standard Java regex.)
   */
  public List<KafkaStream> createMessageStreamsByFilter(
      TopicFilter topicFilter, int numStreams);

  /* Commit the offsets of all messages consumed so far. */
  public commitOffsets()
  
  /* Shut down the connector */
  public shutdown()
}
```

此API以迭代器为中心，由KafkaStream类实现。每个KafkaStream代表一个或多个服务器上的一个或多个partition的消息流。每条流用于单线程处理，因此client可以在create时提供所需流的数量。因此，一条流可能代表了多个服务器partiton的合并（以对应处理线程数），但是每个partition只对应一条流。

createMessageStreams调用注册指定topic的consumer，会造成consumer/broker分配的重新均衡。API建议在一个线程中创建多个topic流，以减少这种均衡的次数。createMessageStreamsByFilter调用注册watcher，以发现符合其filter的新topic。注意，createMessageStreamsByFilter返回的每条流可能会迭代来自多个topic的消息（即，如果多个topic通过了filter）。

## 5.2 Network Layer

网络层就是简单的NIO服务器，这里不再详述。sendfile的实现是通过在MessageSet接口实现writeTo方法完成的。这使得以file存储的消息可以使用更有效的transferTo实现，而非进程内缓存的写入。线程模型是，单个acceptor线程，N个processor线程，每个processor线程处理固定数量的连接。这种设计久经测试，容易实现，而且效率很高。协议简单，方便其他语言的client实现。

## 5.3 Messages

消息由固定头部和变长不透明字节数组payload构成，头部包含格式版本和用来检测缺损的CRC32校验码。使payload不透明是正确的选择：现在正在进行大量关于序列化库的项目，任何决定都不能满足所有需要。毋庸置疑的是，任何使用Kafka的应用都很可能需要自己定制序列化类型。```MessageSet```接口就是遍历消息的迭代器，以及一些特殊的方法，用于读写NIO ```Channel```。

## 5.4 Message Format

```
/** 
	 * A message. The format of an N byte message is the following: 
	 * 
	 * If magic byte is 0 
	 * 
	 * 1. 1 byte "magic" identifier to allow format changes 
	 * 
	 * 2. 4 byte CRC32 of the payload 
	 * 
	 * 3. N - 5 byte payload 
	 * 
	 * If magic byte is 1 
	 * 
	 * 1. 1 byte "magic" identifier to allow format changes 
	 * 
	 * 2. 1 byte "attributes" identifier to allow annotations on the message independent of the version (e.g. compression enabled, type of codec used) 
	 * 
	 * 3. 4 byte CRC32 of the payload 
	 * 
	 * 4. N - 6 byte payload 
	 * 
	 */
```

## 5.5 Log

具有2个partition、名为“my\_topic”的topic的log（即my\_topic\_0和my\_topic\_1），充满了数据文件，这些文件包含了此topic的消息。log文件的格式是一系列的“log entries”；每个log entry是4字节整形*N*，用于保存消息长度，紧接其后的是*N*消息字节。每条消息由64-bit整形*offset*唯一标识，表示在所有发到此topic此partiton的所有消息的流中，此消息的字节起始位置。下面给出了每条消息的磁盘格式。每个log文件的文件名是其包含的第一条消息的offset。所有第一个文件是00000000000.kafka，而每个附加文件的文件名之差大概是*S*字节，其中，*S*是配置中指定的最大log文件大小。

消息的二进制格式包含版本，是一个标准的接口，使得消息组可以在producer、broker和client之间任意转移。格式如下：

```
On-disk format of a message

message length : 4 bytes (value: 1+4+n) 
"magic" value  : 1 byte
crc            : 4 bytes
payload        : n bytes
```

用消息offset作为消息id不太常见。最初的想法是由producer产生GUID，然后在broker上维护GUID到offset的映射。但是，因为consumer需要对每个broker维护一个ID，GUID的全局唯一性就没有意义了。此外，维护随机id到offset的映射需要重量级的索引结构，并且必须与磁盘保持同步，必然需要全部持久化的随机存取数据结构。为了简化查找结构，决定是是用简单的针对每个partiton的原子计数器，与partition id和节点id一起唯一标识一条消息；这简化了查找结构，虽然每个consumer请求需要多次seek。一旦确定了这种counter，从counter到offset的跳转就自然多了——因为两者相对partition来说都是单调递增的整数。因为consumer API不会感知到offset，因此这个决定是一个实现细节，可以使用更有效的方式。

![image]({{ site.url }}/images/blog/kafka-0-8-2-documentation/kafka-log-implementation.png)

### Writes

log允许对最后一个文件进行追加写入，在此文件达到配置大小（比如1GB）时自动切换到新的文件。log有两个配置参数，*M*表示在强制OS将文件刷入磁盘之前可以写多少条消息，*S*表示在强制刷新前可以等多少秒。这给出了durability保障，在系统崩溃时至多损失*M*条消息或*S*秒的数据。

### Reads

通过给定64位逻辑offset和*S*位最大块大小来完成读取。读取会返回*S*位buffer中所含消息的迭代器。*S*应该比单条消息大，但是对于异常大的消息，可能要进行多次读取尝试，每次将buffer大小扩大一倍，直到成功读取消息。可以指定最大消息大小，使服务器可以拒绝大小超过该值的消息，并且为client获取完整消息设定一个最大大小。有可能读取buffer中是部分消息，通过大小界定可以检测到。


读取特定offset消息的实际过程，需要首先定位数据所在log segment，用全局offset值计算文件内offset，然后读取数据。查找是对为每个文件保持的内存区间的二分查找。

log可以让client从最新写入的消息开始订阅，即“right now”。在consumer没有在SLA指定的天数内消费其数据的情况下很有用。在这种情况下，当client尝试去消费不存在的offset时，会得到异常OutOfRangeException，client可以根据使用场景选择重置或者失败。

以下是发送给consumer的结果格式。

```
MessageSetSend (fetch result)

total length     : 4 bytes
error code       : 2 bytes
message 1        : x bytes
...
message n        : x bytes
MultiMessageSetSend (multiFetch result)

total length       : 4 bytes
error code         : 2 bytes
messageSetSend 1
...
messageSetSend n
```

### Deletes

删除数据是以每次删除一个log segment的形式进行的。log manager允许插入的删除策略，用来选择可以删除的文件。现在的策略是删除修改时间为*N*天前的所有旧log文件，还有保留最后*N* GB的策略也很有用。为了避免在修改segment列表时影响读取，使用copy-on-write类型的segment列表实现，提供一致性视图，允许对log segment的不可改变静态snapshot视图进行二分查找，同时进行删除过程。

### Guarantees

log提供了配置参数*M*，其控制了强制刷入磁盘前的最大写入消息数量。启动时，log恢复过程，就是遍历ilog segment中的所有消息，然后确认每个消息条目是有效的。如果消息大小和offset的和小于文件大小，并且消息payload的CRC32与消息中的CRC一致，那么消息条目就是有效的。发现出错数据时，会将文件从最后有效offset处截断。

注意，必须处理两种错误：截断——因为崩溃造成的未写入块丢失，损坏——文件中**加入**了乱数据。因为通常来说，OS不保证文件inode和实际块数据的写入顺序，因此，除了丢失未写入的数据，也有可能inode已更新，但是因为崩溃实际块数据未写入，此时会多出来一些无意义的数据。CRC可以检测到这种情况，防止此错误使得整个log不可用（当然，未写入的消息还是会丢失）。

## 5.6 Distribution

### Consumer Offset Tracking

高级consumer跟踪其消费的每个partition的最大offset，定期得提交offset，这样在重启时可以从上次提交的位置重新开始。Kafka提供了一种选项，可以将指定consumer group的所有offset保存到指定的broker（针对此group），称之为*offset manager*。即，此consumer group里的所有consumer实例都将offset提交到offset manager，并从offset manager（broker）获取其offset。高级consumer自动对此进行处理。如果使用简单的consumer，需要自己管理offset。当前的Java简单consumer还不支持这种功能，仅支持向Zookeeper提交和获取offset。如果使用Scala简单consumer，就可以看到offset manager，显式向offset manager提交或获取offset。consumer可以通过向任何broker发出ConsumerMetadataRequest请求来查看offset manager，读取ConsumerMetadataResponse，其中包含了offset manager。consumer可以接着向offset manager broker提交或获取offset。如果想要自己管理offset，请参考[code samples that explain how to issue OffsetCommitRequest and OffsetFetchRequest](https://cwiki.apache.org/confluence/display/KAFKA/Committing+and+fetching+consumer+offsets+in+Kafka).

当offset manager收到OffsetCommitRequest，其将请求追加到特殊的[compacted](https://kafka.apache.org/documentation.html#compaction) Kafka topic，名为*\_\_consumer\_offsets*。仅当offsets topic的所有replica收到提交的offsets时，offset manager才会向consumer发出offset已经成功提交的回复。如果在配置的超时时间内未成功复制，那么此次offset提交就失败了，consumer可以以退避策略重试。（在高级consumer里这些是自动的。）broker会周期性地compact offsets topic，因为对于每个partition，只需要保留最新的offset。offset manager还会在内存表中缓存offset，以提高offset获取速度。

当offset manager接收到offset获取请求时，会返回offsets缓存中最后提交的offset向量。在offset manager刚启动或刚成为新的一组consumer groups的offset manager时（通过成为offsets topic的一个partition的leader），可能需要将offsets topic partition到缓存中。此时，offset获取请求会失败，得到OffsetsLoadInProgress异常，consumer可以以退避策略重试。（在高级consumer里这些是自动的。）

### Migrating offsets from ZooKeeper to Kafka

之前的版本中，Kafka将offsets存储在Zookeeper上。可以将offset的提交转移到Kafka，步骤如下：

1. 在consumer配置中设置offsets.storage=kafka和dual.commit.enabled=true。
2. 重启下consumer，查看消费是否正常。
3. 在consumer配置中设置dual.commit.enabled=false。
4. 重启下consumer，查看消费是否正常。

也可以回滚（即，从Kafka迁回到Zookeeper），步骤同上，设置offsets.storage=zookeeper。

### ZooKeeper Directories

下面给出了consumers和brokers之间协作用到的ZooKeeper结构和算法。

### Notation

如果路径中有[xyz]，表示xyz不是固定的，而是一个任何可能的实际的znode。例如，/topics/[topic]，是目录/topics，下面是每个topic名的子目录。数字区间[0...5]表示子目录0,1,2,3,4。箭头->表示znode的值。例如/hello->world表示znode /hello的值为“world”。

### Broker Node Registry

```/brokers/ids/[0...N] --> host:port (ephemeral node)```

现存的broker节点列表，每个都表示标识broker的唯一逻辑id（在broker的配置中指定）。启动时，broker节点在/brokers/ids下面创建znode，值为逻辑broker id。逻辑id的意义是，可以将broker迁移到另一个物理机，而不影响consumers。尝试注册已经存在的broker id（比如两个服务器的broker id一样）会出现错误。

因为broker注册的是临时znode，如果broker服务停止或挂了，相应的节点会自动消失（通过这种方式consumer就知道该broker已经不可用了）。

### Broker Topic Registry

```/brokers/topics/[topic]/[0...N] --> nPartions (ephemeral node)```

每个broker将自己注册到所包含的topic下，值为该topic的partition数量。

### Consumers and Consumer Groups

topics的consumers也会在Zookeeper上注册自己，为了互相协作和均衡数据的消费。consumers也可以通过设置```offsets.storage=zookeeper```将offsets存在Zookeeper。然而，此offset存储机制在未来的版本中会废弃。所以，最好将offsets存储到Kafka。

多个consumers可以组成一个group，共同消费一个topic。同一个group中的consumer共享一个group_id。例如，如果一个consumer是你的foobar进程，运行在3个机器上，那么你分配给这组consumer的id可以是“foobar”。此group id是在consumer的配置中，你需要告知consumer它属于哪个group。

同组的consumers会尽量均分partitions，每个partition仅被consumer group中的一个consumer消费。

### Consumer Id Registry

除了同组的所有consumers共用的group\_id外，每个consumer也会被指定一个暂时的唯一consumer\_id（形式：hostname:uuid）。Consumer ids注册在以下目录。

```
/consumers/[group_id]/ids/[consumer_id] --> {"topic1": #streams, ..., "topicN": #streams} (ephemeral node)
```

组内的每个consumer会注册在自己的group下，用consumer\_id创建znode，值为\<topic, #streams\>的map。id是标识组内存活的consumer的，如果consumer进程挂了，此临时节点会消失。

### Consumer Offsets

Consumers会跟踪其消费的每个partition的最大offset。如果```offsets.storage=zookeeper```，该值是存储在ZooKeeper目录中的。

```
/consumers/[group_id]/offsets/[topic]/[broker_id-partition_id] --> offset_counter_value ((persistent node)
```

### Partition Owner registry

每个broker partition被给定的consumer group中的一个consumer消费。在消费开始之前，consumer需要建立对给定partition的占有权。为了建立占有权，consumer将其id写入特定broker partition下的临时节点。

```
/consumers/[group_id]/owners/[topic]/[broker_id-partition_id] --> consumer_node_id (ephemeral node)
```

### Broker node registration

broker节点基本上是独立的，所以仅仅发布一些仅跟broker有关的信息。当一个broker加入时，其将自己注册在broker节点注册目录下，写入其hostname和port相关的信息。broker也会将现存topic和逻辑partition的列表注册到broker topic registry。新topic创建时，broker会动态将其注册上。

### Consumer registration algorithm

consumer启动时，会进行以下步骤：

1. 将自己注册到其group下的consumer id registry。
2. 对consumer id registry下的变化（新consumer加入，原先的consumer离开）注册watch。（每次变化都会触发发生变化的consumer所属group下所有consumer的重新均衡）。
3. 对broker id registry下的变化（新broker加入，原先的broker离开）注册watch。（每次变化都会所有consumer group下所有consumer的重新均衡）。
4. 如果consumer使用topic filter创建了消息流，还会对broker topic registry下的变化注册watch。（每次变化都会触发对能够通过filter的topic重新检测。如果有新的topic通过filter，就会触发此consumer group下所有consumers的重新均衡）。
5. 强制重新平衡其所在consumer group。

### Consumer rebalancing algorithm

consumer均衡算法允许组内所有consumer就哪个consumer消费哪些partitions达成共识。broker节点和同组内consumer的加入和离开都会触发consumer均衡。对于给定的topic和consumer group，broker partitions是均匀得分给此group中的consumers。一个partition总是被一个consumer消费。这个设计简化了实现。如果我们让一个partition可以同时被多个consumer消费，那么就会有对partition的竞争，就需要某种锁机制。如果consumer个数大于partition，一些consumer不会得到任何数据。在重新均衡期间，我们需要尽量减少每个consumer需要连接的broker节点数量。

重新均衡过程中，每个consumer执行以下步骤：

```
1. For each topic T that Ci subscribes to 
2.   let PT be all partitions producing topic T
3.   let CG be all consumers in the same group as Ci that consume topic T
4.   sort PT (so partitions on the same broker are clustered together)
5.   sort CG
6.   let i be the index position of Ci in CG and let N = size(PT)/size(CG)
7.   assign partitions from i*N to (i+1)*N - 1 to consumer Ci
8.   remove current entries owned by Ci from the partition owner registry
9.   add newly assigned partitions to the partition owner registry
   (we may need to re-try this until the original partition owner releases its ownership)
```

当在一个consumer上触发了重新均衡时，同组的其他consumer也需要同时进行重新均衡。

# 6. Operations

这里有一些我们在LinkIn将Kafka运行在生产环境下的一些运维经验。如果有任何tips，请告知我们。

## 6.1 Basic Kafka Operations

这部分包括一些Kafka集群的基本运维操作。所有工具都在/bin目录下，每个工具不带参数运行都会打印出所有命令行选项。

### Adding and removing topics

你可以选择手动添加topic，或者在发送第一条消息时自动创建topic。如果topic是自动创建的，那么你可能需要调整一些默认[topic参数](https://kafka.apache.org/documentation.html#topic-config)。

用topic工具增加和修改topic

``` 
> bin/kafka-topics.sh --zookeeper zk_host:port/chroot --create --topic my_topic_name 
       --partitions 20 --replication-factor 3 --config x=y
```

replication factor表示多少个broker会复制每条写入的消息。如果replication factor为3，那么可以允许2个服务器宕机而不丢数据。我们建议replication factor为2或3，可以在不影响数据消费的情况下重新恢复机器。

partition count控制着topic会被分片到多少个log中。partition count有一些影响。首先每个partition的数据必须全部在单台服务器上。所以如果有20个partition（读写负载）最多由20个服务器处理（不计算replica）。最后，partition数量影响consumer的最大并发度。在[概念部分](https://kafka.apache.org/documentation.html#intro_consumers)会详细讨论。

命令行参数会覆盖服务器的默认设定，例如数据保存的时间。特定于topic的全部配置参考[这里](https://kafka.apache.org/documentation.html#topic-config)。

### Modifying topics

还可以用topic工具修改topic的配置和分片。

增加partition

```
 > bin/kafka-topics.sh --zookeeper zk_host:port/chroot --alter --topic my_topic_name 
       --partitions 40 
```

注意，partition的一种应用场景是语义上对数据分片，增加partition并不会改变现存数据的分片，这可能会使消费新partition的consumer产生困扰。如果数据是通过```hash(key) % number_of_partitions```来分片的，那么通过增加partition，原先的分片会被打乱，但是Kafka不会自动重新分配数据。

增加配置：

```
 > bin/kafka-topics.sh --zookeeper zk_host:port/chroot --alter --topic my_topic_name --config x=y
```

删除配置：

```
 > bin/kafka-topics.sh --zookeeper zk_host:port/chroot --alter --topic my_topic_name --deleteConfig x
```

删除topic：

```
 > bin/kafka-topics.sh --zookeeper zk_host:port/chroot --delete --topic my_topic_name
```

默认topic删除选项是关闭的。通过设置服务器配置可以打开

```
delete.topic.enable=true
```

Kafka目前不支持通过修改replication factor来减少partition。

### Graceful shutdown

Kafka集群会自动检测任何broker关闭或故障，并为其所在机器上的partition选择新的leader。无论服务器挂了或者为了维护或配置更新而故意关闭，都会自动进行以上工作。对于维护或配置更新，Kafka有一种更优雅的方式来停止服务，而非直接kill。当服务平滑关闭时，有两个优点：

1. 可以将所有log同步到磁盘，避免启动时的log恢复（即，检验log尾部所有消息的checksum）。log恢复很耗时间，所以这可以加快重启过程。
2. 在关闭前，将服务器上的任何其为leader的partition迁移到其他replica。可以使leadership转移更快，将每个partition不可用的时间缩短到几毫秒。

在服务器关闭而非强行kill时，log的同步是自动进行的，但是leadership转移需要使用特殊的设置：

```
controlled.shutdown.enable=true
```

注意，受控制的关闭只有在broker上*所有*partition有replica的情况下（即，replication factor大于1，且至少一个replica存活）才会成功。这是通常想要的，因为关闭最后一个replica会使对应的topic partition不可用。

### Balancing leadership

无论何时broker关闭或崩溃，此broker的partitions leadership都会转移到其他replicas。意味着默认情况下，该broker重启后，只会是所有partition的follower，意味着不会用于client读写。

为了避免这种非均衡状态，Kafka有偏好的replica标记。如果partition的replicas列表是1,5,9，那么因为节点1在列表前面，所以倾向于让节点1作为leader。可以让Kafka集群尝试去恢复到原先的leadership，运行以下命令：

```
 > bin/kafka-preferred-replica-election.sh --zookeeper zk_host:port/chroot
```

也可以让Kafka自动进行leadership恢复操作：

```
    auto.leader.rebalance.enable=true
```

### Mirroring data between clusters

将Kafka集群*之间*的拷贝数据过程称为“mirroring”，以避免同单个集群各节点之间的拷贝混淆。Kafka有一个工具用于集群间数据拷贝。该工具从一个或多个源集群读取数据，然后写入目的集群，如下：

![image]({{ site.url }}/images/blog/kafka-0-8-2-documentation/mirror-maker.png)

这种mirroring的常用之处是数据中心之间的数据拷贝。下个部分会详细讨论。

可以运行多个mirroring进程，增加吞吐，容错，当一个进程挂了，其他进程会接管任务。

数据会从源集群被读取出来，然后写入到目的集群的同名topic。实际上，mirror maker就是基于Kafka的consumer和producer的。

源和目的集群是完全独立的：可以有不同数量的partition，offsets可以不同。所以，mirror集群不是一种容错机制（consumer的位置不同）；为了容错，建议集群内的replication。mirror maker进程会保留和使用消息的key来分片，所以数据还是按key有序的。

以下是从两个源集群mirror一个topic（my_topic）的例子：

```
 > bin/kafka-run-class.sh kafka.tools.MirrorMaker
       --consumer.config consumer-1.properties --consumer.config consumer-2.properties 
       --producer.config producer.properties --whitelist my-topic
```

注意，用```--whitelist```指定topic列表，此选项允许所有[Java-style regular expressions](http://docs.oracle.com/javase/7/docs/api/java/util/regex/Pattern.html)中的正则表达式。所以，可以用--whitelist 'A|B'来表示mirror两个topic *A*和*B*。或者可以用--whitelist '*' mirror所有topic。用单引号括起正则表达式是为了不让shell将其扩充为文件路径。为了方便起见，可以用','替代'|'分隔符来指定topic列表。

也可以使用--blacklist来指定排除哪些topic，也接受正则表达式。

与```auto.create.topics.enable=true```结合起来使用，就可以使得mirror集群自动创建和拷贝源集群的所有数据，即使有新的topic加入也可以。

### Checking consumer position

我们还有查看consuemr位置的工具，可以显示group中所有consuemr的位置，以及落后log尾部多远。

```
 > bin/kafka-run-class.sh kafka.tools.ConsumerOffsetChecker --zkconnect localhost:2181 --group test
Group           Topic                          Pid Offset          logSize         Lag             Owner
my-group        my-topic                       0   0               0               0               test_jkreps-mn-1394154511599-60744496-0
my-group        my-topic                       1   0               0               0               test_jkreps-mn-1394154521217-1a0be913-0
```

### Expanding your cluster

为Kafka集群增加服务器很容易，指定唯一的broker id，在新的服务器上启动broker即可。然而，这些新的服务器不会自动分配到任何数据partition，所以除非将partition转移到它们上面，它们无法进行任何工作，除非等待新的topic被创建。所以通常，增加机器时，会想要迁移部分已经存在的数据到这些机器上。

迁移数据的过程是手动启动，然后自动进行的。自动完成的工作是，Kafka将新服务器作为要迁移的partition的replica，完全拷贝该partition中已经存在的数据。当新的服务器完全拷贝了此partition的内容，并加入到in-sync replica，原先存在的其中一个replica会删除自己的数据。

partition reassignment工具可用于在broker之间转移partition。理想的partition分布会确保所有broker具有平均的数据负载和partition大小。在0.8.1中，partition reassignment 工具还不具备自动学习Kafka集群的数据分布，并自动进行负载均衡分布的能力。因此，管理员需要自己判断需要移动哪些topic或partition。

partition reassignment工具可以在以下3中互斥模式下运行——

* --generate: 在这种模式下，给定topic列表和broker列表，该工具会生成候选的reassignment，以将指定的topics的所有partition移动到新的brokers。此选项仅仅为了方便通过给定的topics列表和brokers列表生成一种partition reassignment方案。

* --execute: 在这种模式下，该工具会根据用户提供的reassignment方案进行partitions的重新分配。（使用 --reassignment-json-file 选项）。既可以是管理员直接手写的自定义分配方案，或者是通过--generate生成的方案。

* --verify: 在这种模式下，该工具会对最后--execute的所有partitions的分配状态进行验证。状态可能是成功、失败或正在进行。

#### Automatically migrating data to new machines

partition reassignment 工具用于将当前broker集合中的某些topics移动到新的brokers。当扩充集群时很有用，移动整个topic，比每次移动一个partition容易多了。当用于这种场景时，用户需要提供要移动的topic列表和目的brokers列表。该工具会将给定topic列表的所有partition均匀分布在新的broker集合上。移动时，topic的replication factor是不变的。输出的topic列表的所有partition的replicas都从旧的broker集合转移到新的broker集合。

例如，下面的例子会将topic foo1,foo2的所有partition移动到新的broker 5,6。移动后，topic foo1,foo2的所有partition*只*存在于broker 5,6上。

该工具接受用json文件的形式输入topic列表，创建json文件如下 ——

```
> cat topics-to-move.json
{"topics": [{"topic": "foo1"},
            {"topic": "foo2"}],
 "version":1
}
```

用 partition reassignment 工具生成候选assignment——

```
> bin/kafka-reassign-partitions.sh --zookeeper localhost:2181 --topics-to-move-json-file topics-to-move.json --broker-list "5,6" --generate 
Current partition replica assignment

{"version":1,
 "partitions":[{"topic":"foo1","partition":2,"replicas":[1,2]},
               {"topic":"foo1","partition":0,"replicas":[3,4]},
               {"topic":"foo2","partition":2,"replicas":[1,2]},
               {"topic":"foo2","partition":0,"replicas":[3,4]},
               {"topic":"foo1","partition":1,"replicas":[2,3]},
               {"topic":"foo2","partition":1,"replicas":[2,3]}]
}

Proposed partition reassignment configuration

{"version":1,
 "partitions":[{"topic":"foo1","partition":2,"replicas":[5,6]},
               {"topic":"foo1","partition":0,"replicas":[5,6]},
               {"topic":"foo2","partition":2,"replicas":[5,6]},
               {"topic":"foo2","partition":0,"replicas":[5,6]},
               {"topic":"foo1","partition":1,"replicas":[5,6]},
               {"topic":"foo2","partition":1,"replicas":[5,6]}]
}
```

该工具会生成候选的assignment，用来将topics foo1,foo2的所有partition移动到broker 5,6。注意，实际的移动过程还未开始，只是输出了当前的assignment和推荐的assignment。最好把当前的assignment保存下来，以防后面需要回滚。将新的assignment存入json文件（例如，expand-cluster-reassignment.json），作为--execute选项的输入 ——

```
> bin/kafka-reassign-partitions.sh --zookeeper localhost:2181 --reassignment-json-file expand-cluster-reassignment.json --execute
Current partition replica assignment

{"version":1,
 "partitions":[{"topic":"foo1","partition":2,"replicas":[1,2]},
               {"topic":"foo1","partition":0,"replicas":[3,4]},
               {"topic":"foo2","partition":2,"replicas":[1,2]},
               {"topic":"foo2","partition":0,"replicas":[3,4]},
               {"topic":"foo1","partition":1,"replicas":[2,3]},
               {"topic":"foo2","partition":1,"replicas":[2,3]}]
}

Save this to use as the --reassignment-json-file option during rollback
Successfully started reassignment of partitions
{"version":1,
 "partitions":[{"topic":"foo1","partition":2,"replicas":[5,6]},
               {"topic":"foo1","partition":0,"replicas":[5,6]},
               {"topic":"foo2","partition":2,"replicas":[5,6]},
               {"topic":"foo2","partition":0,"replicas":[5,6]},
               {"topic":"foo1","partition":1,"replicas":[5,6]},
               {"topic":"foo2","partition":1,"replicas":[5,6]}]
}
```

最后，用--verify选项验证下reassignment的状态。注意，（用于--execute选项）的expand-cluster-reassignment.json也要作为--verify选项的输入——

```
> bin/kafka-reassign-partitions.sh --zookeeper localhost:2181 --reassignment-json-file expand-cluster-reassignment.json --verify
Status of partition reassignment:
Reassignment of partition [foo1,0] completed successfully
Reassignment of partition [foo1,1] is in progress
Reassignment of partition [foo1,2] is in progress
Reassignment of partition [foo2,0] completed successfully
Reassignment of partition [foo2,1] completed successfully 
Reassignment of partition [foo2,2] completed successfully 
```

#### Custom partition assignment and migration

partition reassignment 工具也可以选择性地将一个partition的replica移动到指定的broker集合。使用这种方式时，是假设用户知道reassignment方案，而无需使用工具生成候选reassignment，跳过--generate步骤，直接进行--execute步骤。

例如，下面的例子将topic foo1的partition 0移动到broker 5,6，将topic foo2的partition 1移动到broker 2,3

创建json文件

```
> cat custom-reassignment.json
{"version":1,"partitions":[{"topic":"foo1","partition":0,"replicas":[5,6]},{"topic":"foo2","partition":1,"replicas":[2,3]}]}
```

使用--execute，用json文件作为输入，启动reassignment ——

```
> bin/kafka-reassign-partitions.sh --zookeeper localhost:2181 --reassignment-json-file custom-reassignment.json --execute
Current partition replica assignment

{"version":1,
 "partitions":[{"topic":"foo1","partition":0,"replicas":[1,2]},
               {"topic":"foo2","partition":1,"replicas":[3,4]}]
}

Save this to use as the --reassignment-json-file option during rollback
Successfully started reassignment of partitions
{"version":1,
 "partitions":[{"topic":"foo1","partition":0,"replicas":[5,6]},
               {"topic":"foo2","partition":1,"replicas":[2,3]}]
}
```

最后，用--verify选项验证下reassignment的状态。注意，（用于--execute选项）的expand-cluster-reassignment.json也要作为--verify选项的输入——

```
bin/kafka-reassign-partitions.sh --zookeeper localhost:2181 --reassignment-json-file custom-reassignment.json --verify
Status of partition reassignment:
Reassignment of partition [foo1,0] completed successfully
Reassignment of partition [foo2,1] completed successfully 
```

### Decommissioning brokers

partition reassignment 工具还无法自动产生reassignment方案，用来下线broker。所以，管理者需要构造一个reassignment方案，将要下线的broker上所有partition的replicas都迁移到剩余的brokers上。为了简化这个过程，我们打算在0.8.2中增加下线broker的工具。

### Increasing replication factor

增大已经存在的partition的replication factor很容易。仅仅在自定义的reassignment json文件中指定额外的replicas，然后运行--execute选项即可。

例如，下面的例子将topic foo的partition 0的replication factor从1增加到3.在增加replication factor之前，该partition的唯一replica是在broker 5上。为了增大replication factor，我们在broker 6,7上增加更多的replicas。

创建json文件

```
> cat increase-replication-factor.json
{"version":1,
 "partitions":[{"topic":"foo","partition":0,"replicas":[5,6,7]}]}
```
使用--execute，用json文件作为输入，启动reassignment ——

```
> bin/kafka-reassign-partitions.sh --zookeeper localhost:2181 --reassignment-json-file increase-replication-factor.json --execute
Current partition replica assignment

{"version":1,
 "partitions":[{"topic":"foo","partition":0,"replicas":[5]}]}

Save this to use as the --reassignment-json-file option during rollback
Successfully started reassignment of partitions
{"version":1,
 "partitions":[{"topic":"foo","partition":0,"replicas":[5,6,7]}]}
```

最后，用--verify选项验证下reassignment的状态。注意，（用于--execute选项）的increase-replication-factor.json也要作为--verify选项的输入——

```
bin/kafka-reassign-partitions.sh --zookeeper localhost:2181 --reassignment-json-file increase-replication-factor.json --verify
Status of partition reassignment:
Reassignment of partition [foo,0] completed successfully
```
也可以用kafka-topics工具验证replication factor——

```
> bin/kafka-topics.sh --zookeeper localhost:2181 --topic foo --describe
Topic:foo	PartitionCount:1	ReplicationFactor:3	Configs:
	Topic: foo	Partition: 0	Leader: 5	Replicas: 5,6,7	Isr: 5,6,7
```

## 6.2 Datacenters

有些部署需要管理跨多个数据中心的数据管道。我们推荐的方法是，在每个数据中心部署一个本地Kafka集群，该中心的应用实例仅跟本地集群互动，在多个集群之间，配置mirroring（参见mirror maker tool）。

这种部署模式允许各个数据中心之间独立，我们可以集中管理和调整数据中心间的拷贝。即使数据中心间的连接断开了，各个部分也能独立运行：连接断开后，mirroring会落后，连接恢复后，会自动追上。

可以将*所有*数据中心本地集群的数据通过mirroring聚合到提供的集群，提供一个统一的数据视图。这些聚合集群用于需要全部数据集的应用。

当然，这不是唯一的部署模式。也可以直接通过WAN读写远程Kafka集群，显然这种方式延迟比较高。

即使通过高延迟的连接，由于Kafka的producer和consumer都是批量传输数据的，所以吞吐依然会很高。但是为了达到这个效果，可能有必要增大producer、consumer、broker的TCP socket缓存，通过socket.send.buffer.bytes和socket.receive.buffer.bytes配置。参考[这里](http://en.wikipedia.org/wiki/Bandwidth-delay_product)。

通常不建议单个Kafka集群经过高延迟链接跨越多个数据中心。这会增大Kafka和Zookeeper写入的replication延迟，如果不同地点的为了不可用，不同地点的Kafka或Zookeeper都不能保证可用。

## 6.3 Kafka Configuration

### Important Client Configurations

最重要的producer配置

* compression
* sync vs async production
* batch size (for async producers)

最重要的consuemr配置是fetch size。

所有的配置都在configuration部分。

### A Production Server Config

这是我们生产环境的服务器配置：

```
# Replication configurations
num.replica.fetchers=4
replica.fetch.max.bytes=1048576
replica.fetch.wait.max.ms=500
replica.high.watermark.checkpoint.interval.ms=5000
replica.socket.timeout.ms=30000
replica.socket.receive.buffer.bytes=65536
replica.lag.time.max.ms=10000
replica.lag.max.messages=4000

controller.socket.timeout.ms=30000
controller.message.queue.size=10

# Log configuration
num.partitions=8
message.max.bytes=1000000
auto.create.topics.enable=true
log.index.interval.bytes=4096
log.index.size.max.bytes=10485760
log.retention.hours=168
log.flush.interval.ms=10000
log.flush.interval.messages=20000
log.flush.scheduler.interval.ms=2000
log.roll.hours=168
log.retention.check.interval.ms=300000
log.segment.bytes=1073741824

# ZK configuration
zookeeper.connection.timeout.ms=6000
zookeeper.sync.time.ms=2000

# Socket server configuration
num.io.threads=8
num.network.threads=8
socket.request.max.bytes=104857600
socket.receive.buffer.bytes=1048576
socket.send.buffer.bytes=1048576
queued.max.requests=16
fetch.purgatory.purge.interval.requests=100
producer.purgatory.purge.interval.requests=100
```

client的配置根据使用场景而异。

### Java Version

我们目前运行的是JDK 1.7 u51，变换到G1回收器。如果也使用G1回收器（强力推荐），确保你的版本是u51。在测试过程中，我们用过u21，但是那个版本的GC实现有一些问题。我们的调优是：

```
-Xms4g -Xmx4g -XX:PermSize=48m -XX:MaxPermSize=48m -XX:+UseG1GC
-XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35
```

下面是LinkeIn最忙（峰值）的集群之一的状态：——15 brokers——15.5.k partitions（replication factor 2）——400k messages/sec（in）——70 MB/sec inbound，400 MB/sec+ outbound，调优看起来很激进，但是该集群的所有的broker 90%的GC停顿时间是大约21ms，每秒的young GC不超过1次。

## 6.4 Hardware and OS

我们使用的是24GB内存的dual quad-core Intel Xeon机器。

需要充足的内存来缓存活动的读者和写者。可以通过假设需要缓存30秒，用write\_throughput*30计算需要的内存大小，来粗略估计需要的内存大小。

磁盘吞吐量很重要。我们有8x7200 rpm SATA drives。通常磁盘吞吐量是性能瓶颈，磁盘越多越好。根据你如何配置flush，决定是否需要使用更昂贵的硬盘（如果经常强制flush，那么高RPM的SAS会更好）。

### OS

Kafka在任意的unix系统上都应该正常运行，在Linux和Solaris上已经测试过。

对于Windows的支持还不是很好，正在改进。

虽然有些东西可以提高性能，但是基本上没有必要进行OS级别的调优。

两个配置可能很重要：

* 上调了文件描述符的个数，因为有大量的topic和连接。
* 上调了最大socket缓存大小，以提高不同数据中心之间数据转移的性能，参考[这里](http://www.psc.edu/index.php/networking/641-tcp-tune)。

### Disks and Filesystem

我们建议使用多个驱动器以获得高吞吐，Kafka数据和应用日志或其他OS文件系统活动不要共用一个驱动器，以保证低延迟。对于0.8，可以多个驱动器RAID到单个卷，或者对每个驱动器分别格式化并挂载到各自目录下。因为Kafka有replication机制，所以RAID提供的冗余也可以在应用层提供。

如果配置了多个目录，partition会以round-robin的方式分配到这些数据目录中。每个partition只在一个目录中。如果partition之间的数据不均衡，这会导致磁盘之间的负载不均衡。

RAID可能在磁盘负载均衡上做的更好（虽然并非总是如此），因为其在更低的层次进行负载均衡。RAID的主要缺点是对写入吞吐的性能影响很大，并且减少了可用磁盘空间。

RAID的另一个好处是能够容忍磁盘故障。然而，我们的经验是，重建RAID阵列是I/O密集的，几乎使服务不可用，所以也没有提供什么实际的可用性改进。

### Application vs. OS Flush Management

Kafka总是立即将所有数据写入文件系统，并且支持对flush策略进行配置，flush策略控制了数据从OS cache写入磁盘的时机。flush策略可以是定期强制写入磁盘，或者写入一定数量的消息以后强制刷盘。此配置有几种选择。

Kafka最终必须调用fsync，确保数据刷盘。当从崩溃中恢复时，如果有log segment不知道是否fsync过，Kafka会在启动时，通过检查CRC，检查每条消息的完整性，还要重建对应的offset索引文件。

注意，Kafka的durability并不要求将数据刷盘，因为故障节点总会从其replica恢复数据。

我们建议使用默认的flush设置，即完全禁止应用fsync。意味着依赖OS的后台flush和Kafka的后台flush。对于大多数场景，这是最好的：无需调优，高吞吐和低延迟，完全的恢复保障。我们认为replication提供的保障强于同步到磁盘，但是有些人还是希望两者都支持。

使用应用层flush设置的缺点是，其磁盘使用模式的低效（没有给OS重排写入的余地），还会引入延迟，因为大多数Linux文件系统中的fsync会阻塞文件写入，而后台flush使用粗粒度的page级别的锁。

通常无需对文件系统进行调优，但是后面几个部分我们会看一些需要调优的情况。

### Understanding Linux OS Flush Behavior

Linux中，写入文件系统的时间暂存在 pagecache 中，直到其被写入磁盘（应用层的fsync或OS的flush策略）。数据的flush是通过一组后台线程pdflush负责的（2.6.32内核中为“flusher threads”）。

pdflush可以配置cache可以缓存多少脏数据，可以缓存多长时间。此策略详见[这里](http://www.westnet.com/~gsmith/content/linux-pdflush.htm)。当pdflush无法跟上数据写入速率时，最终会阻塞写入进程，导致延迟升高，以降低数据的积压。

可以通过以下命令查看OS内存使用的当前状态

```
  > cat /proc/meminfo
```

使用pagecache比进程内cache的优势是：

* I/O scheduler会将连续的小的写入合并成大的物理写入，以提高吞吐量。
* I/O scheduler会对写入进行重排，以减少磁头的移动，以提高吞吐量。
* 自动使用机器上的所有空闲内存。

### Ext4 Notes

Ext4可能是也可能不是最适合Kafka的文件系统。据说XFS对fsync期间的锁处理得更好。我们只测试过Ext4。

没有必要对这些设置调优，如果想要调优，有几个地方可以参考：

* data=writeback：Ext4默认 data=ordered ，对一些写入顺序要求严格。Kafka对此无太大需求，因为其对任何没有flush的数据都可以恢复。此设置去掉了ordering限制，能够显著降低延迟。
* Disabling journaling：日志是一种折中：可以使服务器宕机后启动的速度更快，但是也引入了额外的锁，会影响写入性能。如果不关心重启时间，而且想降低写入延迟，可以关闭日志功能。
* commit=num_secs：这会调整ext4提交meta数据日志的频率。较低的值会减少崩溃时丢失的数据。较高的值会提高吞吐量。
* nobh：此设置控制使用data=writeback模式时另外的ordering保障。Kafka不依赖写入顺序，所以可以提高吞吐量，降低延迟。
* delalloc：延迟分配是指进行物理写入时才分配实际的块。这使ext4可以申请很大的extent，而非很小的pages，以确保数据顺序写入。此特性对提高吞吐量很有用。可能会涉及到文件系统的某些锁，会增加延迟抖动。

## 6.6 Monitoring

Kafka使用Yammer Metrics，用于服务端和客户端的度量报告。可以配置使用插入的stats reporters报告stats，与监控系统挂钩。

观测可用metrics最简单的方法是启动jconsole，指向运行的kafak客户端或服务器；会使用JMX浏览所有metrics。

我们用于绘图和报警的metrics如下：

表格略。

### New producer monitoring

略

### Audit

最终的报警是对数据传递的正确性。我们审计发布和消费的每条消息，并计算时间间隔。对于重要的topic，如果在一定的时间内没有达到一定的完成度，就会报警。关于审计的详细讨论，请参考KAFKA-260。

## 6.7 ZooKeeper

### Stable version

LinkeIn使用ZooKeeper 3.3.*。3.3.3版本有很严重的问题，关于临时节点删除和session过期。现在用的是3.3.4，已经线上稳定运行1年了。

### Operationalizing ZooKeeper

* 物理/硬件/物理布局的冗余：不要放在同一个机架，优质硬件，冗余电源和网络路径等等。
* I/O 隔离：如果写入操作很多，那么你肯定想把数据处理日志放在与应用日志和快照不同的磁盘组上（Zookeeper服务的写入操作会同步写入磁盘，所以会很慢）。
* 应用隔离：除非你清楚得知道其他apps的应用模式，否则还是孤立地运行Zookeeper较好（可以根据硬件特征进行权衡）。
* 小心使用虚拟化：可以运行，根据你的集群布局，读写模式，SLAs，但是虚拟化层引入的开销累积依赖可能会使Zookeeper无法正常工作，因为其对时间很敏感。
* ZooKeeper配置和监控：设定*足够*的堆空间（我们通常用3-5G，因为我们的数据量很大）。但是我们没有公式来计算这个量。至于监控，JMZ和4 letter commands都很有用，在某些情况下可能会重叠（偏向于使用4 letter commands，它们更可测，至少可以很好地结合LI监控基础组件）
* 集群不要过大：大集群，尤其是对于写入操作很多的使用模式，意味着集群内的通信很多（写入时的quorum和其它成员的数据同步），也不要太小（否则集群资源很快就不够用了）。
* 3-5个节点的集群为宜：Zookeeper使用quorums，所以节点数量必须为奇数。记住，5个节点集群的写入速度比3个节点的慢，但是容错性更高。

