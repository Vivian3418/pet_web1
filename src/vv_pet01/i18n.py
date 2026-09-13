"""国际化（i18n）基础设施模块。

采用「URL 语言前缀 + Flask-Babel」方案：所有页面路由都携带 ``<lang_code>``
路径段（如 ``/zh/adoption/dogs`` 与 ``/en/adoption/dogs``），语言状态因此可
被直接分享与收藏，也便于搜索引擎分别收录。

翻译目录位于 ``vv_pet01/translations/<lang>/LC_MESSAGES/messages.mo``。
受控词表（品种 / 性别 / 体型 / 状态 / 性格标签）以中文为 msgid，仅需维护
一份英文翻译目录。

Typical usage example::

    from vv_pet01.i18n import init_app

    init_app(app)
"""

from __future__ import annotations

from pathlib import Path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from flask import Flask, g, redirect, request, session, url_for
from flask_babel import Babel, get_locale

#: 支持的语言代码及其展示名称（展示名称本身不翻译，方便任何语言下辨认）。
LANGUAGES: dict[str, str] = {
    "zh": "中文",
    "en": "English",
}

#: 默认语言。
DEFAULT_LANGUAGE: str = "zh"

#: 翻译目录存放位置（相对包目录）。
TRANSLATIONS_DIR: Path = Path(__file__).with_name("translations")

#: 翻译域名称。
TRANSLATION_DOMAIN: str = "messages"

#: 保存用户上次所选语言的会话键。
_SESSION_KEY: str = "vv_pet01_lang"


def _compile_catalogs() -> None:
    """把缺失或过期的 ``.po`` 编译为 ``.mo``。

    仓库中只保留可读的 ``.po`` 文本目录；Docker 镜像构建时不额外执行
    ``pybabel compile``，因此这里在应用启动时按需编译，保证英文翻译始终生效。
    """
    if not TRANSLATIONS_DIR.is_dir():
        return

    for po_path in TRANSLATIONS_DIR.glob(f"*/LC_MESSAGES/*.po"):
        mo_path = po_path.with_suffix(".mo")
        if mo_path.exists() and mo_path.stat().st_mtime >= po_path.stat().st_mtime:
            continue
        try:
            with po_path.open("rb") as po_file:
                catalog = read_po(po_file)
            mo_path.parent.mkdir(parents=True, exist_ok=True)
            with mo_path.open("wb") as mo_file:
                write_mo(mo_file, catalog)
        except OSError:  # pragma: no cover - 只读文件系统等极端情况
            continue


def get_language() -> str:
    """获取当前请求语言代码。

    Returns:
        当前语言代码，如 ``"zh"`` 或 ``"en"``；不在请求上下文中或尚未确定时
        返回默认语言。
    """
    try:
        language = g.get("lang_code")
    except RuntimeError:  # 不在应用上下文中
        return DEFAULT_LANGUAGE
    return str(language) if language else DEFAULT_LANGUAGE


def init_app(app: Flask) -> None:
    """初始化国际化能力。

    依次完成：编译翻译目录、注册 Flask-Babel、注册语言前缀的 URL 处理钩子、
    ``/`` 与 ``/<lang_code>`` 入口跳转，以及语言切换所需的模板上下文。

    Args:
        app: 需要初始化国际化的 Flask 应用实例。
    """
    _compile_catalogs()

    app.config.setdefault("BABEL_DEFAULT_LOCALE", DEFAULT_LANGUAGE)
    app.config.setdefault("BABEL_TRANSLATION_DIRECTORIES", str(TRANSLATIONS_DIR))
    babel = Babel()

    def _select_locale() -> str:
        """选择当前请求使用的语言。

        Returns:
            语言代码。优先使用 URL 前缀，其次会话记录，再次浏览器偏好，
            最终回退到默认语言；无请求上下文（CLI、后台任务）时同样回退到
            默认语言。
        """
        try:
            lang_code = getattr(g, "lang_code", None)
            if lang_code:
                return lang_code
            stored = session.get(_SESSION_KEY)
            if stored in LANGUAGES:
                return stored
            best = request.accept_languages.best_match(list(LANGUAGES))
            return best or DEFAULT_LANGUAGE
        except RuntimeError:  # 无请求上下文
            return str(app.config.get("BABEL_DEFAULT_LOCALE", DEFAULT_LANGUAGE))

    babel.init_app(app, locale_selector=_select_locale)

    @app.url_defaults
    def _add_language_code(endpoint: str, values: dict) -> None:
        """为支持语言前缀的端点自动补上 ``lang_code`` 参数。

        Args:
            endpoint: 目标端点名称。
            values: ``url_for`` 收集到的参数，会被原地修改。
        """
        if "lang_code" in values:
            return
        if app.url_map.is_endpoint_expecting(endpoint, "lang_code"):
            values["lang_code"] = get_language()

    @app.url_value_preprocessor
    def _pull_language_code(endpoint: str | None, values: dict | None) -> None:
        """从 URL 中提取并移除 ``lang_code``，同时记录到请求上下文。

        Args:
            endpoint: 匹配到的端点名称。
            values: URL 变量字典，会被原地修改。
        """
        if values is None:
            values = {}
        lang_code = values.pop("lang_code", None)
        if lang_code in LANGUAGES:
            g.lang_code = lang_code
            session[_SESSION_KEY] = lang_code
        else:
            g.lang_code = session.get(_SESSION_KEY) or DEFAULT_LANGUAGE

    @app.route("/")
    def root_redirect():
        """把站点根路径重定向到当前语言的首页。"""
        language = session.get(_SESSION_KEY)
        if language not in LANGUAGES:
            language = request.accept_languages.best_match(list(LANGUAGES)) or DEFAULT_LANGUAGE
        return redirect(url_for("main.index", lang_code=language))

    @app.context_processor
    def _inject_language_context() -> dict[str, object]:
        """向模板注入语言相关的变量与切换地址生成函数。

        Returns:
            包含 ``languages``、``current_language``、``is_english`` 与
            ``switch_language_url`` 的上下文字典。
        """

        def switch_language_url(lang_code: str) -> str:
            """生成切换到指定语言的当前页面地址。

            Args:
                lang_code: 目标语言代码。

            Returns:
                保留当前路径变量与查询参数的完整 URL。
            """
            view_args = dict(request.view_args or {})
            view_args.pop("lang_code", None)
            view_args["lang_code"] = lang_code
            query_args = {
                key: value for key, value in request.args.items() if key != "lang_code"
            }
            try:
                return url_for(request.endpoint or "main.index", **view_args, **query_args)
            except Exception:  # pragma: no cover - 端点无法构造时退回首页
                return url_for("main.index", lang_code=lang_code)

        locale = get_locale()
        language = str(locale) if locale else DEFAULT_LANGUAGE
        return {
            "languages": LANGUAGES,
            "current_language": language,
            "is_english": language.startswith("en"),
            "switch_language_url": switch_language_url,
        }

    app.logger.debug("国际化已启用，翻译目录：%s", TRANSLATIONS_DIR)
