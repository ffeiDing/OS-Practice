
# 第四次作业
## 一、调研两种以上的分布式文件系统以及一种联合文件系统，说明其工作原理和特点以及使用方式

### 1、分布式文件系统

#### 1.1 HDFS (Hadoop Distributed File System)

* 结构

<div align=left><img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/HDFS结构图.png"/></div>

如图所示，HDFS按照master和slave的结构，分为如下几个角色：

 (1) NameNode：master节点，管理数据块映射、处理客户端的读写请求、配置副本策略、管理HDFS的名称空间

 (2) SecondaryNameNode：分担NameNode的工作（从NameNode上获取fsimage和edits，合并后发回给NameNode）、是NameNode的冷备份（存储有NameNode部分信息，如果NameNode宕机，SecondaryNameNode不能马上代替NameNode工作，只能减少宕机损失）

 (3) DataNode：slave节点，存储client发来的数据块block、执行数据块的读写操作

 (4) fsimage：文件系统的目录树

 (5) edits：针对文件系统做的修改操作记录

* 写操作

将client要写入的block以副本的形式存储到至少三个DataNode中，如果client是DataNode节点，规则为：副本1，本节点；副本2，与副本1不同机架节点；副本3，与副本2同一机架的不同节点；其他副本随机挑选。如果client不是DataNode节点，规则为：副本1，随机节点；副本2，与副本1不同机架节点；副本3，与副本2同一机架的不同节点；其他副本随机挑选。

<div align=left><img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/HDFS写操作.png"/></div> 

假设：

有一个文件FileA，100M大小。client将FileA写入到HDFS上。HDFS按默认配置。HDFS分布在三个机架上Rack1，Rack2，Rack3

流程：

(1) client将FileA按照64M分块，分为64M的block1和36M的block2

(2) client向NameNode发送写数据请求，如图中蓝色虚线所示

(3) NameNode记录block1和block2的信息，返回可用的DataNode信息，如粉色虚线所示：block1：host2，host1，host3；block2：host7，host8，host4

(4) client向DataNode以流式发送block1（如图红色实线所示）：将64M的block1按64k的package划分；将第一个package发送给host2；host2接收完后，将第一个package发送给host1，同时client向host2发送第二个package；host1接收完第一个package后，将第一个package发送给host3，同时接收host2发来的第二个package；以此类推，直到将block1发送完毕。

(5) host2、host1、host3接收完毕后向NameNode发送接收完毕通知，host2向client发送接收完毕通知，如图中粉色实线所示

(6) client接收到host2发来的消息后，向NameNode发送“block1写完”消息，如黄色实线所示

(7) 类似发送block1的步骤，发送block2

* 读操作

如果client是DataNode节点，优先读取本机架上的数据
<div align=left><img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/HDFS读操作.png"/></div>  

假设：

client要从HDFS上读取FileA，FileA由block1和block2组成

流程：

(1) client向NameNode发送读FileA请求（蓝色虚线）

(2) NameNode查找数据块映射，返回FileA的各个block的位置（粉色虚线）：block1：host2，host1，host3；block2：host7，host8，host4

(3) client先去host2上读取block1，再去host7上读取block2

#### 1.2 MooseFS (Moose File System)

* 结构

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/MooseFS结构.png"/></div>  

如图，MooseFS按照master和slave的结构，分为如下几个角色：

(1) Master：元数据服务器，master节点，负责各个数据存储服务器的管理，文件读写调度，文件空间回收以及恢复，多节点拷贝

(2) Metalogger：元数据日志服务器，负责备份Master服务器的changelog，在Master出问题时接替其工作

(3) Chunk：数据存储服务器，负责连接Master，听从Master调度，提供存储空间，并为客户端提供数据传输

(4) Client：客户端挂载，通过FUSE内核接口挂载远程管理服务器（Master）上所管理的数据存储服务器（Chunk），使用起来和本地文件系统一样

* 写操作

<div align=left><img width="60%" height="60%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/MooseFS写操作.png"/></div> 

(1) Client给Master写操作的消息

(2) Master判断写入哪个Chunk，既可以选择一个已有的Chunk，也可以创建一个新的Chunk，将目标Chunk返回给Client

(3) Client向目标Chunk写入数据

(4) Chunk同步数据

(5) Chunk返回“成功”消息给Client

(6) Client返回“完毕”消息给Master

* 读操作

<div align=left><img width="60%" height="60%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/MooseFS读操作.png"/></div> 

(1) Client给Master读操作的消息

(2) Master判断数据在哪个Chunk上，将目标Chunk返回给Client

(3) Client向目标Chunk发送“send me the data”消息

(4) Chunk返回数据给Client


#### 1.3 GlusterFS (Gluster File System)

* 结构

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/GlusterFS架构.png"/></div>  

如图，GlusterFS架构中没有元数据服务器组件，主要由一下几部分构成：

(1) Brick Server：存储服务器，提供数据存储功能，其上运行Glusterfsd进程负责处理来自其他组件的数据服务请求

(2) 逻辑卷：多个Brick Server共同构成

(3) Client：客户端，提供数据卷管理、I/O调度、文件定位、数据缓存等功能，其上运行Glusterfs进程，是Glusterfsd的符号链接，利用FUSE（File system in User Space）模块将GlusterFS挂载到本地文件系统之上，实现POSIX兼容的方式来访问系统数据。GlusterFS客户端负载相对传统分布式文件系统要高，包括CPU占用率和内存占用

(4) Storage Gateway：存储网关，提供弹性卷管理和NFS/CIFS访问代理功能，其上运行Glusterd和Glusterfs进程，两者都是Glusterfsd符号链接。卷管理器负责逻辑卷的创建、删除、容量扩展与缩减、容量平滑等功能，并负责向客户端提供逻辑卷信息及主动更新通知功能等。对于没有安装GlusterFS的客户端，需要通过NFS/CIFS代理网关来访问，这时网关被配置成NFS或Samba服务器。相对原生客户端，网关在性能上要受到NFS/Samba的制约

* 数据访问流程概览

GlusterFS采用弹性哈希算法代替传统分布式文件系统中的集中或分布式元数据服务，从而获得了接近线性的高扩展性，同时也提高了系统性能和可靠性，具体流程如下：

(1) 输入文件路径和文件名，计算哈希值

(2) 根据哈希值在cluster中选择子卷（对应的Brick Server），进行文件定位

(3) 对所选择的子卷（对应的Brick Server）进行数据访问

* 功能模块

<div align=left><img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/GlusterFS模块栈.png"/></div> 

如图，GlusterFS是模块化堆栈式的架构设计，其中的模块被称为Translator。每个Translator实现特定的基本功能，比如Cluster, Storage, Performance, Protocol, Features等，多个Translator通过堆栈式组合形成更复杂的功能。客户端和存储服务器均有自己的Translator栈，构成了一棵Translator功能树。主要有如下几个Translator：

(1) Cluster：存储集群分布，有AFR, DHT, Stripe三种方式

(2) Debug：跟踪GlusterFS内部函数和系统调用

(3) Encryption：简单的数据加密实现

(4) Features：访问控制、锁、Mac兼容、静默、配额、只读、回收站等

(5) Mgmt：弹性卷管理

(6) Mount：FUSE接口实现

(7) Nfs：内部NFS服务器

(8) Performance：io-cache, io-threads, quick-read, read-ahead, stat-prefetch, sysmlink-cache, write-behind等性能优化

(9) Protocol：服务器和客户端协议实现

(10) Storage：底层文件系统POSIX接口实现

其中Cluster是实现GlusterFS集群存储的核心：

<code>ARF</code>将同一文件在多个存储节点上保留多份，所有子卷上具有相同的名字空间，查找文件时从第一个节点开始，直到搜索成功或最后节点搜索完毕。读数据时，AFR会把所有请求调度到所有存储节点，进行负载均衡以提高系统性能。写数据时，首先需要在所有锁服务器上对文件加锁，默认第一个节点为锁服务器，可以指定多个。然后，AFR以日志事件方式对所有服务器进行写数据操作，成功后删除日志并解锁。

<code>DHT</code>即弹性哈希算法，它采用hash方式进行数据分布，名字空间分布在所有节点上。查找文件时，通过弹性哈希算法进行，不依赖名字空间。但遍历文件目录时，则实现较为复杂和低效，需要搜索所有的存储节点。单一文件只会调度到唯一的存储节点，一旦文件被定位后，读写模式相对简单。DHT不具备容错能力，需要借助AFR实现高可用性。

<code>Stripe</code>实现分片存储，文件被划分成固定长度的数据分片以Round-Robin轮转方式存储在所有存储节点。所有存储节点组成完整的名字空间，查找文件时需要询问所有节点，非常低效。读写数据时，Stripe涉及全部分片存储节点，操作可以在多个节点之间并发执行，性能非常高。Stripe通常与AFR组合使用，同时获得高性能和高可用性，但存储利用率会低于50%


#### 1.4 三种分布式文件系统对比

1、HDFS只支持追加写，设计中没有考虑修改写、截断写、稀疏写等复杂的posix语义，目的并不是通用的文件系统；MooseFS比较接近GoogleFS的c++实现，通过FUSE支持了标准的posix，算是通用的文件系统

2、HDFS适合大文件存储，顺序读取类型的应用；MooseFS提供了快照功能，针对小文件和随机I/O进行了一些优化

3、HDFS和MooseFS都是类似GoogleFS的实现方式，有数据中心，存在单点问题；GlusterFS采用弹性哈希算法代替元数据服务

4、就主流而言，HDFS具有压倒性的优势，Facebook、Yahoo、阿里、腾讯、百度等都是使用者；豆瓣使用了MooseFS；很多互联网视频公司用GlusterFS来做片库

### 2、联合文件系统--AUFS（Advanced Multi Layered Unification File System）

* 所谓UnionFS就是把不同物理位置的目录合并mount到同一个目录中，比如，我们有两个目录（水果和蔬菜），并在这两个目录中放上一些文件，水果中有苹果和蕃茄，蔬菜有胡萝卜和蕃茄，如下：

```
$ tree
.
├── fruits
│   ├── apple
│   └── tomato
└── vegetables
    ├── carrots
    └── tomato
```
输入以下命令
```
# 创建一个mount目录
$ mkdir mnt

# 把水果目录和蔬菜目录union mount到 ./mnt目录中
$ sudo mount -t aufs -o dirs=./fruits:./vegetables none ./mnt

#  查看./mnt目录
$ tree ./mnt
./mnt
├── apple
├── carrots
└── tomato
```
我们可以看到在./mnt目录下有三个文件，苹果apple、胡萝卜carrots和蕃茄tomato。水果和蔬菜的目录被union到了./mnt目录下了


* AUFS的特性

AUFS有所有UnionFS的特性，把多个目录合并成同一个目录，可以为每个需要合并的目录指定相应的权限，实时的添加、删除、修改已经被mount好的目录。还能在多个可写的branch/dir间进行负载均衡。

* AUFS的性能

AUFS会把所有的分支mount起来，查找文件比较慢。因为它要遍历所有的branch，所以branch越多，查找文件的性能也就越慢。在write/read操作上，性能没有什么变化。

## 二、安装配置一种分布式文件系统，要求启动容错机制，即一台存储节点挂掉仍然能正常工作
### 在1001上安装GlusterFS服务器版本
```
sudo su
```
切换到root模式下
```
add-apt-repository ppa:gluster/glusterfs-3.10
apt update
apt install glusterfs-server
```
### 在1002上安装GlusterFS服务器版本
```
sudo su
```
切换到root模式下
```
add-apt-repository ppa:gluster/glusterfs-3.10
apt update
apt install glusterfs-server
```
### 在1003上安装GlusterFS客户端版本
```
sudo su
```
切换到root模式下
```
add-apt-repository ppa:gluster/glusterfs-3.10
apt update
apt install glusterfs-client
```
### 修改1001上的hosts文件
```
vim /etc/hosts
```
修改为
```
127.0.0.1       server1
127.0.1.1       oo-lab.cs1cloud.internal        oo-lab
172.16.6.224    server2
```
其中server2对应的IP需要在1002上通过<code>ifconfig</code>指令查看
### 修改1002上的hosts文件
```
vim /etc/hosts
```
修改为
```
127.0.0.1       server2
127.0.1.1       oo-lab.cs1cloud.internal        oo-lab
172.16.6.192    server1
```
其中server1对应的IP需要在1001上通过<code>ifconfig</code>指令查看
### 在1001和1002上创建brick
```
mkdir -p /data/brick1
```
### 在1001（也可以在1002）创建复制卷test_volume，并启动该卷
```
gluster volume create test_volume replica 2 server1:/data/brick1 server2:/data/brick1 force
gluster volume start test_volume
gluster volume info
```
查看该卷的信息，表明创建成功
```
Volume Name: test_volume
Type: Replicate
Volume ID: f9e54e0b-0f0b-4869-b473-27cd0c2e8a51
Status: Started
Snapshot Count: 0
Number of Bricks: 1 x 2 = 2
Transport-type: tcp
Bricks:
Brick1: server1:/data/brick1
Brick2: server2:/data/brick1
Options Reconfigured:
transport.address-family: inet
nfs.disable: on
```
### 修改1003上的hosts文件
```
vim /etc/hosts
```
修改为
```
127.0.0.1       localhost
127.0.1.1       oo-lab.cs1cloud.internal        oo-lab
172.16.6.192    server1
172.16.6.224     server2
```
### 在1003上创建挂载点，挂载test_volume卷
```
mkdir -p /storage
mount -t glusterfs server1:/test_volume /storage
```
向/storage里存入50个文件，为hw4.txt的拷贝
```
for i in `seq -w 1 50`; do cp -rp /home/pkusei/hw4.txt /storage/copy-hw4-$i; done
```
### 检查1003挂载点/storage的存入情况
```
cd /storage
ls
```
显示为：
```
copy-hw4-01  copy-hw4-07  copy-hw4-13  copy-hw4-19  copy-hw4-25  copy-hw4-31  copy-hw4-37  copy-hw4-43  copy-hw4-49
copy-hw4-02  copy-hw4-08  copy-hw4-14  copy-hw4-20  copy-hw4-26  copy-hw4-32  copy-hw4-38  copy-hw4-44  copy-hw4-50
copy-hw4-03  copy-hw4-09  copy-hw4-15  copy-hw4-21  copy-hw4-27  copy-hw4-33  copy-hw4-39  copy-hw4-45
copy-hw4-04  copy-hw4-10  copy-hw4-16  copy-hw4-22  copy-hw4-28  copy-hw4-34  copy-hw4-40  copy-hw4-46
copy-hw4-05  copy-hw4-11  copy-hw4-17  copy-hw4-23  copy-hw4-29  copy-hw4-35  copy-hw4-41  copy-hw4-47
copy-hw4-06  copy-hw4-12  copy-hw4-18  copy-hw4-24  copy-hw4-30  copy-hw4-36  copy-hw4-42  copy-hw4-48
```
### 检查1001和1002的/brick1中的存入情况
```
cd /data/brick1
ls
```
两者都显示为：
```
copy-hw4-01  copy-hw4-07  copy-hw4-13  copy-hw4-19  copy-hw4-25  copy-hw4-31  copy-hw4-37  copy-hw4-43  copy-hw4-49
copy-hw4-02  copy-hw4-08  copy-hw4-14  copy-hw4-20  copy-hw4-26  copy-hw4-32  copy-hw4-38  copy-hw4-44  copy-hw4-50
copy-hw4-03  copy-hw4-09  copy-hw4-15  copy-hw4-21  copy-hw4-27  copy-hw4-33  copy-hw4-39  copy-hw4-45
copy-hw4-04  copy-hw4-10  copy-hw4-16  copy-hw4-22  copy-hw4-28  copy-hw4-34  copy-hw4-40  copy-hw4-46
copy-hw4-05  copy-hw4-11  copy-hw4-17  copy-hw4-23  copy-hw4-29  copy-hw4-35  copy-hw4-41  copy-hw4-47
copy-hw4-06  copy-hw4-12  copy-hw4-18  copy-hw4-24  copy-hw4-30  copy-hw4-36  copy-hw4-42  copy-hw4-48
```
也就是任意一台存储节点挂掉仍然能正常工作，因为另一台存储节点还保存有副本

## 三、将web服务器的主页提前写好在分布式文件系统里，在docker容器启动的时候将分布式文件系统挂载到容器里，并将该主页拷贝到正确的路径下，使得访问网站时显示这个主页
### 在1001和1002上分别新建一个brick来存储主页内容
```
mkdir -p /data/brick2
```
### 在1002（也可以在1001）创建复制卷homepage，并启动该卷
```
gluster volume create homepage replica 2 server1:/data/brick2 server2:/data/brick2 force
gluster volume start homepage
```
### 在1003上创建挂载点，挂载homepage卷
```
mkdir -p /html
mount -t glusterfs server2:/homepage /html
```
存入主页文件
```
vim /html/index.nginx-debian.html 
```
### 在1003上创建容器并运行gnix
在1002中以上次作业的ubuntu_docker2镜像创建容器hw4_docker，运行bash
```
docker run -it --name hw4_docker  ubuntu_docker2  /bin/bash 
```
进入新创建的容器后，修改/etc/nginx/sites-enabled/default中root的路径为/html
```
vim /etc/nginx/sites-enabled/default
```
修改完成后退出容器，将该容器保存为ubuntu_docker_hw4镜像
```
docker commit hw4_docker ubuntu_docker_hw4
```
将该镜像从1002传送到1003上
```
docker save -o save.tar ubuntu_docker_hw4
scp -P 1003 save.tar pkusei@162.105.174.40:
```
在1003中以ubuntu_docker_hw4镜像创建后台容器并运行nginx，将/html挂载到容器中的/html中，将容器的80端口映射到宿主机的4040端口
```
docker load < save.tar
docker run -v /html:/html -p 4040:80 -d --name hw4 \
ubuntu_docker_hw4 nginx -g 'daemon off;'
```
登录燕云，将1003的4040端口转发到外网的4040端口，浏览器访问http://162.105.174.40:4040 可以查看主页
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/转发端口.png"/></div>  
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/主页内容.png"/></div>  

## 四、完成一次镜像的制作
### docker的镜像机制
* docker镜像的内容 主要包含两个部分：镜像层文件内容和镜像json文件。容器是一个动态的环境，每一层镜像中的文件属于静态内容，然而Dockerfile中的ENV、VOLUME、CMD等内容最终都需要落实到容器的运行环境中，而这些内容均不可能直接坐落到每一层镜像所包含的文件系统内容中，因此每一个docker镜像还会包含json文件记录与容器之间的关系。
* docker镜像存储位置 docker镜像层的内容一般在docker根目录的aufs路径下，为 /var/lib/docker/aufs/diff/；对于每一个镜像层，docker都会保存一份相应的 json文件，json文件的存储路径为 /var/lib/docker/graph

### 通过ubuntu镜像创建一个docker容器，命名为hw4
```
docker create -it --name hw4 ubuntu /bin/bash
```


















