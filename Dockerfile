# vv_pet01 容器镜像构建文件
# 采用多阶段思路的极简实现：基于 slim 镜像安装依赖并以非 root 用户运行 Gunicorn。

FROM python:3.11-slim

# 容器内统一使用 UTF-8，避免中文输出乱码；关闭 Python 字节码缓存与输出缓冲
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANG=C.UTF-8 \
    FLASK_CONFIG=production \
    VV_PET01_DATABASE=/app/instance/vv_pet01.sqlite \
    PORT=8000

WORKDIR /app

# 先复制打包配置与源码，利用 Docker 层缓存加速依赖安装
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY wsgi.py gunicorn.conf.py ./

# 安装项目本体（含 Flask 与 Gunicorn 依赖）
RUN pip install --upgrade pip && pip install .

# 创建非 root 用户运行服务，降低容器逃逸风险
# instance 目录用于存放 SQLite 数据库文件，需预创建并归属运行用户以便持久化写入
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/instance \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 健康检查：确认首页可正常响应
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/').read()" || exit 1

# 使用 Gunicorn 作为生产 WSGI 服务器
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
