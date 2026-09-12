"""首页蓝图模块。

承载站点入口页面（``/<lang_code>/``），展示站点名称、公益主题标语、
领养流程与救助故事。
"""

from __future__ import annotations

from flask import Blueprint, render_template

from vv_pet01.services.adoption import list_stories

main_bp = Blueprint("main", __name__, url_prefix="/<lang_code>")

#: 首页「救助故事」区块展示的卡片数量。
STORIES_LIMIT: int = 8


@main_bp.get("/")
def index() -> str:
    """渲染站点首页。

    Returns:
        首页模板渲染后的 HTML 字符串。
    """
    return render_template("index.html", stories=list_stories(limit=STORIES_LIMIT))
