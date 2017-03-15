# 第二次作业
## 一、Mesos组成结构及其在源码中具体位置、工作流程
### 1、Mesos组成结构及其在源码中具体位置
<div align=center><img width="75%" height="75%" src="https://github.com/ffeiDing/OS-Practice/blob/master/hw2/Mesos%E6%A1%86%E6%9E%B6%E5%9B%BE.png"/></div>
如上图所示，Mesos主要组件有：
* Zookeeper：选举出Mesos master。
* Mesos master：接收Mesos slave和Framework scheduler的注册，分配资源
* Mwsos slave：接收Mesos master发来的任务，调度Framework executor去执行
* Framework：包括scheduler和executor两部分
