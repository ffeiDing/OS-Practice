


# 第6次作业
## 一、阅读Paxos算法的材料并用自己的话简单叙述
### 1、主要角色
Paxos算法由Lamport提出，目的是让参与分布式处理的每个参与者逐步达成一致的意见。Lamport假想了一个叫Paxos的希腊城邦进行选举的情景。主要有以下三种角色：

* proposer（提议者）：提出提案，提案中含有一个value

* acceptor（接受者/选民）：接受或拒绝某一提案

* learner（学习者）：获取被大多数接受者接受的提案中包含的value

### 2、具体流程

假设信道是可靠的，即不存在拜占庭将军问题：

* 第一阶段（贿赂选民阶段）：要是有多个提议者向接受者提出提案，接受者听谁的呢？接受者会接受编号大的提议者。这里不妨假设提议者对选民进行贿赂，谁给的钱多（编号大），选民就被谁收买。选民有三种状态：（1）未被任何提议者收买；（2）被xx提议者xx贿款（编号）收买，但还没有收到提案；（3）被某一提议者以某额度贿款（编号）收买，且接受了提案。对于处于<code>状态2</code>的选民，如果此时他收到了另一土豪提议者（编号更大）的贿赂，他会很没有原则地倒戈向土豪，被土豪收买，修改自己的记录为被xx提议者（土豪）以xx贿款（土豪的编号）收买，但还没有收到提案。对于处于<code>状态3</code>的选民，如果此时他收到了另一土豪提议者（编号更大）的贿赂，他仍然会很没有原则地倒戈向土豪，被土豪收买，修改自己的记录为被xx提议者（土豪）以xx贿款（土豪的编号）收买，与状态2不同的是，他会发消息告诉土豪自己已经接受了XX提案，它是XX提议者以XX贿款贿赂我的，土豪提议者将自己的提案修改选民已经接受的提案。值得注意的是，由于是分布式处理，土豪提议者可能同时收到多个选民发来的已接受提案的信息，那么他将自己的提案改成哪个提案呢？同样是根据谁钱多听谁的的原则，他会比较这几个提案提议者的编号，接受编号最大的提议者提出的提案。

* 第二阶段（投票表决阶段）：提议者提出提案，如果接受者被他收买，则接受他的提案；如果多数接受者接受了一个提议，则该提议通过，学习者记录提案包含的value。

### 3、存在的博弈

由于接受者何时收到提议者的消息是不可控的，所以可能出现下面的情况：

* 接受者接受了某一提议者贿赂处于状态2，此时新的土豪提议者出现，接受者更新自己的记录（被土豪提议者收买，不再被原来的提议者收买），原来的提议者在第二阶段给该接受者发送提案时被拒绝；

* 接受者接受了某一提议者贿赂处于状态2，在新的土豪提议者贿赂到该接受者之前，原来的提议者已经给该接受者发送了提案并被接受了，新的土豪提议者只能修改自己的提案；

这个博弈过程最后的赢家是谁，取决于这两个提议者谁的进展更快。

## 二、模拟Raft协议工作的一个场景并叙述处理过程
### 1、节点状态转换

节点有三种状态，分别是follower, candidate, leader，转换条件如下：

* 初始状态：所有节点初始状态都为follower，每一节点维护一个日志存储变化信息

* follower -> candidate：如果一个follower很久没有收到leader发来的消息，就会成为candidate，向其他节点请求vote，其他节点会返回vote

* candidate -> leader：如果一个candidate获得大部分节点的vote，它就变为一个leader，follower -> candidate -> leader 的过程被称为leader election；之后，系统的任何变化都需要通过leader，每一变化作为节点日志的一个entry，leader写入待更新的entry（未接受）后，将它发送给follower，等待直到大部分节点写入了这一entry（未接受）后，接受这一entry并更新取值，通知follower该entry被接受，follower接受entry并更新取值，这一过程叫做log replication

### 2、场景模拟

* 当前有五个follower:

<img width="55%" height="55%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/1.png"/>

* 每个节点等待150ms至300ms之间的一个随机数（election timeout）后，如果仍没有接收到leader发来的消息，该节点变为一个candidate，这里Node A最先超时变为candidate:

<img width="55%" height="55%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/2.png"/>

* candidate向follower发送vote申请，如果follower没有投过票，则投票给该candidate并重新设定自己的（election timeout），candidate投票给自己。这里，B、C、D、E投票给A，A已有自己的一票：

<img width="55%" height="55%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/3.png"/>

* candidate获取大多数节点的vote后成为leader。这里A成为leader，B、C、D、E的election timeout仍然在转（如果考虑极端情况，即两个follower同时变为candidate，在没有follower获取大多数vote的情况下，开始新一轮选举，直到有节点获得大多数vote）：

<img width="55%" height="55%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/4.png"/>

* leader以一定周期（heartbeat timeout）向follower发送append entries消息，follower回复该消息。这里A以一定周期向B、C、D、E发送append entries消息，B、C、D、E回复该消息：

<img width="55%" height="55%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/5.png"/>

* 当follower没有接收到leader发来的heartbeat，它等待一个election timeout变为candidate，开始新的选举。该情境中，假设leaderA宕机，新的leaderB被选举产生：

<img width="55%" height="55%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/6.png"/>

* 当系统有变化产生后，leader通过append entries通知follower，follower做出反馈。在这里，client发送change给leaderB，leaderB在自己的log中添加entry<code>set 5</code>，此时该信息并未被接受；leaderB向followerA、C、D、E发送该entry，活跃的follower在自己的log中添加entry<code>set 5</code>，此时该信息并未被接受，并返回消息给leaderB

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/7.png"/>

* leader发现大多数节点添加了修改信息后，接受该修改信息，通知follower自己已接受该修改信息，同时还通知client修改完毕。在这里，leaderB接受<code>set 5</code>，修改自己的值为5，发送消息告诉followerA、C、D、E自己已经接受<code>set 5</code>，同时发送消息告诉client修改完毕：

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/8.png"/>

* follower收到消息后，接受修改信息，leader继续以一定周期（heartbeat timeout）向follower发送append entries消息，攻follower确认leader还活着。该例子中，followerC、D、E接受<code>set 5</code>，修改自己的值为5，之后继续接受leader的heartbeats。

<img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/9.png"/>

## 三、简述Mesos的容错机制并验证
### 1、master宕机

<img width="50%" height="50%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/master_fault.png"/>

根据mesos的架构，可以看到除了当前活跃的master，还有多个standby master，它们都被zookeeper监视着。一旦active master宕机，zookeeper会立刻在standby master中选举产生新的master；master是soft state的，即新选出的master可以很快重建原来master的状态，这是因为master的状态本来就是active slaves、active frameworks和running tasks的链表，slaves、schedulers与新选出的master通信，就可以恢复原来master的状态。

### 2、slave或executor出错

mesos会将slave或executor的错误汇报给所在framework的scheduler，framework根据自己的policies决定如何处理。

### 3、scheduler出错

mesos允许一个framework注册多个scheduler，这样当一个出错崩溃后，另一个可以立即被master通知来接替原来scheduler的工作。同一个framework的不同schedulers之间的状态如何共享取决于framework自己的算法。

### 4、验证master宕机后的恢复
* 分别在1001、1002、1003上配置zookeeper
```
wget http://mirror.nexcess.net/apache/zookeeper/stable/zookeeper-3.4.10.tar.gz
tar -zxf zookeeper-3.4.10.tar.gz
```
* 修改zookeeper配置文件
```
cd zookeeper-3.4.10/
cd conf/
cp zoo_sample.cfg zoo.cfg
vim zoo.cfg

# 修改dataDir为
dataDir=/var/lib/zookeeper

# 添加
# master server
server.1=172.16.6.192:2888:3888
server.2=172.16.6.224:2888:3888
server.3=172.16.6.213:2888:3888
```

* 分别在三台主机的系统var/lib目录下创建/zookeeper/myid文件，记录对应的id
```
# 进入系统tmp目录
root@oo-lab:/var/lib# mkdir zookeeper
root@oo-lab:/var/lib# cd zookeeper
root@oo-lab:/var/lib/zookeeper# vim myid
# 1001为1，1002为2，1003为3
echo "1" > /var/lib/zookeeper/id_record
```

* 分别在三台主机上启动并查看zookeeper集群状态，为leader或者follower
```
bin/zkServer.sh start
ZooKeeper JMX enabled by default
Using config: /home/pkusei/zookeeper-3.4.10/bin/../conf/zoo.cfg
Starting zookeeper ... STARTED
bin/zkServer.sh status
# 1001
ZooKeeper JMX enabled by default
Using config: /home/pkusei/zookeeper-3.4.10/bin/../conf/zoo.cfg
Mode: follower
# 1002
ZooKeeper JMX enabled by default
Using config: /home/pkusei/zookeeper-3.4.10/bin/../conf/zoo.cfg
Mode: leader
# 1003
ZooKeeper JMX enabled by default
Using config: /home/pkusei/zookeeper-3.4.10/bin/../conf/zoo.cfg
Mode: follower
```
* 启动master
```
# 1001
./mesos-master.sh --zk=zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos \
--quorum=2 --ip=172.16.6.192 --port=7070 --cluster=mesos_with_zookeeper \
--hostname=162.105.174.40 --work_dir=/var/lib/mesos 

# 1002
./mesos-master.sh --zk=zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos \
--quorum=2 --ip=172.16.6.224 --port=5050 --cluster=mesos_with_zookeeper \
--hostname=162.105.174.40 --work_dir=/var/lib/mesos 

# 1003
./mesos-master.sh --zk=zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos \
--quorum=2 --ip=172.16.6.213 --port=6060 --cluster=mesos_with_zookeeper \
--hostname=162.105.174.40 --work_dir=/var/lib/mesos
```

* 观察日志，发现1002被选为master
```
I0529 06:19:57.375041 29924 master.cpp:2137] The newly elected leader is master@172.16.6.224:5050 with id ef10001b-a6f2-4350-a6f4-58f448f676bd
I0529 06:19:57.255020 63587 network.hpp:480] ZooKeeper group PIDs: { log-replica(1)@172.16.6.192:7070, log-replica(1)@172.16.6.213:6060, log-replica(1)@172.16.6.224:5050 }
```

* 在三台主机上各启动一个agent
```
# 1001 
./mesos-agent.sh --master=zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos --work_dir=/var/lib/mesos --log_dir=/var/log/mesos --ip=172.16.6.192 --port=7071 \
--hostname=162.105.174.40 --containerizers=docker,mesos --image_providers=docker \
--isolation=docker/runtime

# 1002
./mesos-agent.sh --master=zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos --work_dir=/var/lib/mesos --log_dir=/var/log/mesos --ip=172.16.6.224 --port=7072 \
--hostname=162.105.174.40 --containerizers=docker,mesos --image_providers=docker \
--isolation=docker/runtime

# 1003
./mesos-agent.sh --master=zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos --work_dir=/var/lib/mesos --log_dir=/var/log/mesos --ip=172.16.6.213 --port=7073 \
--hostname=162.105.174.40 --containerizers=docker,mesos --image_providers=docker \
--isolation=docker/runtime
```

* 运行一个简单的test_scheduler以供测试
```
python test_scheduler.py zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos

# 成功运行
DEBUG:root:Status update TID 0552b6e0-c955-4b13-ae1c-b12adc147dc5 TASK_FINISHED
DEBUG:root:Status update TID a2c05e5d-8d0b-474c-a1c7-a3e8c4422335 TASK_FINISHED
DEBUG:root:Status update TID 33946d3c-9319-4624-a5b9-74fc781114ad TASK_RUNNING
DEBUG:root:Status update TID 2615912f-567a-4bfb-a61a-a6599c6af5e3 TASK_RUNNING
DEBUG:root:Status update TID 6b5f7b48-7a25-4963-8aef-aef4be9edc93 TASK_RUNNING
DEBUG:root:Status update TID f38d6280-5340-4381-a08f-9389be24719f TASK_RUNNING
DEBUG:root:Status update TID 328bad6b-b6b2-4b88-9db2-00f00fdff938 TASK_FINISHED
DEBUG:root:Status update TID 5f50704e-2b60-4b68-8bec-3a66b4935a15 TASK_RUNNING
DEBUG:root:Status update TID b1879949-909f-485a-aa1b-e32200593262 TASK_FINISHED
DEBUG:root:Status update TID ea67958f-e039-4162-b6ab-8c8d00d994ca TASK_FINISHED
DEBUG:root:Status update TID c1cb8c44-188a-4cad-bee9-364f4b86c938 TASK_RUNNING
DEBUG:root:Status update TID 83bf0a63-f04d-4860-b3f7-01d2425e70c5 TASK_RUNNING
DEBUG:root:Status update TID db79f1ca-8583-4ace-8e36-fcc44b675af5 TASK_FINISHED
DEBUG:root:Status update TID 81bfe027-ee30-4611-a99a-8f0c5a373e28 TASK_RUNNING
DEBUG:root:Status update TID 4449024c-682d-4951-97c4-40a4bb185788 TASK_FINISHED
DEBUG:root:Status update TID 77db5e5f-d328-4938-9e4f-3a9eb3c1eaef TASK_FINISHED
DEBUG:root:Status update TID 84fc10fc-87b3-4ccb-89a5-6952188edd30 TASK_RUNNING
DEBUG:root:Status update TID 5d2b9764-741f-4830-b1c9-bf840a4f24a3 TASK_RUNNING
```

* 终止master后，发现新的master被选举产生
```
I0530 03:03:14.065492 43034 network.hpp:480] ZooKeeper group PIDs: { log-replica(1)@172.16.6.192:7070, log-replica(1)@172.16.6.213:6060 }
I0530 03:03:14.072106 43032 zookeeper.cpp:259] A new leading master (UPID=master@172.16.6.213:6060) is detected
I0530 03:03:14.074673 43032 master.cpp:2137] The newly elected leader is master@172.16.6.213:6060 with id 55a901ac-4352-457f-9942-7315450300c0
```

* 恢复原来的master后，原来的master自杀，以普通身份加入zookeeper集群
```
W0530 03:05:11.736099 65237 master.cpp:6846] Master returning resources offered to framework c77b154b-823c-48d3-b054-a61f7ed1a22c-0000 because the framework has terminated or is inactive
I0530 03:05:11.737133 65237 master.cpp:2137] The newly elected leader is None
Lost leadership... committing suicide!
I0530 03:05:11.860321 65240 network.hpp:480] ZooKeeper group PIDs: { log-replica(1)@172.16.6.192:7070, log-replica(1)@172.16.6.213:6060, log-replica(1)@172.16.6.224:5050 }
```

## 四、综合作业
### 1、整体思路
第一步，在三台主机上以glusterfs实现分布式存储

第二步，通过镜像创建容器，需要在镜像中指定容器的功能：

（1）部署etcd 

（2）容器间互相免密登录 

（3）循环判断自己是不是master，如果是，部署jupyter notebook

（4）维护host表

第三步，挂代理，使得可以从外部访问该集群

第四步，创建framework，以calico网络启动容器

### 2、具体流程
* 在三台主机上以glusterfs实现分布式存储，具体参考hw4

```
# 在三台主机上安装gluterfs
apt install glusterfs-server

# 分别修改/etc/hosts，下面是1001的例子
vim /etc/hosts
127.0.0.1       server1 localhost
127.0.1.1       oo-lab.cs1cloud.internal        oo-lab
172.16.6.224    server2
172.16.6.213    server3

# 创建卷
mkdir -p /data/brick
gluster volume create my_volume replica 3 server1:/data/brick server2:/data/brick server3:/data/brick force
gluster volume start my_volume
gluster volume info

# 在三台主机上分别创建挂载点，挂载my_volume卷
mkdir -p /storage2
mount -t glusterfs server1:/my_volume /storage2
```

* 部署etcd

```
RUN wget -P /root https://github.com/coreos/etcd/releases/download/v3.1.7/etcd-v3.1.7-linux-amd64.tar.gz && tar -zxf /root/etcd-v3.1.7-linux-amd64.tar.gz -C /root
RUN ln -s /root/etcd-v3.1.7-linux-amd64/etcd /usr/local/bin/etcd && ln -s /root/etcd-v3.1.7-linux-amd64/etcdctl /usr/local/bin/etcdctl
```

启动etcd，将下段代码写入容器启动后执行的python代码中

```
def start_etcd(ip_addr):
    args = ['/usr/local/bin/etcd', '--name', 'node' + ip_addr[-1], \
    '--data-dir', '/var/lib/etcd', \
    '--initial-advertise-peer-urls', 'http://' + ip_addr + ':2380', \
    '--listen-peer-urls', 'http://' + ip_addr + ':2380', \
    '--listen-client-urls', 'http://' + ip_addr + ':2379,http://127.0.0.1:2379', \
    '--advertise-client-urls', 'http://' + ip_addr + ':2379', \
    '--initial-cluster-token', 'etcd-cluster-hw6', \
    '--initial-cluster', 'node0=http://192.168.0.100:2380,node1=http://192.168.0.101:2380,node2=http://192.168.0.102:2380,node3=http://192.168.0.103:2380,node4=http://192.168.0.104:2380', \
    '--initial-cluster-state', 'new']
    subprocess.Popen(args)
```
* 容器间互相免密登录 

涉及到对公钥、私钥的处理，需要在容器启动后共享公钥，修改sshd配置文件
```
RUN mkdir /var/run/sshd
RUN echo 'AuthorizedKeysFile /ssh_info/authorized_keys' >> /etc/ssh/sshd_config
```
将下段代码写入容器启动后执行的python代码中
```
def password_ssh():
    # generate ssh private and public key
	  os.system('ssh-keygen -f /home/admin/.ssh/id_rsa -t rsa -N ""')
    # add the public key to shared 'authorized_keys' file
	  os.system('echo "admin" | sudo -S bash -c "cat /home/admin/.ssh/id_rsa.pub >> /ssh_info/authorized_keys"')
    # start ssh service
	  os.system('/usr/sbin/service ssh start')
```

* 在master上部署jupyter notebook

通过一个while循环，不断向etcd集群发送消息，检查自己是否为master，算法如下：

（1）如果是master且是第一次成为master，部署jupyter notebook，删除原来的master宕机后在kv对中留下的/hosts目录，新建kv对/hosts/0192.168.0.10x -> 192.168.0.10x（使用0开头表示是leader）。在分布式kv对中更新/hosts目录的存活时间为30秒，这是为了如果有follower死掉，可以在30秒重新创建/hosts目录然后清除掉死掉的follower信息；对于不是刚刚成为master的情况继续添加host条目

（2）如果是follower，则继续尝试创建kv对/hosts/192.168.0.10x -> 192.168.0.10x

```
def main():
	f = os.popen("ifconfig cali0 | grep 'inet addr' | cut -d ':' -f 2 | cut -d ' ' -f 1")
	ip_addr = f.read().strip('\n')

	password_ssh()
	start_etcd(ip_addr)

	leader_flag = 0
	watch_flag = 0
	stats_url = 'http://127.0.0.1:2379/v2/stats/self'
	stats_request = urllib.request.Request(stats_url)
	while True:
		try:
			stats_reponse = urllib.request.urlopen(stats_request)

		except urllib.error.URLError as e:
			print('[WARN] ', e.reason)
			print('[WARN] Wating etcd...')

		else:
			if watch_flag == 0:
				watch_flag = 1
				watch_dog(ip_addr)

			stats_json = stats_reponse.read().decode('utf-8')
			data = json.loads(stats_json)


			if data['state'] == 'StateLeader':
				# first time to be master
				if leader_flag == 0:
					leader_flag = 1

					args = ['/usr/local/bin/jupyter', 'notebook', '--NotebookApp.token=', '--ip=0.0.0.0', '--port=8888']
					subprocess.Popen(args)

					os.system('/usr/local/bin/etcdctl rm /hosts')
					os.system('/usr/local/bin/etcdctl mk /hosts/0' + ip_addr + ' ' + ip_addr)
					os.system('/usr/local/bin/etcdctl updatedir --ttl 30 /hosts')
				# not the first time to be master
				else:
					os.system('/usr/local/bin/etcdctl mk /hosts/0' + ip_addr + ' ' + ip_addr)


			elif data['state'] == 'StateFollower':
				# be follower
				leader_flag = 0
				os.system('/usr/local/bin/etcdctl mk /hosts/' + ip_addr + ' ' + ip_addr)

		time.sleep(1)
```
* 维护host表

上一段代码中调用了host_list函数，该函数新启动一个守护进程触发watch.py，监控/hosts目录的更新变化，检测到有新创建的kv对后，立刻更新hosts文件，已经存在的kv对再创建时不会触发守护进程
```
#!/usr/bin/env python3

import subprocess, sys, os, socket, signal, json, fcntl
import urllib.request, urllib.error



def edit_hosts():
	f = os.popen('/usr/local/bin/etcdctl ls --sort --recursive /hosts')
	hosts_str = f.read()


	hosts_arr = hosts_str.strip('\n').split('\n')
	hosts_fd = open('/tmp/hosts', 'w')

	fcntl.flock(hosts_fd.fileno(), fcntl.LOCK_EX)

	hosts_fd.write('127.0.0.1 localhost cluster' + '\n')
	i = 0
	for host_ip in hosts_arr:
		host_ip = host_ip[host_ip.rfind('/') + 1:]
		if host_ip[0] == '0':
			hosts_fd.write(host_ip[1:] + ' cluster-' + str(i) + '\n')
		else:
			hosts_fd.write(host_ip + ' cluster-' + str(i) + '\n')
		i += 1

	hosts_fd.flush()
	os.system('/bin/cp /tmp/hosts /etc/hosts')
	hosts_fd.close()


def main(ip_addr):
	action = os.getenv('ETCD_WATCH_ACTION')

	stats_url = 'http://127.0.0.1:2379/v2/stats/self'
	stats_request = urllib.request.Request(stats_url)

	stats_reponse = urllib.request.urlopen(stats_request)
	stats_json = stats_reponse.read().decode('utf-8')
	data = json.loads(stats_json)

	print('[INFO] Processing', action)

	if action == 'expire':
		if data['state'] == 'StateLeader':
			os.system('/usr/local/bin/etcdctl mk /hosts/0' + ip_addr + ' ' + ip_addr)
			os.system('/usr/local/bin/etcdctl updatedir --ttl 30 /hosts')

	elif action == 'create':
		edit_hosts()
		if data['state'] == 'StateFollower':
			os.system('/usr/local/bin/etcdctl mk /hosts/' + ip_addr + ' ' + ip_addr)

if __name__ == '__main__':
	main(sys.argv[1])
```
* 编写框架，在框架中以calico网络启动容器
```
#!/usr/bin/env python2.7
from __future__ import print_function

import subprocess
import sys
import os
import uuid
import time
import socket
import signal
import getpass
from threading import Thread
from os.path import abspath, join, dirname

from pymesos import MesosSchedulerDriver, Scheduler, encode_data
from addict import Dict

TASK_CPU = 0.2
TASK_MEM = 128
TASK_NUM = 5



class DockerJupyterScheduler(Scheduler):

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
			# ip
			ip = Dict()
			ip.key = 'ip'
			ip.value = '192.168.0.10' + str(self.launched_task)

			# hostname
			hostname = Dict()
			hostname.key = 'hostname'
			hostname.value = 'cluster'

			# volume1
			volume1 = Dict()
			volume1.key = 'volume'
			volume1.value = '/storage2:/ssh_info'

			# volume2
			volume2 = Dict()
			volume2.key = 'volume'
			volume2.value = '/storage3:/home/admin/shared_folder'


			# NetworkInfo
			NetworkInfo = Dict()
			NetworkInfo.name = 'my_net'

			# DockerInfo
			DockerInfo = Dict()
			DockerInfo.image = 'etcd_image'
			DockerInfo.network = 'USER'
			DockerInfo.parameters = [ip, hostname, volume1, volume2]

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
			task.name = 'Docker task'
			task.container = ContainerInfo
			task.command = CommandInfo

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

	# Framework info
	framework = Dict()
	framework.user = getpass.getuser()
	framework.name = "DockerJupyterFramework"
	framework.hostname = socket.gethostname()

	# Use default executor
	driver = MesosSchedulerDriver(
		DockerJupyterScheduler(),
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
	if len(sys.argv) < 2:
		print("Usage: {} <mesos_master>".format(sys.argv[0]))
		sys.exit(1)
	else:
		main(sys.argv[1])
```
运行该框架
```
python hw6_scheduler.py zk://172.16.6.192:2181,172.16.6.224:2181,172.16.6.213:2181/mesos
```
查看162.105.0.40:6060，发现五个容器为running状态：

<img width="100%" height="100%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw6/picture/taskrunning.png"/>

