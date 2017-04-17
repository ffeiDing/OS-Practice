
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



































## 二、docker基本命令
### 1、镜像管理
* 列出镜像 
```
docker images [OPTIONS] [REPOSITORY]
参数:
-a, --all=false                  列出所有镜像（默认隐藏中间镜像）
--digests=falseShow digests      摘要
-f, --filter=[]                  根据条件过滤输出
--help=false                     打印使用帮助
--no-trunc=false                 不缩略输出          
-q, --quiet=false                仅显示数字标识符
```
>例子：
```
docker images
```
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw4/picture/HDFS结构图.png"/></div>  

* 拉取镜像
```
docker pull [OPTIONS] NAME[:TAG|@DIGEST]
参数:
-a, --all-tags=false             拉取所有tagged镜像 
--help=false                     打印使用帮助
```
>例子：
```
docker pull  ubuntu:latest
docker pull  ubuntu:12.04
```
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/dockerpull指令运行截图.png"/></div> 

* 查找镜像
```
docker search [OPTIONS] TERM/NAME
参数:
--automated=false             仅显示自动化的builds
--help=false                  打印使用帮助
--no-trunc=false              不缩略输出 
-s, --stars=0                 只显示至少x颗星的信息（在该情况下为至少0颗星）
```
>例子：
```
docker search hello_world
```
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/dockersearch指令运行截图.png"/></div> 

* 构建镜像

Step 1:建立Dockerfile
```
FROM ubuntu
MAINTAINER zxp huo "likewind@gmail.com"
RUN apt-get update
RUN apt-get install -y nginx
RUN echo 'hi ,i am in container'>/usr/share/nginx/html/index.html
EXPOSE 80
```
Step 2:build建立镜像
```
docker build [OPTIONS] PATH | URL | -
参数:
-c, --cpu-shares=0    CPU shares (relative weight)
--cpuset-cpus=        CPUs in which to allow execution 
-f, --file=           Name of the Dockerfile (Default is 'PATH/Dockerfile')
--force-rm=false      Always remove intermediate containers
--help=false          Print usage
-m, --memory=         Memory limit
--memory-swap=        Total memory (memory + swap), '-1' to disable swap
--no-cache=false      Do not use cache when building the image
--pull=false          Always attempt to pull a newer version of the image
-q, --quiet=false     Suppress the verbose output generated by the containers
--rm=true             Remove intermediate containers after a successful build
-t, --tag=            Repository name (and optionally a tag) for the image(镜像名：标签)
```

### 2、容器管理

* 创建并启动容器
```
docker run [OPTIONS] IMAGE {COMMAND} [ARG...]
参数:
-d                            创建一个守护式容器在后台运行
-i                            交互式运行
-t                            为容器重新分配一个伪输入终端
-p                            指定端口或IP进行映射
--name="NAME"                 为容器指定一个名称
--network="NETWORK_NAME"      选择一个网络
```
* 查看容器
```
docker ps [OPTIONS]
参数:
-a                            查看已经创建的容器
-s                            查看已经启动的容器
```
* 启动容器
```
docker start con_name         启动容器名为con_name的容器
```
* 停止运行容器
```
docker stop con_name          停止容器名为con_name的容器
```
* 删除容器
```
docker rm con_name            删除容器名为con_name的容器
```
* 重命名容器
```
docker rename old_name new_name
```
* 容器信息
```
docker logs con_name          获取容器名为con_name的容器日志
```

### 3、网络管理
* 创建网络
```
docker network create
```
* 容器连接到网络
```
docker network connect
```
* 列出网络
```
docker network ls
```
* 删除网络
```
docker network rm
```
* 容器断开网络
```
docker network disconnect
```
* 网络信息
```
docker network inspect
```

## 三、创建一个基础镜像为ubuntu的docker镜像，随后在其中加入nginx服务器，之后启动nginx服务器并利用tail命令将访问日志输出到标准输出流。要求该镜像中的web服务器主页显示自己编辑的内容，编辑的内容包含学号和姓名。之后创建一个自己定义的network，模式为bridge，并让自己配的web服务器容器连到这一网络中。要求容器所在宿主机可以访问这个web服务器搭的网站
### 1、创建一个基础镜像为ubuntu的docker镜像
* 拉取镜像
```
sudo docker pull  ubuntu:latest
```
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/dockerpull指令运行截图.png"/></div> 

* 创建并启动容器
```
docker run -i -t --name ubuntu_docker -p 9999:80 ubuntu /bin/bash
```
### 2、加入nginx服务器

* 在创建的容器中安装ngix
```
apt update
apt install nginx
```
* 安装依赖包
```
apt install vim
```
* 修改主页内容
```
cd /var/www/html/
vim index.nginx-debian.html
```
* 添加转发端口号

登录燕云，添加内部9999端口至外部9999端口的转发

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/添加端口.png"/></div> 

* 启动nginx服务器
```
cd ..
cd ..
cd ..
nginx
```
* 浏览器访问<code> http://162.105.174.40:9999 </code>查看主页内容

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/web主页内容.png"/></div>

* 输出访问日志到标准输出流
```
tail -f /var/log/nginx/access.log
```
结果如下图：

<div align=left><img width="100%" height="100%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/访问日志.png"/></div>

### 3、创建自定义网络

* 停止容器

Ctrl C 后退回到容器
```
exit
```
停止该容器

* 保存镜像
```
docker commit ubuntu_docker ubuntu_docker2
```
* 创建并运行带新镜像的容器
```
docker run -d --name hw_docker -p 9999:80 ubuntu_docker2 nginx -g 'daemon off;'
```
* 创建一个自己定义的network，模式为bridge
```
docker network create hw_network
```
* 将容器连入网络并检查
```
docker network connect hw_network hw_docker
docker network inspect hw_network
```
下图表示成功连入

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/网络信息.png"/></div>

### 4、宿主机访问web服务器搭的网站

* 查看容器信息获取ip地址
```
docker inspect hw_docker
```

ip地址为172.17.0.2

* 访问web服务器网站
```
curl 172.17.0.2:80
```
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/访问web服务器搭的网站.png"/></div>

## 四、docker容器加入不同的网络模式
### 1、null模式
```
docker run -i -t --net="none"  mysql:latest /bin/bash
```

输入以上指令进入容器后，再输入<code>ip addr</code>，查看网络信息
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/null模式网络.png"/></div>

* 容器仅有一个本地回环网络<code>127.0.0.1</code>，没有任何网络配置

* 容器不能通过网络管理指令来断开null模式下的网络

### 2、bridge模式
```
docker run -i -t mysql:latest /bin/bash
docker run -i -t --net="bridge" mysql:latest /bin/bash
```

以上两个指令都可以创建bridge模式的网络下的容器，即默认情况下容器的网络配置为bridge模式，进入容器后，再输入<code>ip addr</code>，查看网络信息
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/bridge模式网络.png"/></div>

从上图中可以看到，容器内有一个eth0接口，解释eth0需要理解bridge桥接模式：

* Docker Daemon利用veth pair技术，在宿主机上创建两个虚拟网络接口设备，假设为veth0和veth1。veth pair技术的特性可以保证无论哪一个veth接收到网络报文，都会将报文传输给另一方

* Docker Daemon将veth0附加到Docker Daemon创建的docker0网桥上，保证宿主机的网络报文可以发往veth0

* Docker Daemon将veth1添加到容器所属的<code>namespace</code>下，并被改名为eth0。

* 宿主机的网络报文若发往veth0，则立即会被eth0接收，实现宿主机到容器网络的联通性；同时，也保证Docker Container单独使用eth0，实现容器网络环境的隔离性

* bridge模式的网络可以创建多个

* 容器可以通过网络管理指令来断开bridge模式下的网络或连接其他网络

### 3、host模式
```
docker run -i -t --net="host" mysql:latest /bin/bash
```

该模式区别于bridge模式，在无需进行NAT转换的同时，隔离性弱化了：

* 容器不需要通过桥接模式，可以直接访问宿主机上的全部网络信息，不会有所属的<code>namespace</code>，而是共享宿主机的<code>namespace</code>

* 容器内部将不再拥有所有的端口资源，原因是部分端口资源已经被宿主机本身的服务占用，还有部分端口已经用以bridge网络模式容器的端口映射

* 如果两个以上的容器都加入host模式的网络，就无法监听同一端口，会发生访问冲突

* host模式的网络只可以创建一个

* 容器一旦加入host模式的网络，就无法通过网络管理指令来断开或连接网络

### 4、overlay模式
```
docker network create -d overlay overlay_network
```

overlay模式的网络需要手动创建，区别于以上三种模式，它主要用于对集群的管理和服务（假设有三台主机）：

* 第一台主机作为swarn管理节点
```
docker swarm init
```

截图如下：

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/overlay模式管理节点.png"/></div>

* 第二台和第三台主机作为普通节点加入
```
root@oo-lab:/home/pkusei# docker swarm join \
> --token SWMTKN-1-5lod92o32eiq84x5uy26dhszode6zx8pdpj30k85xq1s167pdg-e5li4l6jnd0zjf9j7vg2w3z5g \
> 172.16.6.213:2377
```
截图如下：

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/overlay模式普通节点.png"/></div>

* 第一台主机（管理节点）查看所有节点
```
docker node ls
```
截图如下：

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/overlay节点.png"/></div>

* 每台主机都可以通过<code>docker network ls</code>指令看到overlay模式的网络
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/overlay模式网络.png"/></div>

* 输入<code>docker network create -d overlay overlay_network</code>指令手动创建overlay网络

* 采用如下指令创建容器，此时不能创建普通容器，需要创建一个docker server用于集群，并创建三个task，将管理容器中的80端口映射到宿主机的8888端口
```
docker service create --replicas 3 --network overlay_network --name overlay_web -p 8888:80 nginx
```
* 登录燕云，添加管理容器所在的主机8888端口至宿主机8888端口的端口转发

* 浏览器访问<code>http://162.105.174.40:8888</code>
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/overlay访问web.png"/></div>

## 五、阅读mesos中负责与docker交互的代码

代码位于<code>mesos-1.1.0/src/docker</code>文件夹中，有<code>docker.cpp</code>、<code>docker.hpp</code>、<code>executor.cpp</code>、<code>executor.hpp</code>和<code>spec.cpp</code>五个文件。

### 1、 <code>docker.cpp</code>、<code>docker.hpp</code>

 <code>docker.hpp</code>头文件中定义了Docker类，该类内部又定义了Container（容器）和Image（镜像）两个类。<code>docker.cpp</code>文件实现了Docker类中的成员函数，主要负责将参数与docker指令一一对应。比较重要的函数有<code>create</code>：创建容器或者创建镜像，<code>run</code>：运行docker，<code>stop</code>：停止运行docker，<code>kill</code>：杀死docker，<code>rm</code>：删除docker等等，其中<code>run</code>函数具体实现如下：

* 首先获取docker的信息
```
const ContainerInfo::DockerInfo& dockerInfo = containerInfo.docker();
```

* 添加路径、-H选项、socket参数和run命令
```
vector<string> argv;
argv.push_back(path);
argv.push_back("-H");
argv.push_back(socket);
argv.push_back("run");
```

* 检查是否有特权，如果有添加--privileged参数
```
if (dockerInfo.privileged()) {
    argv.push_back("--privileged");
}
```

* 检查资源分配情况，添加--cpu-shares、--memory参数

* 检查环境变量，添加环境变量参数
```
if (env.isSome()) {
    foreachpair (string key, string value, env.get()) {
    argv.push_back("-e");
    argv.push_back(key + "=" + value);
    }
}
```

* 检查并添加commandInfo中的环境变量参数


* 手动添加MESOS_SANDBOX和MESOS_CONTAINER_NAME环境变量参数
```
argv.push_back("-e");
argv.push_back("MESOS_SANDBOX=" + mappedDirectory);
argv.push_back("-e");
argv.push_back("MESOS_CONTAINER_NAME=" + name);
```

* 配置volume

* 配置网络（host、bridge、none模式和用户自定义模式），并检查相关模式下的配置是否有错误，比如host和none模式下不能进行端口映射等

* 检查并添加外部设备参数

* 如果shell被激活，重写entrypoint
```
if (commandInfo.shell()) {
    argv.push_back("--entrypoint");
    argv.push_back("/bin/sh");
}
```

* 添加容器名和镜像名
```
argv.push_back("--name");
argv.push_back(name);
argv.push_back(image);
```

* 创建子进程运行容器
```
Try<Subprocess> s = subprocess(
    path,
    argv,
    Subprocess::PATH("/dev/null"),
    _stdout,
    _stderr,
    nullptr,
    environment);
```

### 2、<code>executor.cpp</code>、<code>executor.hpp</code>

该部分实现了一个执行docker的executor，将docker作为一个task，对它进行注册、启动、运行、终止等基本操作。

### 3、<code>spec.cpp</code>
该文件负责解析JSON格式的配置文件，解析为map类。

## 五、写一个framework，以容器的方式运行task

和上次作业的最后一题类似，需要修改pymesos的样例，修改后如下：
```
#!/usr/bin/env python2.7
from __future__ import print_function

import sys
import uuid
import time
import socket
import signal
import getpass
from threading import Thread
from os.path import abspath, join, dirname

from pymesos import MesosSchedulerDriver, Scheduler, encode_data, decode_data
from addict import Dict

TASK_CPU = 1
TASK_MEM = 32
EXECUTOR_CPUS = 0.5
EXECUTOR_MEM = 32
TASK_NUM = 1


class DockerScheduler(Scheduler):

    def __init__(self):
        self.launched_task = 0

    def resourceOffers(self, driver, offers):
        filters = {'refuse_seconds': 5}

        for offer in offers:
            cpus = self.getResource(offer.resources, 'cpus')
            mem = self.getResource(offer.resources, 'mem')
            if self.launched_task == TASK_NUM:
                return
            if cpus < TASK_CPU or mem < TASK_MEM:
                continue


            task = Dict()
            task_id = str(uuid.uuid4())
            task.task_id.value = task_id
            task.agent_id.value = offer.agent_id.value

            # Container Info
            task.name = 'docker'
            task.container.type = 'DOCKER'
            task.container.docker.image = 'ubuntu_docker2'
            task.container.docker.network = 'HOST'

            # Command Info
            task.command.shell = False
            task.command.value = 'nginx'
            task.command.arguments=['-g','daemon off;']

            task.resources = [
                dict(name='cpus', type='SCALAR', scalar={'value': TASK_CPU}),
                dict(name='mem', type='SCALAR', scalar={'value': TASK_MEM}),
            ]

            self.launched_task += 1
            driver.launchTasks(offer.id, [task], filters)
            

    def getResource(self, res, name):
        for r in res:
            if r.name == name:
                return r.scalar.value
        return 0.0

    def statusUpdate(self, driver, update):
        logging.debug('Status update TID %s %s',
                      update.task_id.value,
                      update.state)


def main(master):
    framework = Dict()
    framework.user = getpass.getuser()
    framework.name = "DockerFramework"
    framework.hostname = socket.gethostname()

    driver = MesosSchedulerDriver(
        DockerScheduler(),
        framework,
        master,
        use_addict=True,
    )

    def signal_handler(signal, frame):
        driver.stop()

    def run_driver_thread():
        driver.run()

    driver_thread = Thread(target=run_driver_thread, args=())
    driver_thread.start()

    print('Scheduler running, wait :).')
    signal.signal(signal.SIGINT, signal_handler)

    while driver_thread.is_alive():
        time.sleep(1)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) != 2:
        print("Usage: {} <mesos_master>".format(sys.argv[0]))
        sys.exit(1)
    else:
        main(sys.argv[1])
```
与样例的主要区别：
```
# Container Info
task.name = 'docker'
task.container.type = 'DOCKER'
task.container.docker.image = 'ubuntu_docker2'
task.container.docker.network = 'HOST'

# Command Info
task.command.shell = False
task.command.value = 'nginx'
task.command.arguments=['-g','daemon off;']
```
添加了容器和命令行的信息

启动master
```
./bin/mesos-master.sh --ip=172.16.6.213 --hostname=162.105.174.40 --work_dir=/var/lib/mesos
```
启动slave
```
./bin/mesos-agent.sh --master=172.16.6.213:5050 --work_dir=/var/lib/mesos \
--ip=172.16.6.224 --hostname=162.105.174.40 --containerizers=docker,mesos \
--image_providers=docker --isolation=docker/runtime
```
运行调度器
```
python DockerScheduler.py 172.16.6.213 &
```

<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/截图1%20"/></div>
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/截图2"/></div>
