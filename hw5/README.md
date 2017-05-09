

# 第五次作业
## 一、描述Linux内核如何对IP数据包进行处理
如下图所示，Linux内核通过Netfilter进行IP数据包处理

<img width="50%" height="50%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/Linux网络包处理.png"/>

Netfilter为多种网络协议各提供了一套钩子函数。像有几个钓鱼台，在每个钓鱼台放了一个鱼钩(钩子函数)，把经过的数据包钓上来，然后根据自定义的规则，来决定数据包的命运：可以原封不动的放回IP协议栈，继续向上层递交；也可以进行修改，再放回IP协议栈；也可以直接丢弃。

### 具体流程

1、刚刚收到的IP数据包将触发挂在PREROUTING上的回调函数，如果允许通过，进行网络地址转换，进入路由判断

2、路由判断后，如果是本机，触发挂在INPUT上的回调函数（A箭头），如果不是本机，触发挂在FORWARD上的回调函数（B箭头）

3A、如果INPUT上的回调函数允许通过，放回协议栈；本机协议栈如果发出IP数据包，需要路由判断下一个节点，进行网络地址转换，设置目标地址

4、filter规则过滤，网络地址转换，封包发出

### route

route是根据路由表进行路由判断，得到下一节点的地址

### iptables

iptables是用来进行IP数据包filter和NAT的工具，由filter表和NAT表组成

### filter表

有三种内建链：

* INPUT：处理输入的数据

* OUTPUT：处理产生的要输出的数据

* FORWARD：转发数据到本机的其他设备

### NAT表

有三种内建链：

* OUTPUT：处理产生的要输出的数据包

* PREROUTING：处理路由之前的数据包，转换IP数据包中的目标IP地址

* POSTROUTING：处理经过路由之后的数据包，转换IP数据包中的源IP地址

## 二、在服务器上使用iptables分别实现如下功能并测试
### 1、拒绝来自某一特定IP地址的访问
* 查看本机的IP地址
```
10.0.35.198
```
* 登录1001服务器，输入命令
```
iptables -A INPUT -s 10.0.35.198 -j REJECT
```
* 打开新的终端，尝试使用ssh登录1001服务器，发现被拒绝
```
ssh pkusei@162.105.174.40 -p 1001
ssh: connect to host 162.105.174.40 port 1001: Connection refused
```
* 恢复访问，由于本机已无法登录，需要登录燕云，打开1001服务器的控制台，输入命令
```
iptables -D INPUT -s 10.0.35.198 -j REJECT
```
### 2、拒绝来自某一特定mac地址的访问
* 查看1002服务器的mac地址
```
02:00:4d:28:00:03
```
* 登录1001服务器，输入命令
```
iptables -A INPUT -m mac --mac-source 02:00:4d:28:00:03 -j REJECT
```
* 登录1002服务器，ping1001服务器，发现不可达
```
ping 172.16.6.192
PING 172.16.6.192 (172.16.6.192) 56(84) bytes of data.
From 172.16.6.192 icmp_seq=7 Destination Port Unreachable
From 172.16.6.192 icmp_seq=9 Destination Port Unreachable
From 172.16.6.192 icmp_seq=10 Destination Port Unreachable
...
```
* 恢复访问
```
iptables -D INPUT -m mac --mac-source 02:00:4d:28:00:03 -j REJECT
```
### 3、只开放本机的http服务，其余协议与端口均拒绝
* 在1001服务器上，只接受80端口，设置默认规则为DROP
```
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -P INPUT DROP
```
* 设置完毕后，与服务器1001的连接中断，需要登录燕云1001的控制台查看信息
```
iptables -L INPUT --line-numbers
Chain INPUT (policy DROP)
num  target     prot opt source               destination
1    ACCEPT     tcp  --  anywhere             anywhere             tcp dpt:http
```
发现仅开放了了http服务

* 恢复访问，在1001的控制台上输入命令，设置默认规则为接收
```
iptables -P INPUT ACCEPT
```
* 登录1001服务器，删除设置
```
iptables -D INPUT -p tcp --dport 80 -j ACCEPT
```
### 4、拒绝回应来自某一特定IP地址的ping命令
* 查看1002的IP地址
```
172.16.6.224
```
* 在1001服务器上输入命令
```
iptables -A INPUT -p icmp --icmp-type 8 -s 172.16.6.224 -j REJECT
```
* 检查效果，1002服务器向1001服务器ping
```
ping 172.16.6.192
From 172.16.6.192 icmp_seq=1 Destination Port Unreachable
From 172.16.6.192 icmp_seq=2 Destination Port Unreachable
From 172.16.6.192 icmp_seq=3 Destination Port Unreachable
From 172.16.6.192 icmp_seq=4 Destination Port Unreachable
...
```
* 取消拒绝
```
iptables -D INPUT -p icmp --icmp-type 8 -s 172.16.6.224 -j REJECT
```

## 三、解释Linux网络设备工作原理
### 1、bridge工作过程

* Linux内核通过一个虚拟的网桥设备来实现桥接的，这个设备可以绑定若干个以太网接口设备，从而将它们桥接起来。如下图所示：

* 网桥设备br0绑定了eth0和eth1。对于网络协议栈的上层来说，只看得到br0，因为桥接是在数据链路层实现的，上层不需要关心桥接的细节。于是协议栈上层需要发送的报文被送到br0，网桥设备的处理代码再来判断报文该被转发到eth0或是eth1，或者两者皆是；反过来，从eth0或从eth1接收到的报文被提交给网桥的处理代码，在这里会判断报文该转发、丢弃、或提交到协议栈上层。而有时候eth0、eth1也可能会作为报文的源地址或目的地址，直接参与报文的发送与接收（从而绕过网桥）。

### 2、vlan工作过程

* vlan即虚拟局域网，一个vlan能够模拟一个常规的交换网络，实现了将一个物理的交换机划分成多个逻辑的交换网络。而不同的vlan之间如果要进行通信就要通过三层协议来实现，在二层协议里插入额外的vlan协议数据，同时保持和传统二层设备的兼容性。

<img width="50%" height="50%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/VLAN设备工作过程.png"/>

* 如图所示，VLAN设备是以母子关系成对出现的，母设备相当于现实世界中的交换机TRUNK口，用于连接上级网络，子设备相当于普通接口用于连接下级网络。当一个子设备有一包数据需要发送时，数据将被加入VLAN Tag然后从母设备发送出去。当母设备收到一包数据时，它将会分析其中的VLAN Tag，如果有对应的子设备存在，则把数据转发到那个子设备上并根据设置移除VLAN Tag，否则丢弃该数据。和Bridge一样，母子设备的数据也是有方向的，子设备收到的数据不会进入母设备，同样母设备上请求发送的数据不会被转到子设备上。

* 需要注意的是母子VLAN设备拥有相同的MAC地址，多个VLAN设备会共享一个MAC。当一个母设备拥有多个VLAN子设备时，子设备之间是隔离的，不存在Bridge那样的交换转发关系，如果子设备间想要交换数据，就需要将子设备attach到bridge上。

### 3、veth工作过程

* VETH的作用是反转通讯数据的方向，需要发送的数据会被转换成需要收到的数据重新送入内核网络层进行处理，从而间接地完成数据的注入。VETH设备总是成对出现，送到一端请求发送的数据总是从另一端以请求接受的形式出现。该设备不能被用户程序直接操作，但使用起来比较简单。创建并配置正确后，向其一端输入数据，VETH会改变数据的方向并将其送入内核网络核心，完成数据的注入，在另一端能读到此数据。

## 四、说明在calico容器网络中，一个数据包从源容器发送到目标容器接收的具体过程
### docker的镜像机制
* docker镜像的内容 

 主要包含两个部分：镜像层文件内容和镜像json文件。容器是一个动态的环境，每一层镜像中的文件属于静态内容，然而Dockerfile中的ENV、VOLUME、CMD等内容最终都需要落实到容器的运行环境中，而这些内容均不可能直接坐落到每一层镜像所包含的文件系统内容中，因此每一个docker镜像还会包含json文件记录与容器之间的关系。
* docker镜像存储位置 
 
 docker镜像层的内容一般在docker根目录的aufs路径下，为 /var/lib/docker/aufs/diff/；对于每一个镜像层，docker都会保存一份相应的 json文件，json文件的存储路径为 /var/lib/docker/graph

### 通过ubuntu镜像创建一个docker容器，命名为hw4，并启动
```
docker create -it --name hw4 ubuntu /bin/bash
docker start -i hw4
```
### 再开一个新的终端以查看容器的挂载记录
```
df -hT
```
挂载记录如下
```
none                         aufs       19G  7.7G  9.5G  45% /var/lib/docker/aufs/mnt/927ea757f058cf910cf9720fda932b17968ac62b353b42f8d8c8819970f47dcd
```
### 查看层级信息
```
cd /var/lib/docker/aufs/layers
cat 927ea757f058cf910cf9720fda932b17968ac62b353b42f8d8c8819970f47dcd
```
显示出如下层级信息，927ea757f058cf910cf9720fda932b17968ac62b353b42f8d8c8819970f47dcd是只读层，从下至上的五层是Ubuntu镜像中的，最上面一层是容器运行时创建的
```
927ea757f058cf910cf9720fda932b17968ac62b353b42f8d8c8819970f47dcd-init
3f4753a50a4ac039b7dc059818395c653f3afa8a4d0104f8db7bc42a7291c76f
b70de0e23202701f5298813331c7f57679b30a0467efafd1eba99a119ca11e7c
43251f5dc49cc7dbbd4344212bce2ae564d24d928cbd9933bcbe11972d727f93
3f519af4b36f34c2caf181b699043aa679751827f903b10267f01fc6e3524d59
7a3804e013b94d6ac8df3ad94ddd68e0e314de65febee115beb325bf2bfadb79
```
### 保存层级信息
创建新的目录用来保存
```
mkdir /home/pkusei/hw_images
```
保存到创建的目录下
```
cp -r 7a3804e013b94d6ac8df3ad94ddd68e0e314de65febee115beb325bf2bfadb79/ \
 /home/pkusei/hw_images/0
cp -r 3f519af4b36f34c2caf181b699043aa679751827f903b10267f01fc6e3524d59/ \
 /home/pkusei/hw_images/1
cp -r 43251f5dc49cc7dbbd4344212bce2ae564d24d928cbd9933bcbe11972d727f93/ \
 /home/pkusei/hw_images/2
cp -r b70de0e23202701f5298813331c7f57679b30a0467efafd1eba99a119ca11e7c/ \
 /home/pkusei/hw_images/3
cp -r 3f4753a50a4ac039b7dc059818395c653f3afa8a4d0104f8db7bc42a7291c76f/ \
 /home/pkusei/hw_images/4
```
### 切换到原来的终端，在容器中安装软件
```
apt update
apt install nginx
apt install vim
```
### 切换到另一个终端，保存927ea757f058cf910cf9720fda932b17968ac62b353b42f8d8c8819970f47dcd最高层
```
cp -r 927ea757f058cf910cf9720fda932b17968ac62b353b42f8d8c8819970f47dcd/ \
 /home/pkusei/hw_images/software
```
### 使用aufs挂载保存的镜像
创建挂载点
```
mkdir /home/pkusei/hw_mount
```
将镜像挂载到挂载点下
```
mount -t aufs -o br=/home/pkusei/hw_images/software=ro\
 :/home/pkusei/hw_images/4=ro:/home/pkusei/hw_images/3=ro\
 :/home/pkusei/hw_images/2=ro:/home/pkusei/hw_images/1=ro\
 :/home/pkusei/hw_images/0=ro none /home/pkusei/hw_mount
```
### 从挂载点创建新镜像
切换到挂载点
```
cd /home/pkusei/hw_mount
```
创建镜像
```
tar -c . | docker import - hw4_image
```
### 从该镜像中创建容器，使用软件包
创建容器
```
docker run -it --name hw4_image_docker hw4_image /bin/bash
```
查看容器中是否可以使用vim，nginx等之前安装的软件
```
vim 233.txt
```
可以使用vim指令编辑文件，可以使用之前安装好的软件包











