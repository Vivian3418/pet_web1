"""应用配置模块。

集中定义不同运行环境下的 Flask 配置类，避免配置散落在业务代码中。
通过环境变量 ``FLASK_CONFIG`` 选择具体配置，默认使用 ``development``。

Typical usage example::

    from vv_pet01.config import get_config

    config_class = get_config("production")
"""

from __future__ import annotations

import os

#: 应用展示名称，供模板与日志统一引用。
APP_NAME: str = "vv_pet01"

#: 站点标语，用于首页与页脚展示。
APP_SLOGAN: str = "让每一个生命都被温柔以待"


class BaseConfig:
    """基础配置类，存放所有环境共用的配置项。

    Attributes:
        SECRET_KEY: 用于会话签名与 CSRF 保护的密钥，优先从环境变量读取。
        APP_NAME: 应用展示名称。
        APP_SLOGAN: 站点标语。
        JSON_AS_ASCII: 关闭 JSON 的 ASCII 转义，保证中文正常输出。
        TEMPLATES_AUTO_RELOAD: 是否在模板变更时自动重载。
        STATIC_CACHE_MAX_AGE: 静态资源缓存时长（秒）。
    """

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "vv-pet01-dev-secret-key")
    APP_NAME: str = APP_NAME
    APP_SLOGAN: str = APP_SLOGAN

    JSON_AS_ASCII: bool = False
    TEMPLATES_AUTO_RELOAD: bool = False
    STATIC_CACHE_MAX_AGE: int = 60 * 60 * 24
    SEND_FILE_MAX_AGE_DEFAULT: int | None = None

    # SQLite 数据库文件路径；留空时由 vv_pet01.db 解析到 Flask 实例目录
    DATABASE: str | None = os.environ.get("VV_PET01_DATABASE")

    # 国际化
    BABEL_DEFAULT_LOCALE: str = os.environ.get("VV_PET01_LANG", "zh")

    # 表单
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int | None = 60 * 60 * 4

    # 上传限制：单次请求体上限，与动物救助照片大小上限保持一致（5 MB）
    MAX_CONTENT_LENGTH: int = 5 * 1024 * 1024

    @staticmethod
    def init_app(app) -> None:
        """将配置应用到 Flask 应用实例的扩展点。

        Args:
            app: 需要初始化的 Flask 应用实例。
        """
        # 占位钩子：后续可在此处初始化数据库、缓存等扩展。
        return None


class DevelopmentConfig(BaseConfig):
    """开发环境配置。

    Attributes:
        DEBUG: 打开调试模式，便于本地开发时排查问题。
        TEMPLATES_AUTO_RELOAD: 开发环境开启模板热重载。
    """

    DEBUG: bool = True
    TEMPLATES_AUTO_RELOAD: bool = True


class TestingConfig(BaseConfig):
    """测试环境配置。

    Attributes:
        TESTING: 打开测试模式，异常会直接抛出以便断言。
        SECRET_KEY: 测试环境使用固定密钥，保证结果可复现。
        WTF_CSRF_ENABLED: 测试环境关闭 CSRF，便于直接构造请求。
    """

    TESTING: bool = True
    SECRET_KEY: str = "vv-pet01-test-secret-key"
    WTF_CSRF_ENABLED: bool = False


class ProductionConfig(BaseConfig):
    """生产环境配置。

    Attributes:
        DEBUG: 生产环境必须关闭调试模式。
        SECRET_KEY: 生产环境强制从环境变量注入密钥。
        STATIC_CACHE_MAX_AGE: 生产环境延长静态资源缓存时间。
    """

    DEBUG: bool = False
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    STATIC_CACHE_MAX_AGE: int = 60 * 60 * 24 * 30


#: 配置名称到配置类的映射表。
_CONFIG_MAPPING: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str | None = None) -> type[BaseConfig]:
    """根据名称获取配置类。

    Args:
        config_name: 配置名称，可选 ``development``、``testing``、
            ``production``、``default``。为 ``None`` 时读取环境变量
            ``FLASK_CONFIG``，仍为空则回退到 ``default``。

    Returns:
        与名称对应的配置类；名称无法识别时返回默认配置类。
    """
    resolved_name = config_name or os.environ.get("FLASK_CONFIG") or "default"
    return _CONFIG_MAPPING.get(resolved_name.lower(), _CONFIG_MAPPING["default"])
