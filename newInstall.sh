sudo yum install epel-release -y
sudo yum update -y

sudo yum -y install gcc openssl-devel bzip2-devel libffi libffi-devel
sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm
sudo yum -y install ffmpeg

sudo yum install -y wget
sudo yum install -y unzip

cd /usr/src
wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
tar xzf Python-3.7.0.tgz
cd Python-3.7.0
./configure --enable-optimizations
make altinstall

pip3.7 install --upgrade pip
pip3.7 install youtube-dl
pip3.7 install requests

cd ~
wget https://github.com/HalfMAI/AutoYtB/archive/master.zip
unzip master.zip
