"""全站导航菜单数据定义。

将导航结构集中在此处维护，模板通过上下文处理器 ``site_nav`` 获取数据，
从而避免在 HTML 中硬编码链接，新增页面只需同步修改本文件与对应蓝图。

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
#: * ``label``: 菜单展示文案。
#: * ``endpoint``: 一级菜单指向的端点；下拉型菜单指向首个可用子页面。
#: * ``blueprint``: 所属蓝图名称，用于判定当前板块高亮。
#: * ``children``: 二级菜单列表，元素包含 ``label`` 与 ``endpoint``。
SITE_NAV: list[dict[str, Any]] = [
    {
        "label": "首页",
        "endpoint": "main.index",
        "blueprint": "main",
        "children": [],
    },
    {
        "label": "领养宠物",
        "endpoint": "adoption.dogs",
        "blueprint": "adoption",
        "children": [
            {"label": "领养狗狗", "endpoint": "adoption.dogs"},
            {"label": "领养猫咪", "endpoint": "adoption.cats"},
            {"label": "其他宠物", "endpoint": "adoption.others"},
            {"label": "领养流程", "endpoint": "adoption.process"},
        ],
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
        "endpoint": "charity.volunteer",
        "blueprint": "charity",
        "children": [
            {"label": "成为志愿者", "endpoint": "charity.volunteer"},
            {"label": "公益活动", "endpoint": "charity.activities"},
            {"label": "捐赠", "endpoint": "charity.donate"},
            {"label": "寄养宠物", "endpoint": "charity.foster"},
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
