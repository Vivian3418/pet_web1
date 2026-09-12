"""参与公益板块蓝图模块。

对应顶部导航「参与公益」下拉菜单，包含成为志愿者、公益活动、捐赠与
寄养宠物四个子页面，路由带 ``<lang_code>`` 语言前缀。
"""

from __future__ import annotations

from flask import Blueprint, render_template
from flask_babel import gettext as _

charity_bp = Blueprint("charity", __name__, url_prefix="/<lang_code>/charity")


@charity_bp.get("/volunteer")
def volunteer() -> str:
    """成为志愿者页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("成为志愿者"),
        page_desc=_("这里将介绍志愿者招募条件与报名方式。"),
    )


@charity_bp.get("/activities")
def activities() -> str:
    """公益活动页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("公益活动"),
        page_desc=_("这里将展示近期公益活动安排与往期回顾。"),
    )


@charity_bp.get("/donate")
def donate() -> str:
    """捐赠页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("捐赠"),
        page_desc=_("这里将说明捐赠用途、物资清单与捐赠渠道。"),
    )


@charity_bp.get("/foster")
def foster() -> str:
    """寄养宠物页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("寄养宠物"),
        page_desc=_("这里将介绍临时寄养家庭的申请与支持方案。"),
    )
