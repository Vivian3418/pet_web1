"""vv_pet01 公益网站应用包。

本包采用 Flask 官方的应用工厂模式（Application Factory Pattern），
由 :func:`create_app` 负责创建并配置应用实例，避免定义全局单例 ``app``，
从而提升可测试性与可扩展性。

工厂按顺序装配：配置 → 日志 → 国际化 → 数据库 → CSRF → 蓝图 →
模板上下文 → 错误处理。国际化需要先于蓝图注册完成，因为 URL 语言前缀
由 :mod:`vv_pet01.i18n` 注册的钩子在生成链接时生效。
"""

from __future__ import annotations

import logging
import secrets

from flask import Flask, render_template
from flask_babel import gettext as _
from flask_wtf.csrf import CSRFProtect

from vv_pet01 import db, i18n
from vv_pet01.blueprints import ALL_BLUEPRINTS
from vv_pet01.config import get_config
from vv_pet01.navigation import BLUEPRINT_LABELS, SITE_NAV

__version__ = "0.2.0"

__all__ = ["create_app", "__version__"]

#: CSRF 保护扩展实例（Flask-WTF）。
csrf = CSRFProtect()


def create_app(config_name: str | None = None) -> Flask:
    """创建并配置 Flask 应用实例。

    Args:
        config_name: 配置名称，可选 ``development``、``testing``、
            ``production``、``default``。为 ``None`` 时由
            :func:`vv_pet01.config.get_config` 依据环境变量决定。

    Returns:
        已完成配置加载、扩展初始化、蓝图注册与错误页注册的 Flask 应用实例。

    Example:
        >>> app = create_app("testing")
        >>> app.testing
        True
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)

    _ensure_secret_key(app)
    _configure_logging(app)

    # 国际化必须先于蓝图注册：URL 语言前缀依赖 i18n 注册的钩子
    i18n.init_app(app)

    db.init_app(app)
    with app.app_context():
        # 首次启动自动建表并写入种子数据，保证演示站点开箱即用
        db.ensure_initialized()

    csrf.init_app(app)

    _register_blueprints(app)
    _register_context_processors(app)
    _register_error_handlers(app)

    app.logger.info(
        "应用 %s v%s 初始化完成（配置：%s，数据库：%s）",
        app.config.get("APP_NAME", "vv_pet01"),
        __version__,
        config_class.__name__,
        app.config.get("DATABASE"),
    )
    return app


def _ensure_secret_key(app: Flask) -> None:
    """确保存在可用的会话密钥。

    生产环境若未通过环境变量注入 ``SECRET_KEY``，则临时生成随机密钥并告警，
    保证会话与 CSRF 保护可用（多进程部署时应显式注入固定密钥）。

    Args:
        app: 需要检查密钥的 Flask 应用实例。
    """
    if app.config.get("SECRET_KEY"):
        return
    app.config["SECRET_KEY"] = secrets.token_hex(32)
    app.logger.warning(
        "未检测到 SECRET_KEY 环境变量，已生成临时随机密钥；"
        "生产环境请显式注入固定密钥，否则多进程间会话将不一致。"
    )


def _configure_logging(app: Flask) -> None:
    """统一日志配置，保证容器内日志输出到标准输出。

    Args:
        app: 需要配置日志的 Flask 应用实例。
    """
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    app.logger.setLevel(log_level)


def _register_blueprints(app: Flask) -> None:
    """注册全部业务蓝图。

    Args:
        app: 待注册蓝图的 Flask 应用实例。
    """
    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)


def _register_context_processors(app: Flask) -> None:
    """注册模板全局上下文，向所有模板注入导航与站点信息。

    导航文案与板块名称在请求上下文中通过 gettext 翻译，因此无需为
    ``navigation`` 模块维护两套数据。

    Args:
        app: 待注册上下文处理器的 Flask 应用实例。
    """

    @app.context_processor
    def inject_site_context() -> dict[str, object]:
        """向模板注入站点通用变量。

        Returns:
            包含导航菜单、站点名称、标语与板块标签的上下文字典。
        """
        nav = [
            {
                **item,
                "label": _(item["label"]),
                "children": [
                    {**child, "label": _(child["label"])} for child in item["children"]
                ],
            }
            for item in SITE_NAV
        ]
        return {
            "site_nav": nav,
            "blueprint_labels": {
                key: _(value) for key, value in BLUEPRINT_LABELS.items()
            },
            "site_name": app.config.get("APP_NAME", "vv_pet01"),
            "site_slogan": app.config.get("APP_SLOGAN", ""),
        }


def _register_error_handlers(app: Flask) -> None:
    """注册全局错误处理，统一渲染错误页面。

    Args:
        app: 待注册错误处理器的 Flask 应用实例。
    """

    @app.errorhandler(404)
    def page_not_found(error):  # noqa: ANN001, ANN202
        """渲染 404 页面未找到提示页。"""
        return (
            render_template(
                "page.html",
                page_title=_("页面未找到"),
                page_desc=_("您访问的页面不存在，请通过顶部导航返回。"),
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_server_error(error):  # noqa: ANN001, ANN202
        """渲染 500 服务端错误提示页。"""
        return (
            render_template(
                "page.html",
                page_title=_("服务暂时不可用"),
                page_desc=_("服务器开小差了，请稍后再试。"),
            ),
            500,
        )
