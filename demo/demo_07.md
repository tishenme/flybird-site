### USER
我需要在debian12 安装 chrome请提供下载地址 包括会用到的依赖 我是公司内网离线安装

### ASSISTANT
在 Debian 12 上离线安装 Google Chrome（公司内网环境），你需要提前在有网络的机器上下载 Chrome 的 `.deb` 安装包以及所有依赖包，然后拷贝到内网机器安装。

以下是完整操作步骤：

---

## ✅ 一、下载 Google Chrome 安装包

官方下载地址（64位 Debian/Ubuntu）：

👉 https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

你可以用浏览器或 wget 下载：

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
```

---

## ✅ 二、在联网机器上解析并下载所有依赖包（关键步骤）

由于是离线安装，必须提前下载 Chrome 依赖的所有 `.deb` 包。

### 方法：使用 `apt-get download` + `dpkg -I` 解析依赖

#### 步骤 1：安装 `dpkg-dev`（如果未安装）

```bash
sudo apt update
sudo apt install dpkg-dev
```

#### 步骤 2：解析 Chrome 包的依赖

```bash
dpkg -I google-chrome-stable_current_amd64.deb | grep "Depends"
```

你会看到类似输出：

```
Depends: ca-certificates, fonts-liberation, libasound2 (>= 1.0.16), libatk-bridge2.0-0 (>= 2.5.3), libatk1.0-0 (>= 1.12.4), ...
```

#### 步骤 3：创建目录存放所有依赖包

```bash
mkdir chrome-offline
mv google-chrome-stable_current_amd64.deb chrome-offline/
cd chrome-offline
```

#### 步骤 4：使用 `apt-get download` 下载所有依赖（推荐用脚本自动处理）

创建脚本 `download_deps.sh`：

```bash
#!/bin/bash

DEB_FILE="google-chrome-stable_current_amd64.deb"

# 提取 Depends 字段
DEPENDS=$(dpkg -I "$DEB_FILE" | grep -A1 "^ Depends:" | tail -n1 | sed 's/^[ ,]*//;s/ *([^)]*)//g;s/, */ /g')

# 下载主包和所有依赖
apt-get download $DEPENDS

echo "✅ 所有依赖包已下载到当前目录"
```

赋予执行权限并运行：

```bash
chmod +x download_deps.sh
./download_deps.sh
```

> ⚠️ 注意：如果某些包已存在于系统缓存中（`/var/cache/apt/archives/`），`apt-get download` 仍会重新下载到当前目录。

---

## ✅ 三、打包所有文件，拷贝到内网机器

```bash
cd ..
tar -czvf chrome-offline-debian12.tar.gz chrome-offline/
```

将 `chrome-offline-debian12.tar.gz` 拷贝到内网机器（U盘、内网FTP、SCP等）。

---

## ✅ 四、在内网 Debian 12 机器上安装

### 步骤 1：解压

```bash
tar -xzvf chrome-offline-debian12.tar.gz
cd chrome-offline
```

### 步骤 2：安装所有依赖包（推荐使用 `apt install ./<包名>` 自动解决顺序）

```bash
sudo apt install ./*.deb
```

> ✅ `apt install ./*.deb` 会自动处理依赖顺序，比 `dpkg -i` 更可靠。

如果提示缺少某些依赖（极少数情况），可尝试：

```bash
sudo apt --fix-broken install
```

---

## ✅ 五、验证安装

```bash
google-chrome --version
```

或从应用菜单启动 Chrome。

---

## 📌 附：常见依赖包列表（Debian 12 amd64）

以下是 Chrome 通常依赖的包（截至 2024 年），供参考或手动补缺：

```
ca-certificates
fonts-liberation
libasound2
libatk-bridge2.0-0
libatk1.0-0
libatspi2.0-0
libc6
libcairo2
libcups2
libdbus-1-3
libdrm2
libexpat1
libgbm1
libgcc1
libgdk-pixbuf-2.0-0
libglib2.0-0
libgtk-3-0
libnspr4
libnss3
libpango-1.0-0
libx11-6
libxcb1
libxcomposite1
libxdamage1
libxext6
libxfixes3
libxrandr2
wget (非必须，但建议有)
```

> 💡 建议还是用脚本自动下载，避免手动遗漏。

---

## ✅ 六、（可选）设置 Chrome 为默认浏览器

```bash
sudo update-alternatives --config x-www-browser
```

选择 `/usr/bin/google-chrome-stable`

---

## ✅ 七、后续更新（离线）

每次 Chrome 更新，重复上述流程：下载新版 `.deb` → 解析依赖 → 下载依赖 → 拷贝 → 安装。

---

## 🚫 注意事项

- 确保内网机器架构是 `amd64`（x86_64），ARM 不适用。
- 不要混用 Ubuntu 和 Debian 的包，虽然大部分兼容，但可能有库版本差异。
- 如果内网机器完全无 `apt` 环境，需手动 `dpkg -i` 所有包（按依赖顺序），非常麻烦，强烈建议保留基础 `apt` 系统。

---

✅ 按以上步骤操作，即可在 Debian 12 内网离线环境下成功安装 Google Chrome。

如需我帮你生成完整依赖包列表或脚本，也可以提供 Chrome 版本号，我可以为你定制。
