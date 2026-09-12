"""容器内 WSGI 入口模块。

仅负责暴露模块级 ``app`` 对象，供 Gunicorn 以 ``wsgi:app`` 方式加载。
该文件不承载任何业务逻辑，业务实现全部位于 ``src/vv_pet01`` 包内。

Typical usage example::

    gunicorn -c gunicorn.conf.py wsgi:app
"""

from __future__ import annotations

from vv_pet01 import create_app

#: WSGI 服务器加载的应用实例。
app = create_app()

if __name__ == "__main__":
    # 便于本地直接调试：python wsgi.py
    app.run(host="0.0.0.0", port=8000, debug=app.config.get("DEBUG", False))
