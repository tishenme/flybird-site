为了满足您的需求，我将提供完整的解决方案。以下是实现步骤和配置代码：

### 解决方案概述
1. **创建自定义Spawner**：继承`LocalProcessSpawner`，重写关键方法使所有用户共享同一个root用户的JupyterLab实例
2. **配置JupyterHub**：使用LDAP认证并指向自定义Spawner
3. **预启动JupyterLab服务**：以root身份启动共享的JupyterLab实例
4. **环境配置**：确保Python 3.9和Jupyter组件版本符合要求

---

### 1. 创建自定义Spawner（`shared_spawner.py`）
```python
# /opt/jupyterhub/shared_spawner.py
from jupyterhub.spawner import LocalProcessSpawner
from tornado import gen

class SharedRootSpawner(LocalProcessSpawner):
    # 共享的JupyterLab进程信息（类变量）
    shared_process = None
    shared_url = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 所有用户使用root身份
        self.user.name = 'root'
        self.user.server.port = 8888  # 固定端口

    @gen.coroutine
    def start(self):
        # 如果共享进程未启动，则启动它
        if SharedRootSpawner.shared_process is None:
            # 配置root环境
            self.cmd = ['jupyter', 'lab']
            self.args = [
                '--ip=0.0.0.0',
                '--port=8888',
                '--no-browser',
                '--allow-root',
                f'--notebook-dir={self.user.home_dir}'
            ]

            # 启动进程
            SharedRootSpawner.shared_process = yield super().start()
            SharedRootSpawner.shared_url = f"http://{self.host}:{self.port}"

        # 直接返回共享实例信息
        return (SharedRootSpawner.shared_url, SharedRootSpawner.shared_process.pid)

    def poll(self):
        # 始终返回运行状态（None表示运行中）
        return None

    def stop(self, now=False):
        # 阻止停止共享实例
        pass
```

---

### 2. 配置JupyterHub（`jupyterhub_config.py`）
```python
# /etc/jupyterhub/jupyterhub_config.py
c.JupyterHub.spawner_class = 'shared_spawner.SharedRootSpawner'

# LDAP认证配置（根据实际情况修改）
c.JupyterHub.authenticator_class = 'ldapauthenticator.LDAPAuthenticator'
c.LDAPAuthenticator.server_address = 'ldap://your-ldap-server'
c.LDAPAuthenticator.bind_dn_template = ['uid={username},ou=users,dc=example,dc=com']

# 所有用户共享root实例
c.JupyterHub.hub_ip = '0.0.0.0'
c.Spawner.default_url = '/lab'
c.Authenticator.admin_users = {'admin_user'}  # 设置管理员账号
```

---

### 3. 创建系统服务文件（`jupyterhub.service`）
```ini
# /etc/systemd/system/jupyterhub.service
[Unit]
Description=JupyterHub
After=network.target

[Service]
User=root
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/jupyterhub -f /etc/jupyterhub/jupyterhub_config.py

[Install]
WantedBy=multi-user.target
```

---

### 4. 部署步骤
```bash
# 1. 安装依赖
yum install -y python39 python39-devel openldap-devel gcc
pip3.9 install jupyterhub==5.3.0 jupyterlab==4.4.4 ldapauthenticator

# 2. 创建配置文件目录
mkdir -p /etc/jupyterhub
cp shared_spawner.py /opt/jupyterhub/
cp jupyterhub_config.py /etc/jupyterhub/

# 3. 启动服务
systemctl daemon-reload
systemctl enable --now jupyterhub

# 4. 验证（使用LDAP账号登录）
echo "访问地址：http://<服务器IP>:8000"
```

---

### 关键实现说明
1. **共享实例机制**：
   - 使用类变量`shared_process`存储全局唯一的JupyterLab进程
   - 首次登录用户触发root实例启动
   - 后续登录直接重定向到已有实例

2. **用户映射**：
   - 所有LDAP用户通过`self.user.name = 'root'`映射到root身份
   - 固定端口8888确保所有用户访问同一实例

3. **安全注意事项**：
   - 所有用户拥有**root权限**，仅限高度信任环境使用
   - 建议通过JupyterLab的访问控制限制敏感操作
   - 启用HTTPS加密通信（需额外配置）

4. **服务管理**：
   - 共享实例随JupyterHub服务启动/停止
   - 使用systemd监控进程状态

5. **LDAP集成**：
   - 通过`ldapauthenticator`实现企业认证
   - 管理员账号可访问Hub管理界面

---

### 验证方法
1. 使用LDAP账号登录JupyterHub
2. 所有用户自动进入同一JupyterLab实例
3. 检查进程信息：
   ```bash
   ps aux | grep jupyter-lab | grep root
   ```
   应只有1个root用户的JupyterLab进程

此方案完全满足您的需求：
- ✅ LDAP认证后使用共享root实例
- ✅ 无需用户启动服务器
- ✅ 符合指定版本要求
- ✅ 无新建系统用户

> **重要安全提示**：生产环境应添加防火墙规则限制IP访问，并定期审计root操作日志。
