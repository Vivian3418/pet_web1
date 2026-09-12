"""Gunicorn 运行配置。

本地与容器共用同一份配置，避免命令与配置文件产生漂移。
所有可调参数均支持通过环境变量覆盖，便于在不同部署环境中调整。

Typical usage example::

    gunicorn -c gunicorn.conf.py wsgi:app
"""

from __future__ import annotations

import multiprocessing
import os

#: 监听地址，容器内需绑定 0.0.0.0 才能被外部访问。
bind: str = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

#: 工作进程数，默认为 CPU 核心数的 2 倍加 1。
workers: int = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

#: 每个进程的线程数，纯模板渲染场景下可适当提升并发处理能力。
threads: int = int(os.environ.get("GUNICORN_THREADS", 2))

#: 工作模式，gthread 适配 IO 与并发请求。
worker_class: str = "gthread"

#: 请求超时时间（秒），超时后 worker 会被重启。
timeout: int = int(os.environ.get("GUNICORN_TIMEOUT", 60))

#: 优雅退出等待时间（秒）。
graceful_timeout: int = 30

#: 保持连接时间（秒）。
keepalive: int = 5

#: 在 master 进程预加载应用，节省内存并加快 worker 启动。
preload_app: bool = True

#: 临时目录：容器内使用内存盘提升性能，非 Linux 环境（如 macOS）回退为默认目录。
worker_tmp_dir: str | None = (
    os.environ.get("GUNICORN_WORKER_TMP_DIR")
    or ("/dev/shm" if os.path.isdir("/dev/shm") else None)
)

#: 日志输出到标准输出/标准错误，便于容器日志采集。
accesslog: str = "-"
errorlog: str = "-"
loglevel: str = os.environ.get("GUNICORN_LOG_LEVEL", "info")

#: 访问日志格式，附带请求耗时，便于排查性能问题。
access_log_format: str = '%(h)s "%(r)s" %(s)s %(b)s %(L)s秒 "%(a)s"'
