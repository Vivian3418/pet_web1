"""种子数据装配模块。

把 :mod:`vv_pet01.data.shelters` 与 :mod:`vv_pet01.data.dogs` 中的
Python 字典转换为可直接写入 SQLite 的行数据，完成布尔值整数化与
多值字段 JSON 序列化等适配工作。

Typical usage example::

    from vv_pet01.data.seed import build_seed_rows

    shelter_rows, dog_rows = build_seed_rows()
"""

from __future__ import annotations

import json
from typing import Any

from vv_pet01.data.dogs import DOGS
from vv_pet01.data.shelters import SHELTERS

#: 首页「救助故事」合影图片地址模板。
#:
#: 采用关键词图片服务提供「人 + 宠物」合照；URL 末尾的 ``/all`` 表示必须
#: 同时匹配全部标签（而非匹配任意一个），以确保图片里既有狗狗也有人。
#: ``lock`` 参数使同一只狗狗始终得到稳定的同一张照片。
STORY_IMAGE_TEMPLATE: str = "https://loremflickr.com/640/440/{tags}/all?lock={lock}"

#: 合影关键词轮换表，避免相邻故事卡片出现雷同构图。
STORY_IMAGE_TAGS: tuple[str, ...] = (
    "dog,woman",
    "dog,man",
    "dog,person",
    "dog,owner",
    "dog,child",
    "dog,couple",
    "dog,boy",
    "dog,girl",
)


def story_image_url(dog_id: int) -> str:
    """生成某只狗狗对应的「救助人 / 领养人与宠物合照」地址。

    Args:
        dog_id: 狗狗编号，用于选择关键词与锁定具体照片。

    Returns:
        可直接用于 ``<img src>`` 的图片地址。
    """
    tags = STORY_IMAGE_TAGS[(dog_id - 1) % len(STORY_IMAGE_TAGS)]
    return STORY_IMAGE_TEMPLATE.format(tags=tags, lock=dog_id)


def _shelter_row(shelter: dict[str, Any]) -> dict[str, Any]:
    """把救助站字典转换为数据库行。

    Args:
        shelter: 救助站种子字典。

    Returns:
        仅包含数据库列名的行字典。
    """
    return {
        "id": shelter["id"],
        "name": shelter["name"],
        "name_en": shelter["name_en"],
        "city": shelter["city"],
        "district": shelter["district"],
        "address": shelter["address"],
        "address_en": shelter["address_en"],
        "phone": shelter["phone"],
        "lat": float(shelter["lat"]),
        "lng": float(shelter["lng"]),
        "founded_year": int(shelter["founded_year"]),
        "description": shelter["description"],
        "description_en": shelter["description_en"],
    }


def _dog_row(dog: dict[str, Any]) -> dict[str, Any]:
    """把狗狗字典转换为数据库行。

    Args:
        dog: 狗狗种子字典。

    Returns:
        仅包含数据库列名的行字典，布尔值转为 0/1，性格标签转为 JSON 字符串。
    """
    return {
        "id": int(dog["id"]),
        "name": dog["name"],
        "name_en": dog["name_en"],
        "breed": dog["breed"],
        "gender": dog["gender"],
        "age_months": int(dog["age_months"]),
        "size": dog["size"],
        "weight_kg": float(dog["weight_kg"]),
        "shelter_id": dog["shelter_id"],
        "status": dog["status"],
        "vaccinated": int(bool(dog["vaccinated"])),
        "neutered": int(bool(dog["neutered"])),
        "traits": json.dumps(dog["traits"], ensure_ascii=False),
        "description": dog["description"],
        "description_en": dog["description_en"],
        "image": dog["image"],
        "story_image": story_image_url(int(dog["id"])),
        "intake_date": dog["intake_date"],
    }


def build_seed_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """构造全部种子数据的数据库行。

    Returns:
        ``(救助站行列表, 狗狗行列表)`` 二元组。
    """
    shelters = [_shelter_row(shelter) for shelter in SHELTERS]
    dogs = [_dog_row(dog) for dog in DOGS]
    return shelters, dogs
