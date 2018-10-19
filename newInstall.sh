sudo yum install epel-release -y
sudo yum update -y

sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm

sudo yum install -y wget
sudo yum install -y unzip

wget https://raw.githubusercontent.com/Sporesirius/ffmpeg-install/master/ffmpeg-install
chmod a+x ffmpeg-install
./ffmpeg-install --install release
rm -f ffmpeg-install

curl https://intoli.com/install-google-chrome.sh | bash
wget -N https://chromedriver.storage.googleapis.com/2.42/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/bin/
rm -f chromedriver_linux64.zip

sudo yum install -y gcc openssl-devel bzip2-devel libffi libffi-devel sqlite-devel
cd /usr/src
wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
tar xzf Python-3.7.0.tgz
cd Python-3.7.0
./configure --enable-optimizations
make altinstall
rm -f /usr/src/Python-3.7.0.tgz

pip3.7 install --upgrade pip
pip3.7 install streamlink
pip3.7 install requests
pip3.7 install numpy
pip3.7 install selenium
pip3.7 install Pillow
pip3.7 install Crypto
pip3.7 install sqlalchemy
pip3.7 install apscheduler

firewall-cmd --zone=public --add-port=80/tcp --permanent
firewall-cmd --reload

cd ~
wget https://github.com/HalfMAI/AutoYtB/archive/master.zip
[ -f AutoYtB-master/config.json ] && unzip -o master.zip -x *.json || unzip -o master.zip
rm -f master.zip

shutdown -r now
