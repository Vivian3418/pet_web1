"""蓝图包初始化模块。

集中导入各业务板块的蓝图对象，并以 :data:`ALL_BLUEPRINTS` 列表对外暴露，
供应用工厂统一注册，避免在 ``create_app`` 中逐个 import 造成冗余。
"""

from __future__ import annotations

from flask import Blueprint

from vv_pet01.blueprints.adoption import adoption_bp
from vv_pet01.blueprints.charity import charity_bp
from vv_pet01.blueprints.main import main_bp
from vv_pet01.blueprints.protection import protection_bp

__all__ = [
    "ALL_BLUEPRINTS",
    "adoption_bp",
    "charity_bp",
    "main_bp",
    "protection_bp",
]

#: 需要被注册到应用实例的全部蓝图，注册顺序即为导航展示顺序。
ALL_BLUEPRINTS: list[Blueprint] = [
    main_bp,
    adoption_bp,
    protection_bp,
    charity_bp,
]
