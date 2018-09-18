# AutoYtB
订阅youtuber, 有视频时自动转播到对应的b站账号

感谢autolive的参考 : https://github.com/7rikka/autoLive

## 软件依赖和环境安装
#### youtube-dl, ffmpeg, python3

youtube-dl安装
```
pip install youtube-dl
```

ffmpeg安装,因为各系统不同安装方法也不同这里只提供vultr centos7的安装方法
```
sudo yum install epel-release -y
sudo yum update -y
sudo yum install gcc openssl-devel bzip2-devel libffi libffi-devel
shutdown -r now

sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm
sudo yum -y install ffmpeg
```
python3安装,这里安装的是3.7独立安装，运行时调用的是python3.7而不是python3。
```
cd /usr/src
wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
tar xzf Python-3.7.0.tgz
cd Python-3.7.0
./configure --enable-optimizations
make altinstall
```

### 代码依赖库
```
pip install requests
```


## 运行前的配置
打开Config.json
```
{
    "serverIP": "XXXXX",      <-必需设置,用于pubsubhub的回调地址
    "serverPort": "80",       <-运行端口
    "subSecert": "",          <-会自动生成的sercert,用于pubsubhub的订阅校验，以后可能还可以用在别的地方
    "subscribeList": [
        {
            "bilibili_cookiesStr": "xxxxxxxxxxx",       <-输入访问B站时的requestHeader的cookies
            "forwardLink": "",                          <-还未有用
            "bilibili_areaid": "33",                    <-自动开播时的区域ID
            "youtubeChannelId": "UCWCc8tO-uUl_7SJXIKJACMw",     <-订阅的youtube channel_id
            "twitcast": "kaguramea"                     <-以后可能可以做到twitcast的监控？先写着吧
        },
        {
            "bilibili_cookiesStr": "xxxxxxxxxxxx",
            "forwardLink": "",
            "bilibili_areaid": "33",
            "youtubeChannelId": "xxxxxxxxxxx",
            "twitcast": ""
        }
    ]
}
```
### 如何运行
```
nohup python3.7 -u main.py > logfile.txt &
```

### 如何手动开播
访问地址：http://{服务器IP或域名}/web/restream.html

### TODO LIST
- [ ] 环境自动安装脚本
- [ ] 添加手动下播功能？需要使用sercert来做检验是否管理员？
- [ ] 订阅列表添加到config.json的可视化界面和接口吧
- [ ] twitcast 支持？
- [ ] openREC 支持？
- [ ] showroom 支持？
- [ ] Mirrativ 支持？
- [ ] 17live 支持？
- [ ] RELITIY 支持？？
- [ ] 使用microsoft flow 监控推特自动监控上面的其它平台？？
