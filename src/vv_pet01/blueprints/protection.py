"""动物保护板块蓝图模块。

对应顶部导航「动物保护」下拉菜单，包含动物福利、反动物虐待与
灾害动物救助三个子页面，路由带 ``<lang_code>`` 语言前缀。
"""

from __future__ import annotations

from flask import Blueprint, render_template
from flask_babel import gettext as _

protection_bp = Blueprint(
    "protection", __name__, url_prefix="/<lang_code>/protection"
)


@protection_bp.get("/welfare")
def welfare() -> str:
    """动物福利页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("动物福利"),
        page_desc=_("这里将介绍动物福利五大自由与相关公益倡议。"),
    )


@protection_bp.get("/anti-cruelty")
def anti_cruelty() -> str:
    """反动物虐待页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("反动物虐待"),
        page_desc=_("这里将介绍反虐待动物知识科普与举报求助渠道。"),
    )


@protection_bp.get("/disaster-rescue")
def disaster_rescue() -> str:
    """灾害动物救助页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("灾害动物救助"),
        page_desc=_("这里将介绍自然灾害中的动物紧急救助行动。"),
    )
