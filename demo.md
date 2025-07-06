# /opt/jupyterhub/custom_spawners/shared_spawner.py
from jupyterhub.spawner import LocalProcessSpawner
from tornado import gen
import os
import sys

# 使用单例模式管理共享进程
class SharedRootSpawner(LocalProcessSpawner):
    _shared_instance = None

    def __new__(cls, *args, **kwargs):
        # 单例模式实现
        if cls._shared_instance is None:
            cls._shared_instance = super().__new__(cls)
        return cls._shared_instance

    def __init__(self, *args, **kwargs):
        # 确保只初始化一次
        if not hasattr(self, '_initialized'):
            super().__init__(*args, **kwargs)
            self._initialized = True
            self.log.name = "SharedRootSpawner"
            self.log.info("Initializing SharedRootSpawner")

            # 所有用户使用root身份
            self.user.name = 'root'
            self.user.server.port = 8888  # 固定端口
            self._process = None
            self._url = None

    @gen.coroutine
    def start(self):
        self.log.info("Starting shared JupyterLab instance")

        # 如果共享进程未启动，则启动它
        if self._process is None:
            # 配置root环境
            self.cmd = [sys.executable, '-m', 'jupyter', 'lab']
            self.args = [
                '--ip=0.0.0.0',
                '--port=8888',
                '--no-browser',
                '--allow-root',
                f'--notebook-dir=/root'
            ]

            # 启动进程
            self._process = yield super().start()
            self._url = f"http://{self.host}:{self.port}"
            self.log.info(f"Shared JupyterLab started at {self._url}")

        # 直接返回共享实例信息
        return (self._url, self._process.pid)

    def poll(self):
        # 始终返回运行状态（None表示运行中）
        return None

    def stop(self, now=False):
        # 阻止停止共享实例
        self.log.info("Preventing stop of shared JupyterLab instance")
        pass

    @property
    def process(self):
        return self._process

    @property
    def url(self):
        return self._url
