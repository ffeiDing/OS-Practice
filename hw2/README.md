# 第二次作业
## 一、Mesos组成结构、在源码中具体位置与工作流程
### 1、Mesos组成结构
<div align=center><img width="75%" height="75%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/Mesos%E6%A1%86%E6%9E%B6%E5%9B%BE.png"/></div>
如上图所示，Mesos主要组件有：

* Zookeeper：选举出Mesos master。
* Mesos master：接收Mesos slave和Framework scheduler的注册，分配资源。
* Standby master：作为备用Master，与Master节点运行在同一集群中。在Leader宕机后Zookeeper可以很快地从其中选举出新的Leader，恢复状态。
* Mesos slave：接收Mesos master发来的Task，调度Framework executor去执行。
* Framework：例如Spark，Hadoop等，包括Scheduler和Executor两部分。Scheduler启动后注册到Master，决定是否接收Master发送来的Resource offer消息，并反馈给Master。Executor由Slave调用，执行Framework的Task。
* Task：Task由Slave调度Exexutor执行，可以是长生命周期的，也可以是短生命周期的。

### 2、源码中具体位置

* Zookeeper：位于mesos-1.1.0/src/zookeeper文件夹中，其中detector.cpp用来检测当前的Leader，contender.cpp用来进行Leader的竞争。
* Master：位于mesos-1.1.0/src/master文件夹中，其中的main.cpp是入口程序，封装了Google的gflags来解析命令行参数和环境变量。在Master的初始化过程中，首先初始化Allocator，默认的Allocator是内置的Hierarchical Dominant Resource Fairness allocator。然后监听消息，注册处理函数，当收到消息时调用相应的函数。最后竞争（默认Zookeeper)成为Master中的Leader，或者检测当前的Leader。
* Slave：位于mesos-1.1.0/src/slave文件夹中，其中的main.cpp是入口程序，封装了Google的flags来解析命令行参数和环境变量。在slave.cpp中，首先初始化资源预估器、初始化attributes、初始化hostname。然后注册一系列处理函数，当收到消息时调用相应的函数。
* Test Framework：位于mesos-1.1.0/src/examples/test_framework.cpp中，在main函数中，首先指定Executor的uri，配置Executor的信息，创建Scheduler。
* Test Scheduler：位于mesos-1.1.0/src/scheduler文件夹中，其中，运行MesosSchedulerDriver的代码在mesos-1.1.0/src/sched/sched.cpp中，首先检测Leader，创建一个线程，然后注册消息处理函数，最终调用了Test Framework的resourceOffers函数，根据得到的offers，创建一系列Tasks，然后调用driver的launchTasks函数，最终向Leader发送launchTasks的消息。
* Test Executor：位于mesos-1.1.0/src/examples/test_executor.cpp中，运行MesosExecutorDriver和Slave进行通信。MesosExecutorDriver的实现在mesos-1.1.0/src/exec/exec.cpp中，类似MesosSchedulerDriver，它创建了一个线程，处理相应的消息。

### 3、工作流程

* 集群中的所有Slave节点会和Master定期进行通信，将自己的资源信息同步到Master，Master由此获知到整个集群的资源状况。
* Master会和已注册、受信任的Framework进行交互，定期将最新的资源情况发送给Framework，当Framework前端有工作需求时，将选择接收资源，否则拒绝。
* 前端用户提交了一个工作需求给Framework。
* Framework接收Master发过来的资源信息。
* Framework依据资源信息向Slave发起任务启动命令，开始调度工作。


## 二、框架在Mesos上的运行过程与在传统操作系统上运行程序对比
### 1、框架在Mesos上的运行过程
<div align=center><img width="60%" height="60%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/Mesos流程.png"/></div>
如上图所示，Framework运行在Mesos上，任务的调度和执行由Framework自己完成：

* Slave1向Master汇报其有（4CPU，4GB RAM）的空闲资源。
* Master收到Slave1发来的消息后，调用分配模块，发送一个描述Slave1当前空闲资源的resource offer给Framework1。
* Framework1的调度器回复Master，需要运行两个task在Slave1上，第一个task需要资源（2CPU, 1GB RAM），第二个task需要资源（1CPU, 2GB RAM）。
* Master把任务需求资源发送给Slave1，Slave1分配适当的资源给Framework1的Executor，然后Executor开始执行这两个任务，因为Slave1还剩（1CPU，1GB RAM）的资源还未分配，分配模块可以将这些资源提供给Framwork2来使用。
* Master把任务需求资源发送给Slave1，Slave1分配适当的资源给Framework1的Executor，然后Executor开始执行这两个任务，因为Slave1还剩（1CPU，1GB RAM）的资源还未分配，分配模块可以将这些资源提供给Framwork2来使用。
<div align=center><img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/Spark%20框架图.png"/></div>
以Spark on Mesos为例，根据Spark官方文档，从Spark的视角看，Mesos将Spark master替换为了cluster manager，Mesos决定任务的调度和执行。

### 2、与传统操作系统上运行程序对比

二者的差异性主要体现在资源分配方式上。Framework在Mesos上运行时，Master向Framework报告可用的资源，至于是否接收由Framework自己决定；而程序运行在传统操作系统上时，进程向内核申请资源，申请一般都会被满足。

## 三、Master和Slave的初始化过程
### 1、Master初始化过程
mesos-1.1.0/src/master/master.cpp对Master进行了初始化，主要是通过<code>initialize()</code>初始化函数。初始化之前，相关命令行解析等工作前文已经提到，下面仅分析初始化函数。

在<code>master::initialize()</code>初始化函数中：

* 在进行一系列权限认证、权值设置等操作后，初始化Allocator
```
// Initialize the allocator.
 allocator->initialize(
     flags.allocation_interval,
     defer(self(), &Master::offer, lambda::_1, lambda::_2),
     defer(self(), &Master::inverseOffer, lambda::_1, lambda::_2),
     weights,
     flags.fair_sharing_excluded_resource_names);
```
* 时钟开始计时
```
startTime = Clock::now();
```
* 注册消息处理函数，伪码如下（对原代码做了整理，对几个重要的消息处理函数添加了注释）：
```
install<SubmitSchedulerRequest>();
install<RegisterFrameworkMessage>(); //Framework注册
install<ReregisterFrameworkMessage>();
install<UnregisterFrameworkMessage>();
install<DeactivateFrameworkMessage>();
install<ResourceRequestMessage>(); //Slave发送来资源的要求
install<LaunchTasksMessage>(); //Framework发送来启动Task的消息
install<ReviveOffersMessage>(); 
install<KillTaskMessage>(); //Framework发送来终止Task的消息
install<StatusUpdateAcknowledgementMessage>(); 
install<FrameworkToExecutorMessage>();
install<RegisterSlaveMessage>(); //Slave注册
install<ReregisterSlaveMessage>();
install<UnregisterSlaveMessage>();
install<StatusUpdateMessage>(); //状态更新
install<ExecutorToFrameworkMessage>();
install<ReconcileTasksMessage>();
install<ExitedExecutorMessage>();
install<UpdateSlaveMessage>(); //Slave更新
install<AuthenticateMessage>();
```
* 设置http路由
* 开始竞争成为Leader，或者检测当前的Leader
```
 // Start contending to be a leading master and detecting the current
 // leader.
 contender->contend()
   .onAny(defer(self(), &Master::contended, lambda::_1));
 detector->detect()
   .onAny(defer(self(), &Master::detected, lambda::_1));
```
### 2、Slave初始化过程
mesos-1.1.0/src/slave/slave.cpp对Slave进行了初始化，主要是通过<code>initialize()</code>初始化函数。初始化之前，相关命令行解析等工作前文已经提到，下面仅分析初始化函数。

在<code>slave::initialize()</code>初始化函数中：

* 与<code>master::initialize()</code>类似，在权限认证、确认工作目录存在、磁盘可达等一系列预备工作后
