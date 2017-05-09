

# 第五次作业
## 一、描述Linux内核如何对IP数据包进行处理
如下图所示，Linux内核通过Netfilter进行IP数据包处理

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
### 3、只开放本机的http服务，其余协议与端口均拒绝
### 4、拒绝回应来自某一特定IP地址的ping命令
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
172.16.6.224    server2
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
### 在1003上创建容器并运行nginx
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











