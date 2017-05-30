FROM ubuntu:latest

# 安装所需的软件包
RUN apt update && apt install -y sudo python3-pip ssh net-tools curl vim
RUN pip3 install --upgrade pip && pip3 install jupyter

RUN useradd -ms /bin/bash admin && adduser admin sudo && echo 'admin:admin' | chpasswd
RUN mkdir /home/admin/first_folder

# 修改sshd配置文件以支持之后的免密访问
RUN mkdir /var/run/sshd
RUN echo 'AuthorizedKeysFile /ssh_info/authorized_keys' >> /etc/ssh/sshd_config

# 部署etcd
RUN wget -P /root https://github.com/coreos/etcd/releases/download/v3.1.7/etcd-v3.1.7-linux-amd64.tar.gz && tar -zxf /root/etcd-v3.1.7-linux-amd64.tar.gz -C /root
RUN ln -s /root/etcd-v3.1.7-linux-amd64/etcd /usr/local/bin/etcd && ln -s /root/etcd-v3.1.7-linux-amd64/etcdctl /usr/local/bin/etcdctl

# 导入入口地址代码，code目录和Dockerfile放在一起
ADD code/ /home/admin/code/

# 创建共享目录
RUN mkdir /home/admin/shared_folder

USER admin
WORKDIR /home/admin

# 入口进程
CMD ["/usr/bin/python3", "/home/admin/code/start.py"]