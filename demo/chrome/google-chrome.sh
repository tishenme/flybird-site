# 我需要在debian12 安装 chrome请提供下载地址 包括会用到的依赖 我是公司内网离线安装

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

root@192:~# dpkg -I google-chrome-stable_current_amd64.deb | grep "Depends"
 Pre-Depends: dpkg (>= 1.14.0)
 Depends: ca-certificates, fonts-liberation, libasound2 (>= 1.0.17), libatk-bridge2.0-0 (>= 2.5.3), libatk1.0-0 (>= 2.11.90), libatspi2.0-0 (>= 2.9.90), libc6 (>= 2.25), libcairo2 (>= 1.6.0), libcups2 (>= 1.6.0), libcurl3-gnutls | libcurl3-nss | libcurl4 | libcurl3, libdbus-1-3 (>= 1.9.14), libexpat1 (>= 2.1~beta3), libgbm1 (>= 17.1.0~rc2), libglib2.0-0 (>= 2.39.4), libgtk-3-0 (>= 3.9.10) | libgtk-4-1, libnspr4 (>= 2:4.9-2~), libnss3 (>= 2:3.35), libpango-1.0-0 (>= 1.14.0), libudev1 (>= 183), libvulkan1, libx11-6 (>= 2:1.4.99.1), libxcb1 (>= 1.9.2), libxcomposite1 (>= 1:0.4.4-1), libxdamage1 (>= 1:1.1), libxext6, libxfixes3, libxkbcommon0 (>= 0.5.0), libxrandr2, wget, xdg-utils (>= 1.0.2)

cd /root
rm -rf /root/chrome-offline
mkdir /root/chrome-offline
cp /root/google-chrome-stable_current_amd64.deb /root/chrome-offline/google-chrome-stable_current_amd64.deb
cd /root/chrome-offline
ls -alh

rm -rf /root/chrome-offline/google-chrome.sh
nano /root/chrome-offline/google-chrome.sh
cat -n /root/chrome-offline/google-chrome.sh

# 从这里开始
cat chrome-offline-debian12.tar.gz.part_* > chrome-offline-debian12.tar.gz
tar -zxvf chrome-offline-debian12.tar.gz
cd chrome-offline
apt install ./*.deb
apt --fix-broken install
