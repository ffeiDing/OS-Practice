


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
第一步，通过镜像创建容器，需要在镜像中指定容器的功能：（1）部署etcd （2）判断自己是不是master，如果是，部署jupyter notebook （3）容器间互相免密登录 （4）host表中的名字按顺序排列；

第二步，挂代理，使得可以从外部访问该集群

第三步，创建framework，以calico网络启动容器

### 2、具体流程






