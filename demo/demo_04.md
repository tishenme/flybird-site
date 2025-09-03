### USER
在 redhat8 上用 systemd 启动 airflow 2.7.3 发现会向 /var/log/message 里面写文件 记录airflow的日志 怎么控制这个文件?

### ASSISTANT
在 Red Hat 8 上使用 `systemd` 启动 Airflow 2.7.3 时，发现日志被写入 `/var/log/messages`，这通常是因为 `systemd` 的 `journald` 将服务的标准输出（stdout/stderr）转发到了系统日志中。这是默认行为，但你可以通过配置来控制日志的输出位置和行为。

以下是解决和控制该问题的方法：

---

### ✅ 1. **理解问题来源**

当使用 `systemd` 启动服务时，如果服务没有明确重定向日志输出（例如通过 `StandardOutput` 或 `StandardError`），`systemd` 会将输出发送到 `journald`，然后由 `rsyslog` 或 `syslog` 服务将部分日志（尤其是 `info` 及以上级别）写入 `/var/log/messages`。

Airflow 默认会将日志输出到 **控制台（stdout/stderr）**，而 `systemd` 捕获这些输出并记录到系统日志中。

---

### ✅ 2. **解决方案：配置 systemd 服务文件**

你需要编辑 Airflow 的 `systemd` 服务文件（通常是 `/etc/systemd/system/airflow-*.service`），显式控制日志输出。

#### 示例：修改 `airflow-webserver.service`

```ini
[Unit]
Description=Airflow webserver
After=network.target

[Service]
EnvironmentFile=/etc/sysconfig/airflow
User=airflow
Group=airflow
Type=simple
ExecStart=/bin/airflow webserver
Restart=always
RestartSec=10

# === 关键：控制日志输出 ===
StandardOutput=journal
StandardError=journal
SyslogIdentifier=airflow-webserver

# 或者，如果你想完全禁用 stdout 输出到 syslog：
# StandardOutput=null
# StandardError=null

# 更推荐的方式：重定向到专用日志文件
# StandardOutput=file:/var/log/airflow/webserver.log
# StandardError=file:/var/log/airflow/webserver-error.log

[Install]
WantedBy=multi-user.target
```

> 🔹 `StandardOutput=journal`：输出到 journald（可通过 `journalctl -u airflow-webserver` 查看）
> 🔹 `StandardOutput=file:/path/to/log`：直接写入文件，**不会进入 `/var/log/messages`**
> 🔹 `StandardOutput=null`：丢弃输出（不推荐用于生产）

---

### ✅ 3. **推荐做法：使用文件输出 + logrotate**

#### 步骤：

1. 创建日志目录：

```bash
sudo mkdir -p /var/log/airflow
sudo chown airflow:airflow /var/log/airflow
```

2. 修改 `systemd` 服务文件，使用文件输出：

```ini
StandardOutput=file:/var/log/airflow/webserver.log
StandardError=file:/var/log/airflow/webserver-error.log
```

3. 配置 `logrotate` 管理日志轮转：

创建 `/etc/logrotate.d/airflow`：

```conf
/var/log/airflow/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    create 640 airflow airflow
}
```

---

### ✅ 4. **Airflow 自身日志配置**

除了 `systemd`，你还应配置 Airflow 自己的日志系统，避免 Airflow 任务日志也污染系统日志。

编辑 `airflow.cfg`：

```ini
[logging]
# 任务日志应写入文件系统，而不是 stdout
remote_logging = False
logging_level = INFO
dag_processor_manager_log_location = /var/log/airflow/dag_processor_manager.log
worker_log_server_port = 8793
base_log_folder = /var/log/airflow/jobs
```

确保这些目录存在并有权限：

```bash
sudo mkdir -p /var/log/airflow/jobs
sudo chown airflow:airflow /var/log/airflow/jobs
```

---

### ✅ 5. **验证和重载配置**

```bash
# 重载 systemd 配置
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

# 重启服务
sudo systemctl restart airflow-webserver
sudo systemctl restart airflow-scheduler

# 查看日志（journal）
journalctl -u airflow-webserver -f

# 或查看文件日志
tail -f /var/log/airflow/webserver.log
```

---

### ✅ 6. **防止日志进入 /var/log/messages**

确保 `rsyslog` 不转发 `journal` 中的 `airflow` 日志到 `/var/log/messages`。

检查 `/etc/rsyslog.conf` 或 `/etc/rsyslog.d/` 中是否有类似：

```conf
*.info;mail.none;authpriv.none;cron.none    /var/log/messages
```

如果你发现 Airflow 日志仍进入 `/var/log/messages`，是因为其日志级别为 `info`。你可以：

- 使用 `SyslogIdentifier=airflow-webserver` 在 systemd 中打标签
- 在 rsyslog 中过滤掉该标识：

创建 `/etc/rsyslog.d/airflow.conf`：

```conf
:syslog-identifier, isequal, "airflow-webserver" ~
:syslog-identifier, isequal, "airflow-scheduler" ~
```

> `~` 表示丢弃匹配的日志

然后重启 rsyslog：

```bash
sudo systemctl restart rsyslog
```

---

### ✅ 总结

| 目标 | 方法 |
|------|------|
| 停止日志写入 `/var/log/messages` | 使用 `StandardOutput=file:` 或 rsyslog 过滤 |
| 集中管理 Airflow 日志 | 写入 `/var/log/airflow/` 目录 |
| 避免日志膨胀 | 配置 `logrotate` |
| 调试方便 | 保留 `journalctl -u airflow-*` 查看 |

---

如果你提供你的 `.service` 文件内容，我可以帮你具体修改。
