

# 第五次作业
## 一、描述Linux内核如何对IP数据包进行处理
如下图所示，Linux内核通过Netfilter进行IP数据包处理

<img width="90%" height="90%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/Linux网络包处理.png"/>

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

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/VLAN设备工作过程.png"/>

* 如图所示，VLAN设备是以母子关系成对出现的，母设备相当于现实世界中的交换机TRUNK口，用于连接上级网络，子设备相当于普通接口用于连接下级网络。当一个子设备有一包数据需要发送时，数据将被加入VLAN Tag然后从母设备发送出去。当母设备收到一包数据时，它将会分析其中的VLAN Tag，如果有对应的子设备存在，则把数据转发到那个子设备上并根据设置移除VLAN Tag，否则丢弃该数据。和Bridge一样，母子设备的数据也是有方向的，子设备收到的数据不会进入母设备，同样母设备上请求发送的数据不会被转到子设备上。

* 需要注意的是母子VLAN设备拥有相同的MAC地址，多个VLAN设备会共享一个MAC。当一个母设备拥有多个VLAN子设备时，子设备之间是隔离的，不存在Bridge那样的交换转发关系，如果子设备间想要交换数据，就需要将子设备attach到bridge上。

### 3、veth工作过程

* VETH的作用是反转通讯数据的方向，需要发送的数据会被转换成需要收到的数据重新送入内核网络层进行处理，从而间接地完成数据的注入。VETH设备总是成对出现，送到一端请求发送的数据总是从另一端以请求接受的形式出现。该设备不能被用户程序直接操作，但使用起来比较简单。创建并配置正确后，向其一端输入数据，VETH会改变数据的方向并将其送入内核网络核心，完成数据的注入，在另一端能读到此数据。

## 四、说明在calico容器网络中，一个数据包从源容器发送到目标容器接收的具体过程

### 1、整体架构
calico能够方便的部署在物理服务器、虚拟机或者容器环境下。同时calico自带的基于iptables的ACL管理组件非常灵活，能够满足比较复杂的安全隔离需求。

在主机网络拓扑的组织上，calico在主机上启动虚拟机路由器，将每个主机作为路由器使用，组成互联互通的网络拓扑。当安装了calico的主机组成集群后，每个主机上都部署了calico/node作为虚拟路由器，并且可以通过calico将宿主机组织成任意的拓扑集群。当集群中的容器需要与外界通信时，就可以通过BGP协议将网关物理路由器加入到集群中，使外界可以直接访问容器IP，而不需要做任何NAT之类的复杂操作。

架构如下图所示

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/calico%E6%9E%B6%E6%9E%84.png"/>

* Felix：Calico Agent，跑在每台需要运行Workload的节点上，主要负责配置路由及ACLS等信息来确保Endpoint的连通状态

* etcd：分布式键值存储，主要负责网络元数据一致性，确保Calico网络状态的准确性

* BGP Client (BIRD): 主要负责把Felix写入Kernel的路由信息分发到当前Calico网络，确保Workload间的通信的有效性

* BGP Route Reflector (BIRD)：大规模部署时使用，摒弃所有节点互联的mesh模式，通过一个或者多个BGP Route Reflector来完成集中式的路由分发

### 2、通信流程

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/跨主机通信.png"/>

从上图可以看出，当容器创建时，calico为容器生成veth pair，一端作为容器网卡加入到容器的网络命名空间，并设置IP和掩码，一端直接暴露在宿主机上，并通过设置路由规则，将容器IP暴露到宿主机的通信路由上。于此同时，calico为每个主机分配了一段子网作为容器可分配的IP范围，这样就可以根据子网的CIDR为每个主机生成比较固定的路由规则。

当容器需要跨主机通信时，主要经过下面的简单步骤：

* 容器流量通过veth pair到达宿主机的网络命名空间上

* 根据容器要访问的IP所在的子网CIDR和主机上的路由规则，找到下一跳要到达的宿主机IP

* 流量到达下一跳的宿主机后，根据当前宿主机上的路由规则，直接到达对端容器的veth pair插在宿主机的一端，最终进入容器


## 五、调研除calico以外的任意一种容器网络方案(如weave、ovs、docker swarm overlay)，比较其与calico的优缺点
### 1、weave
### weave架构
weave通过在docker集群的每个主机上启动虚拟的路由器，将主机作为路由器，形成互联互通的网络拓扑，在此基础上，实现容器的跨主机通信。其主机网络拓扑参见下图： 

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/weave网络通信模型.png"/>

在每一个部署Docker的主机（可能是物理机也可能是虚拟机）上都部署有一个W（即weave router，它本身也可以以一个容器的形式部署）。weave网络是由这些weave routers组成的对等端点（peer）构成，并且可以通过weave命令行来定制网络拓扑。

每个部署了weave router的主机之间都会建立TCP和UDP两个连接，保证weave router之间控制面流量和数据面流量的通过。控制面由weave routers之间建立的TCP连接构成，通过它进行握手和拓扑关系信息的交换通信。控制面的通信可以被配置为加密通信。而数据面由weave routers之间建立的UDP连接构成，这些连接大部分都会加密。这些连接都是全双工的，并且可以穿越防火墙。 

### weave通信流程

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/weave跨主机通信.png"/>

如上图所示，对每一个weave网络中的容器，weave都会创建一个网桥，并且在网桥和每个容器之间创建一个veth pair，一端作为容器网卡加入到容器的网络命名空间中，并为容器网卡配置ip和相应的掩码，一端连接在网桥上，最终通过宿主机上weave router将流量转发到对端主机上。其基本过程如下：

* 容器流量通过veth pair到达宿主机上weave router网桥上

* weave router在混杂模式下使用pcap在网桥上截获网络数据包，并排除由内核直接通过网桥转发的数据流量，例如本子网内部、本地容器之间的数据以及宿主机和本地容器之间的流量。捕获的包通过UDP转发到所其他主机的weave router端

* 在接收端，weave router通过pcap将包注入到网桥上的接口，通过网桥的上的veth pair，将流量分发到容器的网卡上


### 2、calico与weave比较
#### calico优势：

跨主机通信时，整个通信路径完全没有使用NAT或者UDP封装，性能上的损耗比较低

#### calico劣势：

* calico的通信机制是完全基于三层的，目前只支持TCP、UDP、ICMP、ICMPv6协议，如果使用其他四层协议（例如NetBIOS协议），建议使用weave、原生overlay等其他overlay网络实现

* 基于三层实现通信，在二层上没有任何加密包装，因此只能在私有的可靠网络上使用

* 流量隔离基于iptables实现，并且从etcd中获取需要生成的隔离规则，有一些性能上的隐患

### weave优势：

* 可以完全自定义整个集群的网络拓扑

* 支持通信加密

### weave劣势：

* weave自定义容器数据包的封包解包方式，不够通用，传输效率比较低，性能上的损失也比较大

* 集群配置比较负载，需要通过weave命令行来手工构建网络拓扑，在大规模集群的情况下，加重了管理员的负担


## 五、编写一个mesos framework，使用calico容器网络自动搭建一个docker容器集群（docker容器数量不少于三个），并在其中一个容器中部署jupyter notebook。运行后外部主机可以通过访问宿主机ip+8888端口使用jupyter notebook对docker集群进行管理
* 分别在三台主机上安装etcd，并使用service命令关掉自动开启etcd后台程序
```
apt install etcd
service etcd stop
```
* 分别在三台主机上输入如下命令来创建etcd集群环境
```
etcd --name node0 --initial-advertise-peer-urls http://172.16.6.192:2380 \
--listen-peer-urls http://172.16.6.192:2380 \
--listen-client-urls http://172.16.6.192:2379,http://127.0.0.1:2379 \
--advertise-client-urls http://172.16.6.192:2379 \
--initial-cluster-token etcd-cluster-hw5 \
--initial-cluster node0=http://172.16.6.192:2380,node1=http://172.16.6.224:2380,node2=http://172.16.6.213:2380 \
--initial-cluster-state new
```
```
etcd --name node1 --initial-advertise-peer-urls http://172.16.6.224:2380 \
--listen-peer-urls http://172.16.6.224:2380 \
--listen-client-urls http://172.16.6.224:2379,http://127.0.0.1:2379 \
--advertise-client-urls http://172.16.6.224:2379 \
--initial-cluster-token etcd-cluster-hw5 \
--initial-cluster node0=http://172.16.6.192:2380,node1=http://172.16.6.224:2380,node2=http://172.16.6.213:2380 \
--initial-cluster-state new
```
```
etcd --name node2 --initial-advertise-peer-urls http://172.16.6.213:2380 \
--listen-peer-urls http://172.16.6.213:2380 \
--listen-client-urls http://172.16.6.213:2379,http://127.0.0.1:2379 \
--advertise-client-urls http://172.16.6.213:2379 \
--initial-cluster-token etcd-cluster-hw5 \
--initial-cluster node0=http://172.16.6.192:2380,node1=http://172.16.6.224:2380,node2=http://172.16.6.213:2380 \
--initial-cluster-state new
```
在1001上检查
```
etcdctl cluster-health
member 9b9bffb2a23f982 is healthy: got healthy result from http://172.16.6.192:2379
member 7fbe2c2ad27dba8d is healthy: got healthy result from http://172.16.6.224:2379
member ce77e5ded1584bf3 is healthy: got healthy result from http://172.16.6.213:2379
cluster is healthy
```
* 三台主机都需要退出其他集群网络，比如之前作业中的swarm
```
docker swarm leave --force
```
* 在三台主机上修改docker daemon，使docker支持etcd
```
service docker stop
dockerd --cluster-store etcd://172.16.6.192:2379 &
```
```
service docker stop
dockerd --cluster-store etcd://172.16.6.224:2379 &
```
```
service docker stop
dockerd --cluster-store etcd://172.16.6.213:2379 &
```
* 在三台主机上安装calico
```
wget -O /usr/local/bin/calicoctl https://github.com/projectcalico/calicoctl/releases/download/v1.1.3/calicoctl
chmod +x /usr/local/bin/calicoctl
```
* 在三台主机上启动calico容器
```
calicoctl node run --ip 172.16.6.192 --name node0
```
```
calicoctl node run --ip 172.16.6.224 --name node1
```
```
calicoctl node run --ip 172.16.6.213 --name node2
```
在1001服务器上检查
```
calicoctl node status
Calico process is running.

IPv4 BGP status
+--------------+-------------------+-------+----------+-------------+
| PEER ADDRESS |     PEER TYPE     | STATE |  SINCE   |    INFO     |
+--------------+-------------------+-------+----------+-------------+
| 172.16.6.224 | node-to-node mesh | up    | 05:54:47 | Established |
| 172.16.6.213 | node-to-node mesh | up    | 05:54:55 | Established |
+--------------+-------------------+-------+----------+-------------+
IPv6 BGP status
No IPv6 peers found.
```
* 在1001主机上创建calico的IP池
```
cat << EOF | calicoctl create -f -
- apiVersion: v1
  kind: ipPool
  metadata:
    cidr: 192.0.2.0/24
EOF
Successfully created 1 'ipPool' resource(s)
```
* 在三台主机上通过创建Dockerfile制作jupyter镜像
```
FROM ubuntu:latest

MAINTAINER dff

RUN apt update
RUN apt install -y sudo python3-pip ssh

RUN pip3 install --upgrade pip
RUN pip3 install jupyter

RUN useradd -ms /bin/bash admin
RUN adduser admin sudo
RUN echo 'admin:admin' | chpasswd

RUN mkdir /var/run/sshd

RUN mkdir /home/admin/first_folder

RUN echo 'The user name is "admin". The password is "admin" by default.' > /home/admin/README.txt
RUN echo 'There are 5 containers running as a cluster. This one can be regarded as manager. The user name and password of other containers is also "admin".' >> /home/admin/README.txt
RUN echo 'The ip address of this container is "192.168.0.100".' >> /home/admin/README.txt
RUN echo 'The ip addresses of the rest containers are "192.168.0.101", "192.168.0.102", "192.168.0.103" and "192.168.0.104".' >> /home/admin/README.txt
RUN echo 'Run command "/usr/sbin/sshd" to use ssh.' >> /home/admin/README.txt
RUN echo 'The Internet access and sudo privilege are available. You can install software packages by "sudo apt install".' >> /home/admin/README.txt

USER admin
WORKDIR /home/admin

CMD ["/usr/local/bin/jupyter", "notebook", "--NotebookApp.token=", "--ip=0.0.0.0", "--port=8888"]
```
创建镜像
```
docker build -t jupyter .
```
* 在三台主机上通过Dockerfile制作带ssh的ubuntu镜像
```
FROM ubuntu:latest

MAINTAINER dff

RUN apt update
RUN apt install -y sudo ssh

RUN useradd -ms /bin/bash admin
RUN adduser admin sudo
RUN echo 'admin:admin' | chpasswd

RUN mkdir /var/run/sshd

RUN mkdir /home/admin/first_folder
USER admin
WORKDIR /home/admin

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
```
创建镜像
```
docker build -t ubuntu_ssh .
```
* 在1001服务器上创建calico容器网络
```
docker network create --driver calico --ipam-driver calico-ipam --subnet=192.168.0.0/16 my_net
```
* 安装configurable-http-proxy
```
apt install -y npm nodejs-legacy
npm install -g configurable-http-proxy
```
* 在1002和1003上提前设置机器到jupyter容器的转发
```
nohup configurable-http-proxy --default-target=http://192.168.0.100:8888 --ip=172.16.6.224 --port=8888 > http_proxy.log 2>&1 &
```
```
nohup configurable-http-proxy --default-target=http://192.168.0.100:8888 --ip=172.16.6.213 --port=8888 > http_proxy.log 2>&1 &
```
* 创建scheduler.py，运行5个任务
```
#!/usr/bin/env python2.7
from __future__ import print_function

import subprocess
import sys
import uuid
import time
import socket
import signal
import getpass
from threading import Thread
from os.path import abspath, join, dirname

from pymesos import MesosSchedulerDriver, Scheduler, encode_data
from addict import Dict

TASK_CPU = 0.1
TASK_MEM = 128
TASK_NUM = 5

agent_map = Dict()
AGENT_1 = 'a6b6e216-eef0-421b-a23f-19da2f0ca329-S1'
AGENT_2 = '1fe90052-cd8d-455d-a587-239c4aee74ad-S0'
AGENT_3 = '1fe90052-cd8d-455d-a587-239c4aee74ad-S1'


class JupyterScheduler(Scheduler):

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

			# Launching tasks
			if self.launched_task == 0:
				# ip
				ip = Dict()
				ip.key = 'ip'
				ip.value = '192.168.0.100'

				# hostname
				hostname = Dict()
				hostname.key = 'hostname'
				hostname.value = 'cluster'

				# NetworkInfo
				NetworkInfo = Dict()
				NetworkInfo.name = 'my_net'

				# DockerInfo
				DockerInfo = Dict()
				DockerInfo.image = 'jupyter'
				DockerInfo.network = 'USER'
				DockerInfo.parameters = [ip, hostname]

				# ContainerInfo
				ContainerInfo = Dict()
				ContainerInfo.type = 'DOCKER'
				ContainerInfo.docker = DockerInfo
				ContainerInfo.network_infos = [NetworkInfo]

				# CommandInfo
				CommandInfo = Dict()
				CommandInfo.shell = False

				task = Dict()
				task_id = 'node0'
				task.task_id.value = task_id
				task.agent_id.value = offer.agent_id.value
				task.name = 'Docker jupyter task'
				task.container = ContainerInfo
				task.command = CommandInfo

				task.resources = [
					dict(name='cpus', type='SCALAR', scalar={'value': TASK_CPU}),
					dict(name='mem', type='SCALAR', scalar={'value': TASK_MEM}),
				]

				print("Launching the jupyter task")

				self.launched_task += 1
				driver.launchTasks(offer.id, [task], filters)

				global agent_map
				num = agent_map[task.agent_id.value]

				args = ['/usr/local/bin/configurable-http-proxy']
				if num == 0:
					args.append('--default-target=http://192.168.0.100:8888')
				elif num == 1:
					args.append('--default-target=http://172.16.6.224:8888')
				else:
					args.append('--default-target=http://172.16.6.213:8888')

				args.append('--ip=172.16.6.192')
				args.append('--port=8888')
				subprocess.Popen(args)

			else:
				# ip
				ip = Dict()
				ip.key = 'ip'
				ip.value = '192.168.0.10' + str(self.launched_task)

				# hostname
				hostname = Dict()
				hostname.key = 'hostname'
				hostname.value = 'cluster'

				# NetworkInfo
				NetworkInfo = Dict()
				NetworkInfo.name = 'my_net'

				# DockerInfo
				DockerInfo = Dict()
				DockerInfo.image = 'ubuntu_ssh'
				DockerInfo.network = 'USER'
				DockerInfo.parameters = [ip, hostname]

				# ContainerInfo
				ContainerInfo = Dict()
				ContainerInfo.type = 'DOCKER'
				ContainerInfo.docker = DockerInfo
				ContainerInfo.network_infos = [NetworkInfo]

				# CommandInfo
				CommandInfo = Dict()
				CommandInfo.shell = False

				task = Dict()
				task_id = 'node' + str(self.launched_task)
				task.task_id.value = task_id
				task.agent_id.value = offer.agent_id.value
				task.name = 'Docker normal task'
				task.container = ContainerInfo
				task.command = CommandInfo

				task.resources = [
					dict(name='cpus', type='SCALAR', scalar={'value': TASK_CPU}),
					dict(name='mem', type='SCALAR', scalar={'value': TASK_MEM}),
				]

				print("Launching a normal task")

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

	# Framework info
	framework = Dict()
	framework.user = getpass.getuser()
	framework.name = "JupyterFramework"
	framework.hostname = socket.gethostname()

	# Use default executor
	driver = MesosSchedulerDriver(
		JupyterScheduler(),
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

	print('Scheduler running, Ctrl+C to quit.')
	signal.signal(signal.SIGINT, signal_handler)
	while driver_thread.is_alive():
		time.sleep(1)

if __name__ == '__main__':
	import logging
	logging.basicConfig(level=logging.DEBUG)
	if len(sys.argv) < 4:
		print("Usage: {} <mesos_master> <number of agent> [agent_id ...]".format(sys.argv[0]))
		sys.exit(1)
	else:
		for i in range(int(sys.argv[2])):
			agent_map[sys.argv[3 + i]] = i
		main(sys.argv[1])
```
* 在1001上启动master
```
./bin/mesos-master.sh --ip=172.16.6.192 --hostname=162.105.174.40 --work_dir=/var/lib/mesos
```
* 在1001、1002、1003上启动agent
```
./bin/mesos-agent.sh --master=172.16.6.192:5050 --work_dir=/var/lib/mesos --ip=172.16.6.192 --port=5051 --hostname=162.105.174.40 --containerizers=docker,mesos --image_providers=docker --isolation=docker/runtime
```
```
./bin/mesos-agent.sh --master=172.16.6.192:5050 --work_dir=/var/lib/mesos --ip=172.16.6.224 --port=5052  --hostname=162.105.174.40 --containerizers=docker,mesos  --image_providers=docker --isolation=docker/runtime
```
```
./bin/mesos-agent.sh --master=172.16.6.192:5050 --work_dir=/var/lib/mesos --ip=172.16.6.213 --port=5053 --hostname=162.105.174.40 --containerizers=docker,mesos --image_providers=docker --isolation=docker/runtime
```
* 运行scheduler.py
```
nohup python scheduler.py 172.16.6.192 3 a6b6e216-eef0-421b-a23f-19da2f0ca329-S1 1fe90052-cd8d-455d-a587-239c4aee74ad-S0 1fe90052-cd8d-455d-a587-239c4aee74ad-S1 > scheduler.log 2>&1 &
```
* 端口转发后，分别查看<code>http://162.105.174.40:5050</code>和<code>http://162.105.174.40:8888</code>，结果如下图所示
<img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/mesos运行框架.png"/>
<img width="90%" height="90%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/jupyter.png"/>
<img width="90%" height="90%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw5/pictures/控制台.png"/>

