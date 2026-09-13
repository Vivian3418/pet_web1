"""种子数据装配模块。

把 :mod:`vv_pet01.data.shelters` 与 :mod:`vv_pet01.data.pets` 中的
Python 字典转换为可直接写入 SQLite 的行数据，完成布尔值整数化与
多值字段 JSON 序列化等适配工作。

Typical usage example::

    from vv_pet01.data.seed import build_seed_rows

    shelter_rows, pet_rows = build_seed_rows()
"""

from __future__ import annotations

import json
from typing import Any

from vv_pet01.data.pets import PETS
from vv_pet01.data.shelters import SHELTERS


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


def _pet_row(pet: dict[str, Any]) -> dict[str, Any]:
    """把宠物字典转换为数据库行。

    Args:
        pet: 宠物种子字典。

    Returns:
        仅包含数据库列名的行字典，布尔值转为 0/1，
        性格标签与相处对象转为 JSON 字符串。
    """
    return {
        "id": int(pet["id"]),
        "species": pet["species"],
        "name": pet["name"],
        "name_en": pet["name_en"],
        "breed": pet["breed"],
        "gender": pet["gender"],
        "age_months": int(pet["age_months"]),
        "size": pet.get("size", ""),
        "weight_kg": float(pet["weight_kg"]),
        "shelter_id": pet["shelter_id"],
        "status": pet["status"],
        "vaccinated": int(bool(pet["vaccinated"])),
        "neutered": int(bool(pet["neutered"])),
        "traits": json.dumps(pet["traits"], ensure_ascii=False),
        "companions": json.dumps(pet["companions"], ensure_ascii=False),
        "description": pet["description"],
        "description_en": pet["description_en"],
        "image": pet["image"],
        "intake_date": pet["intake_date"],
    }


def build_seed_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """构造全部种子数据的数据库行。

    Returns:
        ``(救助站行列表, 宠物行列表)`` 二元组。
    """
    shelters = [_shelter_row(shelter) for shelter in SHELTERS]
    pets = [_pet_row(pet) for pet in PETS]
    return shelters, pets
