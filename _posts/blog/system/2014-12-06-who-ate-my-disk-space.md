---
layout: post
title: "Who Ate My Disk Space"
modified:
categories: blog/system
excerpt:
tags: [Kafka, XFS, Disk Usage, Apparent Size, Df, Du, Preallocation]
author: zheolong
comments: true
share: true
date: 2014-12-06T15:12:25+08:00
---
## High Disk Usage 

Apache Kafka is publish-subscribe messaging rethought as a distributed commit log. Messages are persisted on disk. We built serveral kafka clusters (v0.7.2), but during the operation encountered a thorny problem: disk usage of some brokers is high, approaching **87%**, but after restarting the kafka process, disk usage dropped to **60%**. 


Before restarted kafka, `df -h` shows

    Filesystem            Size  Used Avail Use% Mounted on

    /dev/mapper/VolGroup00-LogVol04   1.6T  1.3T  206G  87% /data

After restarted kafka, `df -h` shows


    Filesystem            Size  Used Avail Use% Mounted on
                     
    /dev/mapper/VolGroup00-LogVol04    1.6T  987G  588G  63% /data

## Kafka Process

### File Held Open?
We all know that kafka process has one thread cleanup expired log file periodically (for v0.7.2, default 10 minutes).

First we assumed that there exist some deleted log files are still open for reading, if so, the os won't really delete them until they are closed. 

`lsof | grep 'deleted$'` will tell us which deleted files are still held open. Unfortunately we found nothing related to kafka log files.
 
### Cleanup Thread? 
Maybe when kafka process quit, it execute cleanup procedure again. We compared the log file name before and after restarting, still found no any difference.

## Space vs. Data
`df` tool only show the disk super block info, the **Used** refers to disk space was occupied, not the real data amount. For example, create a file **test.txt** and echo **1** char to it.

`du --block-size=1 test.txt` shows **4096** 

`du --block-size=1 --apparent-size test.txt` or `du -b test.txt` shows **2**

why is the output of `du` so different from `du -b` ?

**Apparent size** is the number of bytes your applications think are in the file. It's the amount of data that would be transferred over the **network** (not counting protocol headers) if you decided to send the file over FTP or HTTP. It's also the result of `cat theFile | wc -c`, and the amount of address space that the file would take up if you loaded the whole thing using **mmap**.

**Disk usage** is the amount of space that can't be used for something else because your file is occupying that space.

In most cases, the apparent size is smaller than the disk usage because the disk usage counts the full size of the last (partial) block of the file, and apparent size only counts the data that's in that last block. However, apparent size is larger when you have a sparse file (sparse files are created when you seek somewhere past the end of the file, and then write something there -- the OS doesn't bother to create lots of blocks filled with zeros -- it only creates a block for the part of the file you decided to write to).

If you use `ncdu`, it will compute disk usage and apparent size of every subdir.

### Disk Fragment?

Let's be doctor and check disk fragment. `fsck` may be the common tool, but here we use 

`sudo xfs_db -r -c frag /dev/mapper/VolGroup00-LogVol04` as the filesystem is **XFS**.

> -r means read only, if you want to try this cmd, use it for safe

Run this cmd before and after restarting, but result did not change, as below, 

```
actual 559717, ideal 4899, fragmentation factor 99.12%
```

Filesystem under linux may have defragmention tools but won't execute automatically, so process action won't trigger disk defragmention.

### Preallocation?

Yeah! Finally, [XFS FAQ](http://xfs.org/index.php/XFS_FAQ#Q:_Why_do_files_on_XFS_use_more_data_blocks_than_expected.3F) helped us. XFS has a feature naming **Speculative Preallocation**. 

The XFS speculative preallocation algorithm allocates extra blocks beyond end of file (EOF) to minimize file fragmentation during buffered write workloads.

This post-EOF block allocation is accounted identically to blocks within EOF. It is visible in 'st_blocks' counts via stat() system calls, accounted as globally allocated space and against quotas that apply to the associated file. The space is reported by various userspace utilities (**stat, du, df, ls**) and thus provides a common source of **confusion for administrators**.

In most cases, speculative preallocation is automatically **reclaimed when a file is closed**. 

Speculative preallocation **can not be disabled** but XFS can be tuned to a **fixed allocation size** with the 'allocsize=' mount option. Speculative preallocation is not dynamically resized when the allocsize mount option is set and thus the potential for fragmentation is increased. Use 'allocsize=64k' to revert to the default XFS behavior prior to support for dynamic speculative preallocation.


## What We Can Do?

1. Restart kafka process periodically.
2. Fix XFS preallocation size.

## Why Not?
1. Try other filesystem?

     A: You can try, but it's time expensive. Linkedin use Ext4 as their Kafka cluster filesystem, you can start from this.

2. Use apparent size as disk space judgement standard?

     A: The diff between disk usage and apparent size not just affected by preallocation extent, but also affected by fragmentation, directories, sparse files, hard links.  


## References

1. [Why is disk usage greater than the size of all files on it?](http://askubuntu.com/questions/234913/why-is-disk-usage-greater-than-the-size-of-all-files-on-it)
2. [Why are my XFS filesystems suddenly consuming more space and full of sparse files?](http://serverfault.com/questions/406069/why-are-my-xfs-filesystems-suddenly-consuming-more-space-and-full-of-sparse-file)
3. [why is the output of `du` often so different from `du -b`](http://stackoverflow.com/questions/5694741/why-is-the-output-of-du-often-so-different-from-du-b)




















