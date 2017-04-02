# 第三次作业
## 一、安装配置Docker

安装成功后，docker服务端和docker客户端版本信息如下图：
<div align=left><img width="50%" height="50%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/docker%E7%89%88%E6%9C%AC%E4%BF%A1%E6%81%AF%E6%88%AA%E5%9B%BE.png"/></div>

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

例子：
```
docker images
```
<div align=left><img width="80%" height="80%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw3/dockerimages指令运行截图.png"/></div>

* 拉取镜像
```
docker pull [OPTIONS] NAME[:TAG|@DIGEST]
参数:
-a, --all-tags=false             拉取所有tagged镜像 
--help=false                     打印使用帮助
```
例子：
```
docker pull  ubuntu:latest
docker pull  ubuntu:12.04
```



如上图所示，Framework运行在Mesos上，任务的调度和执行由Framework自己完成：

* Slave1向Master汇报其有（4CPU，4GB RAM）的空闲资源。
* Master收到Slave1发来的消息后，调用分配模块，发送一个描述Slave1当前空闲资源的resource offer给Framework1。
* Framework1的调度器回复Master，需要运行两个task在Slave1上，第一个task需要资源（2CPU, 1GB RAM），第二个task需要资源（1CPU, 2GB RAM）。
* Master把任务需求资源发送给Slave1，Slave1分配适当的资源给Framework1的Executor，然后Executor开始执行这两个任务，因为Slave1还剩（1CPU，1GB RAM）的资源还未分配，分配模块可以将这些资源提供给Framwork2来使用。
* Master把任务需求资源发送给Slave1，Slave1分配适当的资源给Framework1的Executor，然后Executor开始执行这两个任务，因为Slave1还剩（1CPU，1GB RAM）的资源还未分配，分配模块可以将这些资源提供给Framwork2来使用。
<div align=center><img width="70%" height="70%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/Spark%20框架图.png"/></div>
以Spark on Mesos为例，根据Spark官方文档，从Spark的视角看，Mesos将Spark master替换为了cluster manager，Mesos决定任务的调度和执行。

### 2、容器管理

二者的差异性主要体现在资源分配方式上。Framework在Mesos上运行时，Master向Framework报告可用的资源，至于是否接收由Framework自己决定；而程序运行在传统操作系统上时，进程向内核申请资源，申请一般都会被满足。

### 3、网络管理

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

* 与<code>master::initialize()</code>类似，在完成权限认证等一系列预备工作后，初始化资源预估器
```
Try<Nothing> initialize =
  resourceEstimator->initialize(defer(self(), &Self::usage));
```
* 确认slave工作目录存在
```
// Ensure slave work directory exists.
CHECK_SOME(os::mkdir(flags.work_dir))
  << "Failed to create agent work directory '" << flags.work_dir << "'";
```
* 确认磁盘可达
* 初始化attributes
```
Attributes attributes;
  if (flags.attributes.isSome()) {
    attributes = Attributes::parse(flags.attributes.get());
  }
```
* 初始化hostname
* 初始化statusUpdateManager
```
statusUpdateManager->initialize(defer(self(), &Slave::forward, lambda::_1)
    .operator std::function<void(StatusUpdate)>());
```
* 注册消息处理函数，伪码如下（对原代码做了整理，对几个重要的消息处理函数添加了注释）：
```
install<SlaveRegisteredMessage>(); //Slave注册成功的消息
install<SlaveReregisteredMessage>();
install<RunTaskMessage>(); //运行一个Task的消息
install<RunTaskGroupMessage>();
install<KillTaskMessage>(); //停止运行一个Task的消息
install<ShutdownExecutorMessage>();
install<ShutdownFrameworkMessage>();
install<FrameworkToExecutorMessage>();
install<UpdateFrameworkMessage>();
install<CheckpointResourcesMessage>();
install<StatusUpdateAcknowledgementMessage>();
install<RegisterExecutorMessage>(); //注册一个Executor的消息
install<ReregisterExecutorMessage>();
install<StatusUpdateMessage>(); //状态更新消息
install<ExecutorToFrameworkMessage>();
install<ShutdownMessage>();
install<PingSlaveMessage>();
```

## 四、Mesos资源调度算法
### 1、我对DRF算法的理解
* Mesos默认的资源调度算法是DRF（主导资源公平算法 Dominant Resource Fairness），它是一种支持多资源的最大-最小公平分配机制。类似网络拥塞时带宽的分配，在公平的基础上，尽可能满足更大的需求。但Mesos更为复杂一些，因为有主导资源（支配性资源）的存在。比如假设系统中有9个CPU，18GB RAM，A用户请求的资源为（1 CPU, 4 GB），B用户请求的资源为（3 CPU， 1 GB），那么A的支配性资源为内存（CPU占比1/9，内存占比4/18），B的支配性资源为CPU（CPU占比3/9，内存占比1/18）。
* DRF算法的目标是使每个用户获得相同比例的支配性资源，给A用户（3 CPU，12 GB），B用户（6 CPU，2 GB），这样A获得了2/3的内存资源，B获得了2/3的CPU资源。
* DRF鼓励用户去共享资源，如果资源是在用户之间被平均地切分，会保证没有用户会拿到更多资源。
* DRF是strategy-proof，即用户不能通过欺骗来获取更多地资源分配。
* DRF是envy-free（非嫉妒）的，没有一个用户会与其他用户交换资源分配。
* DRF分配是Pareto efficient，即不可能通过减少一个用户的资源分配来提升另一个用户的资源分配。
### 2、在源码中的位置
DRF算法的源码位于mesos-1.1.0/src/master/allocator/sorter/drf文件夹中，其中的sorter.cpp用来对framework进行排序、add、remove、update等操作。mesos-1.1.0/src/master/allocator/mesos/hierarchical.cpp文件是分层分配器，它调用了sorter.cpp和sorter.hpp进行功能上的具体实现。

## 五、写一个完成简单工作的框架

使用python语言，扩展了豆瓣的pymesos/examples文件夹下的scheduler.py和executor.py，使用蒙特卡洛法计算π的值。

蒙特卡洛算法是通过概率来计算π的值的。对于一个单位为1的正方形，以其某一个顶点为圆心，边为半径在正方形内画扇形（一个1/4的圆形的扇形），那么扇形的面积就是π/4。这样，利用概率的方式，“随机”往正方形里面放入一些“点”，根据这些点在扇形内的概率（在扇形内的点数/投的总点数）计算出π的值。

本程序中共随机了20*200000次。

Pi_scheduler.py文件如下：
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


class PiScheduler(Scheduler):
    # 初始化一些变量
    Pi = 0
    sumPi = 0
    count = 20
    i = 0
    temp = 0
    nums = 2000000

    def __init__(self, executor):
        self.executor = executor

    # 计算Pi的值，判断何时停止运行
    def frameworkMessage(self, driver, executorId, slaveId, message):
        self.sumPi = self.sumPi + float(decode_data(message))
        self.temp = self.temp + 1
        if self.temp >= self.count:
            self.Pi = self.sumPi/self.count
            print(self.Pi)
            driver.stop()

    def resourceOffers(self, driver, offers):
        if self.i >= self.count:
            return None
        filters = {'refuse_seconds': 5}

        for offer in offers:
            if self.i >= self.count:
                break
            cpus = self.getResource(offer.resources, 'cpus')
            mem = self.getResource(offer.resources, 'mem')
            if cpus < TASK_CPU or mem < TASK_MEM:
                continue

            task = Dict()
            task_id = str(uuid.uuid4())
            task.task_id.value = task_id
            task.agent_id.value = offer.agent_id.value
            task.name = 'task {}'.format(task_id)
            task.executor = self.executor
            # 保留以作测试用 ：）
            task.data = encode_data('Hello from task {}!'.format(task_id))

            task.resources = [
                dict(name='cpus', type='SCALAR', scalar={'value': TASK_CPU}),
                dict(name='mem', type='SCALAR', scalar={'value': TASK_MEM}),
            ]

            driver.launchTasks(offer.id, [task], filters)
            self.i = self.i + 1

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
    executor = Dict()
    executor.executor_id.value = 'PiExecutor'
    executor.name = executor.executor_id.value
    executor.command.value = '%s %s' % (
        sys.executable,
        abspath(join(dirname(__file__), 'executor.py'))
    )
    executor.resources = [
        dict(name='mem', type='SCALAR', scalar={'value': EXECUTOR_MEM}),
        dict(name='cpus', type='SCALAR', scalar={'value': EXECUTOR_CPUS}),
    ]

    framework = Dict()
    framework.user = getpass.getuser()
    framework.name = "PiFramework"
    framework.hostname = socket.gethostname()

    driver = MesosSchedulerDriver(
        PiScheduler(executor),
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

其中，和样例的主要差别在于：
```
 # 计算Pi的值，判断何时停止运行
    def frameworkMessage(self, driver, executorId, slaveId, message):
        self.sumPi = self.sumPi + float(decode_data(message))
        self.temp = self.temp + 1
        if self.temp >= self.count:
            self.Pi = self.sumPi/self.count
            print(self.Pi)
            driver.stop()
```

样例不会主动停止运行，可以通过调用API让程序自动终止，并打印出最终结果。

Pi_executor.py文件如下：
```
#!/usr/bin/env python2.7
from __future__ import print_function

import sys
from random import random
import time
from threading import Thread

from pymesos import MesosExecutorDriver, Executor, decode_data, encode_data
from addict import Dict


class PiExecutor(Executor):
    def launchTask(self, driver, task):
        def run_task(task):
            update = Dict()
            update.task_id.value = task.task_id.value
            update.state = 'TASK_RUNNING'
            update.timestamp = time.time()
            driver.sendStatusUpdate(update)

            # 保留以作测试用
            print(decode_data(task.data), file=sys.stderr)
            cnt = 0 
            N = 2000000
            for i in range(N) :  
                x = random()
                y = random()
                if (x*x + y*y) < 1 :  
                    cnt += 1  
            vPi = 4.0 * cnt / N 
            print(vPi)
            driver.sendFrameworkMessage(encode_data(str(vPi)))

            time.sleep(30)

            update = Dict()
            update.task_id.value = task.task_id.value
            update.state = 'TASK_FINISHED'
            update.timestamp = time.time()
            driver.sendStatusUpdate(update)

        thread = Thread(target=run_task, args=(task,))
        thread.start()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    driver = MesosExecutorDriver(PiExecutor(), use_addict=True)
    driver.run()
```

其中，和样例的主要差别在于：
```
            # 具体程序
            cnt = 0 
            N = 2000000
            for i in range(N) :  
                x = random()
                y = random()
                if (x*x + y*y) < 1 :  
                    cnt += 1  
            vPi = 4.0 * cnt / N 
            print(vPi)
            driver.sendFrameworkMessage(encode_data(str(vPi)))
```

样例仅仅是简单输出了“Hello from task...”，此处需要修改为计算Pi值的具体程序，并将单次计算结果封装传递。

运行结果截图如下，可以看到计算出的π的结果3.1414582，还是比较接近原值的，如果加大数据量，结果应该会更加准确：
<div align=center><img width="75%" height="75%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/运行结果截图.png"/></div>

资源使用情况如下：
<div align=center><img width="30%" height="30%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/资源使用情况截图.png"/></div>

