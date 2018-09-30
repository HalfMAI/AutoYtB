# AutoYtB
订阅youtuber, 有视频时自动转播到对应的b站账号

感谢autolive的参考 : https://github.com/7rikka/autoLive

## 一键安装，适合完全新手，而且服务器也没有别的其它设置的
```
wget https://raw.githubusercontent.com/HalfMAI/AutoYtB/master/newInstall.sh && chmod +x newInstall.sh && bash newInstall.sh
```
如果服务器有别的设置的话建议参考下列各个软件进行选择性安装

## 软件依赖和环境安装
#### youtube-dl, ffmpeg, python3
#### 如果使用account登录模式, 还需要安装chrome与chromedriver或firefox与firefoxdriver

ffmpeg安装,因为各系统不同安装方法也不同这里只提供vultr centos7的安装方法
```
sudo yum install epel-release -y
sudo yum update -y
sudo yum -y install gcc openssl-devel bzip2-devel libffi libffi-devel
shutdown -r now

sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm
sudo yum -y install ffmpeg
```

python3安装,这里安装的是3.7独立安装，运行时调用的是python3.7而不是python3。
如果系统没有 wget 请先运行
```
yum install -y wget
```
然后再运行下面的
```
cd /usr/src
wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
tar xzf Python-3.7.0.tgz
cd Python-3.7.0
./configure --enable-optimizations
make altinstall
```

youtube-dl安装，如果系统没有pip，请在安装python3.7后再更改为pip3.7
```
pip3.7 install youtube-dl
```

firefox与firefoxdriver安装,和chrome之间二选一安装即可
```
sudo yum -y install firefox
wget https://github.com/mozilla/geckodriver/releases/download/v0.22.0/geckodriver-v0.22.0-linux64.tar.gz
tar xvzf geckodriver-v0.22.0-linux64.tar.gz
chmod +x geckodriver
mv geckodriver /usr/bin/
rm -f geckodriver-v0.22.0-linux64.tar.gz
```

chrome与chromedriver安装,和firefox之间二选一安装即可

先配置yum源,在/ect/yum.repos.d下新建文件google-chrome.repo,写入以下内容
```
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/$basearch
enabled=1
gpgcheck=1
gpgkey=https://dl-ssl.google.com/linux/linux_signing_key.pub
```
然后执行安装chrome和下载chromedriver
```
sudo yum -y install google-chrome-stable
wget -N https://chromedriver.storage.googleapis.com/2.42/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/bin/
rm -f chromedriver_linux64.zip
```

### 代码依赖库
如果系统没有pip，请在安装python3.7后再更改为pip3.7
```
pip3.7 install requests
pip3.7 install numpy
pip3.7 install selenium
pip3.7 install Pillow
```


### 开启防火墙,这里打开的是80端口，需要根据对应配置的端口来设置
```
firewall-cmd --zone=public --add-port=80/tcp --permanent
firewall-cmd --reload
```

### 如何把当前代码传到服务器上
```
cd ~
wget https://github.com/HalfMAI/AutoYtB/archive/master.zip
unzip master.zip
cd AutoYtB-master/
```

# 运行前的配置
打开目录中的Config.json
```
{
    "serverIP": "XXXXX",      <-必需设置,用于pubsubhub的回调地址
    "serverPort": "80",       <-运行端口
    "subSecert": "",          <-会自动生成的sercert,用于pubsubhub的订阅校验，以后可能还可以用在别的地方
    "driver_type": "chrome",  <-account登录模式时使用的浏览器,可选值为chrome和firefox,请根据自己机器上安装的浏览器与驱动配置
    "login_retry_times": 3,   <-登录重试次数
    "subscribeList": [
        {
            "login_type": "cookies",                    <-登录模式,目前支持cookies及account两种模式
            "bilibili_cookiesStr": "xxxxxxxxxxx",       <-cookies登录模式时必填,输入访问B站时的requestHeader的cookies
            "auto_send_dynamic": false,                 <-开播时是否自动发动态,注意如果你的账号以前没发过动态,先手动去发条动态同意一下协议
            "dynamic_template": "转播开始了哦~",        <-开播动态内容
            "forwardLink": "",                          <-还未有用
            "bilibili_areaid": "33",                    <-自动开播时的区域ID
            "youtubeChannelId": "UCWCc8tO-uUl_7SJXIKJACMw",     <-订阅的youtube channel_id
            "twitcast": "kaguramea"                     <-以后可能可以做到twitcast的监控？先写着吧
        },
        {
            "login_type": "account",                    <-登录模式,目前支持cookies及account两种模式
            "username": "xxxxxxxxxxxx",                 <-登录账号,account登录模式时必填
            "password": "xxxxxxxxxxxx",                 <-登录密码,account登录模式时必填
            "auto_send_dynamic": false,
            "dynamic_template": "转播开始了哦~",
            "forwardLink": "",
            "bilibili_areaid": "33",
            "youtubeChannelId": "xxxxxxxxxxx",
            "twitcast": ""
        }
    ]
}
```
### 如何运行
1.cd 到对应的目录，如果是按上面执行的话就是要先cd到AutoYtB文件夹
```
cd AutoYtB
```
2.运行以下命令
```
nohup python3.7 -u main.py > logfile.txt &
```

### 如何手动开播
访问地址：http://{服务器IP或域名}/web/restream.html

### TODO LIST
- [X] 环境自动安装脚本
- [X] 添加手动下播功能，只需要对应rtmp就可以了
- [ ] 订阅列表添加到config.json的可视化界面和接口吧
- [ ] twitcast 支持？
- [ ] openREC 支持？
- [ ] showroom 支持？
- [ ] Mirrativ 支持？
- [ ] 17live 支持？
- [ ] RELITIY 支持？？
- [ ] 使用microsoft flow 监控推特自动监控上面的其它平台？？
- [ ] account登录模式cookies过期自动重新登录
- [ ] 开播动态内容支持部分变量(如来源频道标题等)
