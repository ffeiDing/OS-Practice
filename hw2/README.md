# 第二次作业
## 一、Mesos组成结构、在源码中具体位置与工作流程
### 1、Mesos组成结构
<div align=center><img width="75%" height="75%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/Mesos%E6%A1%86%E6%9E%B6%E5%9B%BE.png"/></div>
如上图所示，Mesos主要组件有：

* Zookeeper：选举出Mesos master。
* Mesos master：接收Mesos slave和Framework scheduler的注册，分配资源。
* Standby master：作为备用Master，与Master节点运行在同一集群中。在Master宕机后Zookeeper可以很快地从其中选举出新的Master，恢复状态。
* Mesos slave：接收Mesos master发来的Task，调度Framework executor去执行。
* Framework：例如Spark，Hadoop等，包括Scheduler和Executor两部分。Scheduler启动后注册到Master，决定是否接收Master发送来的Resource offer消息，并反馈给Master。Executor由Slave调用，执行Framework的Task。
* Task：Task由Slave调度Exexutor执行，可以是长生命周期的，也可以是短生命周期的。

### 2、源码中具体位置

* Zookeeper：
* Mesos master：位于mesos-1.1.0/src/master文件夹中，其中的main.cpp是入口程序，
* Standby master：
* Mesos slave：
* Framework：
* Task：
