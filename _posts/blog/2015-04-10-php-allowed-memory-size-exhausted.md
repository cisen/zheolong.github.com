---
layout: post
title: "Php: Allowed Memory Size Exhausted"
modified:
categories: blog
excerpt:
tags: [php qbus]
comments: true
share: true
image:
  feature:
date: 2015-04-10T14:06:59+08:00
---

## 问题

2015年4月8日下午，业务反映调用QBus php sdk的consumer接口取不到cluster:zzzc2，topic：barcode_realtime的数据。

## 解决

### 第一个小问题：为何无法输出消息

#### 排除

首先排除了以下几个可能的问题：

1. 读取的offset异常
2. 服务器磁盘异常
3. 用户程序问题（基本与我们提供的消费者例子类似）


#### 复现 & 跟踪

通过程序运行的信息可以看出，其试图将从QBus服务器拉取的数据写入到/tmp目录下的一个php*临时文件，而由于/tmp目录所在磁盘满，导致写入不成功。我们通过在/tmp目录下创建一个大的临时文件来模拟磁盘满。

创建一个临时文件

``` bash
[liujun-xy@w007 /tmp]$ fallocate -l 923M /tmp/test_qiao.tmp
[liujun-xy@w007 /tmp]$ df -h /tmp
Filesystem            Size  Used Avail Use% Mounted on
/dev/mapper/VolGroup00-LogVol01
                     1008M  957M     0 100% /tmp
```

然后运行程序

``` bash
[liujun-xy@w007 ~/gjb_scancode_push]$ strace ./qbus-install/php/bin/php -c ./qbus-install/php.ini consumer.php  -c zzzc2 -t barcode_realtime -g test_qiao
```

strace的结果看似非常正常，但截取输出信息的片段可以看到ENOSPC的错误

``` bash
write(8, "027\\u957f\\u8896\\u5706\\u9886\\u6bd"..., 8192) = -1 ENOSPC (No space left on device)
```

刚开始也是凭借此信息可以知道系统某个磁盘数据满，并找到/tmp目录所在磁盘。发现/tmp下有大量的php*文件，例如php09bOJ2。截取的strace输出信息片段中可以查找以php开头的文件信息，如下

``` bash
lstat("/tmp", {st_mode=S_IFDIR|S_ISVTX|0777, st_size=4096, ...}) = 0
open("/tmp/php7fU7Uu", O_RDWR|O_CREAT|O_EXCL, 0600) = 8

......

close(8)                                = 0
unlink("/tmp/php7fU7Uu")                = 0
pipe2([8, 9], O_CLOEXEC)                = 0
```

确实是我们的程序创建了这个文件并对其进行了读写，进而想到php会将某些数据缓存在临时文件中，默认的目录就是/tmp（用户可以自己指定），继而查找sdk中有关文件打开的操作，创建临时文件的代码有两处：

``` bash
./qbus-install/kafka_client/lib/Kafka/BoundedByteBuffer/Send.php:52:		$this->buffer = fopen('php://temp', 'w+b');

./qbus-install/kafka_client/lib/Kafka/BoundedByteBuffer/Receive.php:116:	  $this->buffer = fopen('php://temp', 'w+b');
```

而Receive.php是与我们的消费程序调用路径相关的，此处相关代码片段如下

``` php
$read = $this->readRequestSize($stream);
// have we allocated the request buffer yet?
if (!$this->buffer) {
        $this->buffer = fopen('php://temp', 'w+b');
}
// if we have a buffer, read some stuff into it
if ($this->buffer && !$this->complete) {
        $freadBufferSize = min(8192, $this->remainingBytes);
        if ($freadBufferSize > 0) {
                //TODO: check that fread returns something
                $bytesRead = fwrite($this->buffer, fread($stream, $freadBufferSize));
                $this->remainingBytes -= $bytesRead;
                $read += $bytesRead;
```

php官方提供的文档中可以找到与php://temp相关的说明，如下

>
php://memory and php://temp
>
php://memory and php://temp are read-write streams that allow temporary data to be stored in a file-like wrapper. The only difference between the two is that php://memory will always store its data in memory, whereas php://temp will use a temporary file once the amount of data stored hits a predefined limit (the default is 2 MB). The location of this temporary file is determined in the same way as the sys_get_temp_dir() function.
>
The memory limit of php://temp can be controlled by appending /maxmemory:NN, where NN is the maximum amount of data to keep in memory before using a temporary file, in bytes.


也就是说php://temp这种“I/O类型”会在存储的数据量超过2M时将剩余的数据存储在临时文件中，而php://memory只存储在内存中。

有兴趣的读者可以统计下[strace信息片段]({{ site.url }}/images/blog/php_memory_out/strace_info.txt)中存入buffer的数据量，大约就是2M，然后才开始存入临时文件。

这种临时文件大小差不多30M(大概就是QBus配置中maxFetchSize的大小），并且文件会在关闭后（用 fclose()）自动被删除，或当脚本结束后。注意，这里的结束是**正常退出**，如果发送SIGKILL或SIGINT给该进程，而此时临时文件仍在打开状态，那么该文件就不会被删除（已验证），这也解释了为何/tmp目录下会有大量的php*临时文件。

#### 小结

解决方法如下

1. 删除这些临时文件，并且推荐业务对线上机器的磁盘进行监控，如果遇到磁盘满的问题，比较容易定位；

2. 可以将sdk中php://temp改为php://memory，这样虽然多浪费一些内存空间，但是可以减少磁盘依赖，当然内存空间使用也是需要加监控的。

在删除了临时文件后，再次运行程序又出现了以下问题。


### 第二个小问题：为何提示内存超限制

#### 复现 & 跟踪

对于lib/Kafka/Config.php中设置了maxFetchSize为30M的情况，如下

``` php
    /**
     * @var   Int     max buffer size to fetch message from broker, it should be bigger than message length + 10 at least
     */
    public static $maxFetchSize         = 31457280; // 30M
```

30M表示每次fetch请求最多从QBus的服务端拉回30M数据。这30M数据在sdk的调用过程中会被复制至少一次，可以假设现在拉回来的数据占据的内存空间至少60M。

在运行消费程序后会导致如下错误

``` bash
[liujun-xy@w007 ~/gjb_scancode_push]$ ./qbus-install/php/bin/php -c ./qbus-install/php.ini qbus-install/kafka_client/examples/consume.php zzzc2 barcode_realtime test_qiao

Fatal error: Allowed memory size of 134217728 bytes exhausted (tried to allocate 32 bytes) in /home/liujun-xy/gjb_scancode_push/qbus-install/kafka_client/lib/Kafka/Message.php on line 95
Segmentation fault (core dumped)
```

也就是说分配的内存大小已经达到了php的默认限制128M（134217728）。

在sdk的对应出错代码前面加入一行代码，输出内存分配情况，结果如下

代码

``` php
echo "memory usage: ".memory_get_usage()."\n";
```

结果

``` bash
memory usage: 32776832
memory usage: 32778888
memory usage: 32780648
memory usage: 32782488
memory usage: 32784288
memory usage: 32785976
memory usage: 32787720

......

memory usage: 134166520
memory usage: 134168304
memory usage: 134170096
memory usage: 134171888
memory usage: 134173664
memory usage: 134175448
memory usage: 134177240
memory usage: 134179024

Fatal error: Allowed memory size of 134217728 bytes exhausted (tried to allocate 313 bytes) in /home/liujun-xy/gjb_scancode_push/qbus-install/kafka_client/lib/Kafka/Message.php on line 63

```

分配的系统内存从刚开始的31M增加到128M（memory_limit）。

此时使用的内存管理方式是Zend Engine的内存管理方式，默认情况下不是使用malloc，而是每次分配256K的大块系统内存，这些内存由Zend Engine管理。

#### 小结

1. 在程序中加入

``` php
ini_set('memory_limit','-1');
```
程序可以正常运行，分配的内存最多达到+240M。当然最好设置一个合理的值，比如500M限制，设置-1表示没有限制。

2. 使用malloc分配内存

设置环境变量export USE_ZEND_ALLOC=0，这种情况会使用malloc分配内存，效率比Zend的内存管理器低。

3. 修改maxFetchSize

比如修改为1M，128M足够用，但是这会导致有些单条大小超过1M的数据丢失，与业务情况相关。如果数据远小于1M，最好在程序中将maxFetchSize设置为1M，尽量不要修改公用的Config.php文件，防止影响其他使用该文件的程序。

#### FAQ

**疑问**：消息（包括复制的）最多60M，为何分配的内存达到了+240M

**回答**：+240M指的是os分配的总内存，这些内存不只用于消息。如果将maxFetchSize设置为1M，最终分配的总内存是+160M，与+240M相差的大约80M才是每次多取数据造成的内存分配。


## 总结

由于业务单条数据不大（<1k），建议其删除临时文件后，将maxFetchSize改为1M，并对线上机器磁盘和内存进行监控。



