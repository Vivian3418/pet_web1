"""全站导航菜单数据定义。

将导航结构集中在此处维护，模板通过上下文处理器 ``site_nav`` 获取数据，
从而避免在 HTML 中硬编码链接，新增页面只需同步修改本文件与对应蓝图。

合并领养界面后，「领养宠物」不再使用下拉菜单，而是直接指向统一的宠物
领养检索页；「领养流程」提升为一级菜单项。

Typical usage example::

    from vv_pet01.navigation import SITE_NAV

    for item in SITE_NAV:
        print(item["label"])
"""

from __future__ import annotations

from typing import Any

#: 顶部导航菜单结构。
#:
#: 每个一级菜单为字典，字段含义如下：
#:
#: * ``label``: 菜单展示文案（中文即 msgid，由上下文处理器翻译）。
#: * ``endpoint``: 菜单指向的端点。
#: * ``blueprint``: 所属蓝图名称。
#: * ``children``: 二级菜单列表，元素包含 ``label`` 与 ``endpoint``；
#:   为空表示该菜单为直达链接而非下拉菜单。
#: * ``active_endpoints``: 可选，除自身端点外还需保持高亮的端点
#:   （例如合并后的领养页需要在详情页与申请表页继续高亮）。
SITE_NAV: list[dict[str, Any]] = [
    {
        "label": "首页",
        "endpoint": "main.index",
        "blueprint": "main",
        "children": [],
    },
    {
        "label": "领养宠物",
        "endpoint": "adoption.pets",
        "blueprint": "adoption",
        "children": [],
        "active_endpoints": (
            "adoption.pets",
            "adoption.pet_detail",
            "adoption.apply",
            "adoption.applications",
            "adoption.application_detail",
        ),
    },
    {
        "label": "领养流程",
        "endpoint": "adoption.process",
        "blueprint": "adoption",
        "children": [],
    },
    {
        "label": "动物保护",
        "endpoint": "protection.welfare",
        "blueprint": "protection",
        "children": [
            {"label": "动物福利", "endpoint": "protection.welfare"},
            {"label": "反动物虐待", "endpoint": "protection.anti_cruelty"},
            {"label": "灾害动物救助", "endpoint": "protection.disaster_rescue"},
        ],
    },
    {
        "label": "参与公益",
        "endpoint": "charity.rescue",
        "blueprint": "charity",
        "children": [
            {"label": "动物救助", "endpoint": "charity.rescue"},
            {"label": "成为志愿者", "endpoint": "charity.volunteer"},
            {"label": "爱心捐款", "endpoint": "charity.donate"},
        ],
    },
]

#: 蓝图名称到中文板块名的映射，用于面包屑展示。
BLUEPRINT_LABELS: dict[str, str] = {
    "main": "首页",
    "adoption": "领养宠物",
    "protection": "动物保护",
    "charity": "参与公益",
}


def active_endpoints_of(item: dict[str, Any]) -> tuple[str, ...]:
    """计算某个菜单项需要高亮的端点集合。

    含子菜单的菜单项以全部子项端点为准；无子菜单的菜单项以自身端点
    加上可选的 ``active_endpoints`` 为准。

    Args:
        item: 导航菜单项。

    Returns:
        需要保持高亮的端点名称元组。
    """
    children = item.get("children") or []
    if children:
        return tuple(child["endpoint"] for child in children)
    return tuple(item.get("active_endpoints") or (item["endpoint"],))
