"""领养业务服务模块。

集中实现宠物检索、附近救助站计算、分页与领养申请持久化等逻辑，
使蓝图只负责解析请求参数与渲染模板，模板只负责展示。

检索模型（合并狗 / 猫 / 其他宠物后的界面）：

1. **参考点**：优先使用用户定位（``origin``），否则回退到所选城市的中心坐标。
2. **搜索距离**：以参考点为圆心过滤救助站，仅保留半径内的救助站所辖宠物。
3. **宠物类别**：决定可选的品种集合，以及是否展示「体型」筛选。
4. **相处对象**：多选，命中任意一项即匹配。

受控词表字段（类别 / 品种 / 性别 / 体型 / 状态 / 性格标签 / 相处对象）
以中文为规范值存取，展示时由模板通过 gettext 翻译；自由文本字段则按当前
请求语言挑选 ``xxx`` 或 ``xxx_en`` 列。

Typical usage example::

    from vv_pet01.services.adoption import search_pets

    results = search_pets(species="猫", reference=(31.23, 121.47), radius=25)
"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from typing import Any, Sequence

from flask import current_app
from flask_babel import get_locale
from flask_babel import gettext as _

from vv_pet01.data.cities import city_center
from vv_pet01.data.stories import story_image
from vv_pet01.data.taxonomy import (
    AGE_GROUP_OPTIONS,
    COMPANION_OPTIONS,
    GENDER_OPTIONS,
    RADIUS_OPTIONS,
    SIZE_OPTIONS,
    SPECIES_OPTIONS,
    STATUS_ADOPTABLE,
    STATUS_SLUGS,
    age_group_range,
    breeds_for,
    shows_size,
)
from vv_pet01.db import get_db

#: 每页展示的宠物数量。
DEFAULT_PER_PAGE: int = 9

#: 地球平均半径（千米），用于 Haversine 距离计算。
_EARTH_RADIUS_KM: float = 6371.0088

#: 排序方式到展示文案（msgid）的映射。
_SORT_LABELS: dict[str, str] = {
    "distance": "距离最近",
    "latest": "最新发布",
    "age_asc": "年龄从小到大",
    "name": "名字排序",
}

#: 领养申请状态到展示文案（msgid）的映射。
APPLICATION_STATUS_LABELS: dict[str, str] = {
    "submitted": "已提交",
    "reviewing": "审核中",
    "approved": "已通过",
}

#: 检索条件键集合，供 :func:`list_shelters` 复用与裁剪。
FILTER_KEYS: tuple[str, ...] = (
    "species",
    "keyword",
    "breed",
    "gender",
    "size",
    "age_group",
    "companions",
    "status",
)


# --------------------------------------------------------------------------- #
# 语言与字段本地化
# --------------------------------------------------------------------------- #


def current_language() -> str:
    """获取当前请求语言代码。

    Returns:
        ``"zh"`` 或 ``"en"``；不在请求上下文中时回退为默认语言。
    """
    try:
        return str(get_locale() or "zh")
    except RuntimeError:
        return str(current_app.config.get("BABEL_DEFAULT_LOCALE", "zh"))


def _is_english(language: str | None = None) -> bool:
    """判断给定或当前语言是否为英文。

    Args:
        language: 语言代码；为 ``None`` 时使用当前请求语言。

    Returns:
        语言以 ``en`` 开头时返回 ``True``。
    """
    return (language or current_language()).lower().startswith("en")


def pick_localized(row: dict[str, Any], base: str, language: str | None = None) -> str:
    """按语言挑选自由文本字段。

    Args:
        row: 数据库行转换而来的字典。
        base: 中文字段名，英文字段名为 ``f"{base}_en"``。
        language: 语言代码；为 ``None`` 时使用当前请求语言。

    Returns:
        对应语言的文本；英文缺失时回退为中文内容。
    """
    if _is_english(language):
        return row.get(f"{base}_en") or row.get(base) or ""
    return row.get(base) or row.get(f"{base}_en") or ""


# --------------------------------------------------------------------------- #
# 距离与格式化
# --------------------------------------------------------------------------- #


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """计算两个经纬度坐标之间的球面直线距离。

    Args:
        lat1: 起点纬度。
        lng1: 起点经度。
        lat2: 终点纬度。
        lng2: 终点经度。

    Returns:
        两点之间的球面距离，单位为千米，保留一位小数。
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    distance = 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))
    return round(distance, 1)


def resolve_reference(
    city: str, origin: tuple[float, float] | None = None
) -> tuple[float, float] | None:
    """解析「附近」计算的参考点。

    Args:
        city: 用户选择的所在地（城市名称）。
        origin: 浏览器定位得到的 ``(纬度, 经度)``，优先级高于城市中心。

    Returns:
        参考点坐标；既无定位也未选择已收录城市时返回 ``None``。
    """
    if origin is not None:
        return origin
    center = city_center(city) if city else None
    if center is None:
        return None
    return center.lat, center.lng


def format_age(age_months: int) -> str:
    """将月龄格式化为易读的年龄文案。

    Args:
        age_months: 月龄。

    Returns:
        中文环境下形如 ``"8 个月"``、``"1 岁 2 个月"``；
        英文环境下形如 ``"8 months"``、``"1 yr 2 mo"``。
    """
    if age_months < 12:
        return _("%(n)s 个月") % {"n": age_months}

    years, months = divmod(age_months, 12)
    if months == 0:
        return _("%(y)s 岁") % {"y": years}
    return _("%(y)s 岁 %(m)s 个月") % {"y": years, "m": months}


# --------------------------------------------------------------------------- #
# 查询构造
# --------------------------------------------------------------------------- #

#: 宠物查询语句：联表取出救助站信息，避免 N+1 查询。
_PET_SELECT = """
    SELECT
        p.id, p.species, p.name, p.name_en, p.breed, p.gender, p.age_months,
        p.size, p.weight_kg, p.shelter_id, p.status, p.vaccinated, p.neutered,
        p.traits, p.companions, p.description, p.description_en, p.image,
        p.intake_date,
        s.name AS shelter_name, s.name_en AS shelter_name_en,
        s.city AS city, s.district AS district,
        s.address AS shelter_address, s.address_en AS shelter_address_en,
        s.phone AS shelter_phone, s.lat AS shelter_lat, s.lng AS shelter_lng,
        s.founded_year AS shelter_founded_year,
        s.description AS shelter_description,
        s.description_en AS shelter_description_en
    FROM pets p
    JOIN shelters s ON s.id = p.shelter_id
"""


def _build_filters(
    *,
    species: str = "",
    keyword: str = "",
    breed: str = "",
    gender: str = "",
    size: str = "",
    age_group: str = "",
    companions: Sequence[str] | None = None,
    shelter_ids: Sequence[str] | None = None,
    status: str = STATUS_ADOPTABLE,
) -> tuple[str, list[Any]]:
    """根据检索条件构造 SQL WHERE 子句与参数列表。

    品类联动在此处兜底：当所选品种不属于当前类别时忽略该条件，
    体型筛选也仅在狗类别下生效。

    Args:
        species: 宠物类别；空字符串表示不限。
        keyword: 关键词，匹配多个文本字段。
        breed: 品种精确匹配。
        gender: 性别精确匹配。
        size: 体型精确匹配（仅狗类别生效）。
        age_group: 年龄段查询值。
        companions: 相处对象多选，命中任意一项即匹配。
        shelter_ids: 允许的救助站编号集合（由搜索距离计算得出）。
        status: 领养状态；空字符串表示不限制。

    Returns:
        ``(where_sql, params)`` 二元组，``where_sql`` 以 ``WHERE`` 开头；
        无任何条件时返回 ``("", [])``。
    """
    clauses: list[str] = []
    params: list[Any] = []

    if status:
        clauses.append("p.status = ?")
        params.append(status)
    if species:
        clauses.append("p.species = ?")
        params.append(species)
    if breed and breed in breeds_for(species):
        clauses.append("p.breed = ?")
        params.append(breed)
    if gender:
        clauses.append("p.gender = ?")
        params.append(gender)
    if size and shows_size(species):
        clauses.append("p.size = ?")
        params.append(size)

    age_range = age_group_range(age_group)
    if age_range is not None:
        min_months, max_months = age_range
        clauses.append("p.age_months >= ?")
        params.append(min_months)
        if max_months is not None:
            clauses.append("p.age_months < ?")
            params.append(max_months)

    for companion in companions or ():
        if companion in COMPANION_OPTIONS:
            # companions 以 JSON 数组字符串存储，用带引号的模糊匹配精确命中某一项
            clauses.append("p.companions LIKE ?")
            params.append(f'%"{companion}"%')

    if shelter_ids is not None:
        if not shelter_ids:
            # 半径内没有任何救助站：构造恒假条件，明确返回空结果
            clauses.append("1 = 0")
        else:
            placeholders = ", ".join("?" for _ in shelter_ids)
            clauses.append(f"p.shelter_id IN ({placeholders})")
            params.extend(shelter_ids)

    if keyword:
        pattern = f"%{keyword}%"
        clauses.append(
            "("
            "p.name LIKE ? OR p.name_en LIKE ? OR p.breed LIKE ? OR p.traits LIKE ? "
            "OR p.description LIKE ? OR p.description_en LIKE ? "
            "OR s.name LIKE ? OR s.name_en LIKE ? OR s.city LIKE ? OR s.district LIKE ?"
            ")"
        )
        params.extend([pattern] * 10)

    if not clauses:
        return "", []
    return "WHERE " + " AND ".join(clauses), params


def _load_json_list(raw: Any) -> list[str]:
    """把数据库中的 JSON 数组字符串解析为列表。

    Args:
        raw: 原始字段值。

    Returns:
        解析后的字符串列表；解析失败时返回空列表。
    """
    try:
        value = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    return value if isinstance(value, list) else []


def _decorate_pet(
    row: sqlite3.Row | dict[str, Any],
    reference: tuple[float, float] | None,
    language: str | None = None,
) -> dict[str, Any]:
    """把数据库行转换为模板可直接使用的宠物字典。

    Args:
        row: 联表查询返回的原始行。
        reference: 参考点坐标 ``(纬度, 经度)``；为 ``None`` 时不计算距离。
        language: 语言代码；为 ``None`` 时使用当前请求语言。

    Returns:
        含本地化文本、救助站子字典、``age_text``、``status_slug``、``companions``
        与 ``distance_km`` 的字典。
    """
    data = dict(row)

    shelter = {
        "id": data["shelter_id"],
        "name": pick_localized(data, "shelter_name", language),
        "city": data["city"],
        "district": data["district"],
        "address": pick_localized(data, "shelter_address", language),
        "phone": data["shelter_phone"],
        "lat": data["shelter_lat"],
        "lng": data["shelter_lng"],
        "founded_year": data["shelter_founded_year"],
        "description": pick_localized(data, "shelter_description", language),
    }

    distance_km: float | None = None
    if reference is not None:
        distance_km = haversine_km(
            reference[0], reference[1], data["shelter_lat"], data["shelter_lng"]
        )

    return {
        "id": data["id"],
        "species": data["species"],
        "name": pick_localized(data, "name", language),
        "name_zh": data["name"],
        "name_en": data["name_en"],
        "breed": data["breed"],
        "gender": data["gender"],
        "age_months": data["age_months"],
        "size": data["size"],
        "weight_kg": data["weight_kg"],
        "status": data["status"],
        "status_slug": STATUS_SLUGS.get(data["status"], "available"),
        "vaccinated": bool(data["vaccinated"]),
        "neutered": bool(data["neutered"]),
        "traits": _load_json_list(data.get("traits")),
        "companions": _load_json_list(data.get("companions")),
        "description": pick_localized(data, "description", language),
        "image": data["image"],
        "intake_date": data["intake_date"],
        "age_text": format_age(data["age_months"]),
        "shelter": shelter,
        "city": data["city"],
        "distance_km": distance_km,
    }


def _sort_pets(
    pets: list[dict[str, Any]],
    sort: str,
    reference: tuple[float, float] | None,
    language: str | None = None,
) -> list[dict[str, Any]]:
    """对宠物列表排序。

    Args:
        pets: 已完成字段补充的宠物列表。
        sort: 排序方式，见 :func:`search_pets`。
        reference: 参考点坐标，仅 ``distance`` 排序需要。
        language: 语言代码，用于「名字排序」选择排序键。

    Returns:
        排序后的宠物列表；距离排序在缺少参考点时回退为最新发布。
    """
    if sort == "distance" and reference is not None:
        return sorted(pets, key=lambda p: (p["distance_km"] is None, p["distance_km"] or 0.0))
    if sort == "age_asc":
        return sorted(pets, key=lambda p: p["age_months"])
    if sort == "name":
        key = "name_en" if _is_english(language) else "name_zh"
        return sorted(pets, key=lambda p: p[key].lower())
    return sorted(pets, key=lambda p: p["intake_date"], reverse=True)


def search_pets(
    *,
    species: str = "",
    keyword: str = "",
    breed: str = "",
    gender: str = "",
    size: str = "",
    age_group: str = "",
    companions: Sequence[str] | None = None,
    shelter_ids: Sequence[str] | None = None,
    status: str = STATUS_ADOPTABLE,
    reference: tuple[float, float] | None = None,
    sort: str = "",
) -> list[dict[str, Any]]:
    """按条件检索待领养宠物。

    检索条件之间为「与」关系；``shelter_ids`` 通常由
    :func:`nearby_shelter_ids` 依据参考点与搜索距离计算得到。

    Args:
        species: 宠物类别。
        keyword: 关键词，匹配呼名、品种、性格、简介与救助站信息。
        breed: 品种精确匹配（与类别联动，不匹配时自动忽略）。
        gender: 性别精确匹配。
        size: 体型精确匹配（仅狗类别生效）。
        age_group: 年龄段查询值。
        companions: 相处对象多选。
        shelter_ids: 允许的救助站编号集合；``None`` 表示不限。
        status: 领养状态；空字符串表示不限制。
        reference: 参考点坐标，用于计算并展示距离。
        sort: 排序方式，可选 ``distance``、``latest``、``age_asc``、``name``；
            留空时，有参考点则按距离、无参考点则按最新发布。

    Returns:
        匹配并已补充派生字段的宠物列表。
    """
    where_sql, params = _build_filters(
        species=species,
        keyword=keyword,
        breed=breed,
        gender=gender,
        size=size,
        age_group=age_group,
        companions=companions,
        shelter_ids=shelter_ids,
        status=status,
    )

    rows = get_db().execute(f"{_PET_SELECT} {where_sql}", params).fetchall()
    language = current_language()
    pets = [_decorate_pet(row, reference, language) for row in rows]

    resolved_sort = sort or ("distance" if reference is not None else "latest")
    return _sort_pets(pets, resolved_sort, reference, language)


def count_pets(
    *,
    species: str = "",
    keyword: str = "",
    breed: str = "",
    gender: str = "",
    size: str = "",
    age_group: str = "",
    companions: Sequence[str] | None = None,
    shelter_ids: Sequence[str] | None = None,
    status: str = STATUS_ADOPTABLE,
) -> int:
    """统计符合检索条件的宠物数量。

    Args:
        各参数含义同 :func:`search_pets`，其中 ``reference`` 与 ``sort`` 不参与统计。

    Returns:
        符合条件的记录条数。
    """
    where_sql, params = _build_filters(
        species=species,
        keyword=keyword,
        breed=breed,
        gender=gender,
        size=size,
        age_group=age_group,
        companions=companions,
        shelter_ids=shelter_ids,
        status=status,
    )
    sql = (
        "SELECT COUNT(*) AS total FROM pets p JOIN shelters s ON s.id = p.shelter_id "
        f"{where_sql}"
    )
    row = get_db().execute(sql, params).fetchone()
    return int(row["total"]) if row else 0


# --------------------------------------------------------------------------- #
# 附近救助站
# --------------------------------------------------------------------------- #


def all_shelters() -> list[dict[str, Any]]:
    """读取全部救助站档案。

    Returns:
        按录入顺序排列的救助站行字典列表。
    """
    rows = get_db().execute("SELECT * FROM shelters ORDER BY rowid").fetchall()
    return [dict(row) for row in rows]


def nearby_shelter_ids(
    reference: tuple[float, float] | None, radius_km: int
) -> list[str] | None:
    """按参考点与搜索距离筛选附近的救助站编号。

    Args:
        reference: 参考点坐标；为 ``None`` 时表示未选择所在地。
        radius_km: 搜索距离（千米）；``0`` 表示不限距离。

    Returns:
        半径内的救助站编号列表，按距离升序；未提供参考点或不限距离时
        返回 ``None``（表示不做距离限制）。
    """
    if reference is None or radius_km <= 0:
        return None

    within: list[tuple[float, str]] = []
    for shelter in all_shelters():
        distance = haversine_km(
            reference[0], reference[1], shelter["lat"], shelter["lng"]
        )
        if distance <= radius_km:
            within.append((distance, shelter["id"]))
    within.sort()
    return [shelter_id for _distance, shelter_id in within]


def list_shelters(
    base_filters: dict[str, Any],
    reference: tuple[float, float] | None = None,
    radius_km: int = 0,
) -> list[dict[str, Any]]:
    """列出（附近的）救助站，并统计其符合当前条件的在养宠物数量。

    统计时忽略 ``shelter_id`` 条件，以便用户在同一区域内切换救助站。

    Args:
        base_filters: 当前生效的检索条件（键见 :data:`FILTER_KEYS`）。
        reference: 参考点坐标；提供后按距离升序返回。
        radius_km: 搜索距离（千米）；``0`` 表示不限距离。

    Returns:
        救助站列表，每项附本地化文本、``pet_count`` 与 ``distance_km``。
    """
    filters = {key: value for key, value in base_filters.items() if key != "shelter_id"}
    filters = {key: filters.get(key, "") for key in FILTER_KEYS if key != "shelter_id"}
    filters["companions"] = base_filters.get("companions") or []
    filters["status"] = base_filters.get("status", STATUS_ADOPTABLE)

    language = current_language()
    shelters: list[dict[str, Any]] = []

    for row in all_shelters():
        distance_km: float | None = None
        if reference is not None:
            distance_km = haversine_km(
                reference[0], reference[1], row["lat"], row["lng"]
            )

        # 超出搜索距离的救助站不参与展示与计数
        if radius_km > 0 and distance_km is not None and distance_km > radius_km:
            continue

        pet_count = count_pets(**filters, shelter_ids=[row["id"]])
        shelters.append(
            {
                "id": row["id"],
                "name": pick_localized(row, "name", language),
                "city": row["city"],
                "district": row["district"],
                "address": pick_localized(row, "address", language),
                "phone": row["phone"],
                "lat": row["lat"],
                "lng": row["lng"],
                "founded_year": row["founded_year"],
                "description": pick_localized(row, "description", language),
                "pet_count": pet_count,
                "distance_km": distance_km,
            }
        )

    # 仅保留当前条件下仍有在养宠物的救助站，避免点击后得到空结果
    shelters = [shelter for shelter in shelters if shelter["pet_count"] > 0]

    if reference is not None:
        shelters.sort(key=lambda s: (s["distance_km"] is None, s["distance_km"] or 0.0))
    return shelters


# --------------------------------------------------------------------------- #
# 分页与筛选项
# --------------------------------------------------------------------------- #


def paginate(items: list[Any], page: int, per_page: int = DEFAULT_PER_PAGE) -> dict[str, Any]:
    """对列表进行分页。

    Args:
        items: 待分页的完整列表。
        page: 请求页码，从 1 开始；超出范围时会被收敛到合法区间。
        per_page: 每页条数。

    Returns:
        分页结果字典，键 ``records`` 为当前页数据（命名为 ``records`` 而非
        ``items``，以避免与 ``dict.items`` 在模板中产生属性解析冲突）；
        此外还包含 ``page``、``pages``、``total``、``has_prev``、
        ``has_next``、``prev_page``、``next_page``。
    """
    per_page = max(1, per_page)
    total = len(items)
    pages = max(1, math.ceil(total / per_page))
    current = min(max(1, page), pages)
    start = (current - 1) * per_page

    return {
        "records": items[start : start + per_page],
        "page": current,
        "pages": pages,
        "total": total,
        "per_page": per_page,
        "has_prev": current > 1,
        "has_next": current < pages,
        "prev_page": current - 1,
        "next_page": current + 1,
    }


def get_filter_options(species: str = "") -> dict[str, Any]:
    """汇总检索表单所需的全部受控词表选项。

    品种与相处对象选项随类别联动；体型选项仅在狗类别下返回，猫与其他
    宠物将得到空列表，模板据此隐藏对应控件。

    Args:
        species: 当前选中的宠物类别；空字符串表示不限。

    Returns:
        包含 ``species``、``breeds``、``breeds_by_species``、``cities``、
        ``sizes``、``genders``、``age_groups``、``companions``、``radii``、
        ``sorts``、``shows_size`` 的字典。
    """
    from vv_pet01.data.cities import city_names

    return {
        "species": SPECIES_OPTIONS,
        "breeds": breeds_for(species),
        "breeds_by_species": {item: breeds_for(item) for item in SPECIES_OPTIONS},
        "cities": city_names(),
        "sizes": SIZE_OPTIONS if shows_size(species) else [],
        "genders": GENDER_OPTIONS,
        "age_groups": [
            (value, label) for value, label, _min, _max in AGE_GROUP_OPTIONS
        ],
        "companions": COMPANION_OPTIONS,
        "radii": RADIUS_OPTIONS,
        "sorts": [
            (value, _SORT_LABELS[value]) for value in ("distance", "latest", "age_asc", "name")
        ],
        "shows_size": shows_size(species),
    }


def get_pet_detail(
    pet_id: int, reference: tuple[float, float] | None = None
) -> dict[str, Any] | None:
    """查询宠物详情。

    Args:
        pet_id: 宠物编号。
        reference: 参考点坐标，用于计算与救助站的距离。

    Returns:
        补充派生字段后的宠物档案；未找到时返回 ``None``。
    """
    row = get_db().execute(f"{_PET_SELECT} WHERE p.id = ?", [pet_id]).fetchone()
    if row is None:
        return None
    return _decorate_pet(row, reference, current_language())


def list_stories(limit: int = 8) -> list[dict[str, Any]]:
    """获取首页「救助故事」展示用的条目。

    选取最新入站的待领养宠物，取其救助经历作为故事内容；照片使用与
    类别匹配的「救助人 / 领养人与宠物合照」图库。

    Args:
        limit: 返回条数上限。

    Returns:
        已补充本地化文本与 ``story_image`` 的宠物列表，按入站日期倒序排列。
    """
    rows = get_db().execute(
        f"{_PET_SELECT} WHERE p.status = ? ORDER BY p.intake_date DESC LIMIT ?",
        [STATUS_ADOPTABLE, max(1, limit)],
    ).fetchall()
    language = current_language()

    counters: dict[str, int] = {}
    stories: list[dict[str, Any]] = []
    for row in rows:
        pet = _decorate_pet(row, None, language)
        index = counters.get(pet["species"], 0)
        counters[pet["species"]] = index + 1
        pet["story_image"] = story_image(pet["species"], index)
        stories.append(pet)
    return stories


# --------------------------------------------------------------------------- #
# 领养申请
# --------------------------------------------------------------------------- #


def _generate_reference(connection: sqlite3.Connection) -> str:
    """生成人类可读的申请编号。

    编号由「提交日期 + 当日序号」构成，便于救助站口头核对。

    Args:
        connection: 数据库连接。

    Returns:
        形如 ``AV-20260911-0001`` 的申请编号。
    """
    prefix = f"AV-{datetime.now(timezone.utc).astimezone():%Y%m%d}-"
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM applications WHERE reference LIKE ?",
        [f"{prefix}%"],
    ).fetchone()
    sequence = int(row["total"]) + 1 if row else 1
    return f"{prefix}{sequence:04d}"


def create_application(payload: dict[str, Any]) -> dict[str, Any]:
    """写入一条领养申请记录。

    Args:
        payload: 已通过表单校验的申请数据，多选字段为 Python 列表。

    Returns:
        含 ``id`` 与 ``reference`` 的新建记录摘要。
    """
    connection = get_db()
    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    cursor = connection.execute(
        """
        INSERT INTO applications (
            reference, pet_id, pet_name, pet_name_en, applicant_name, address,
            town_state_zip, email, preferred_phone, preferred_contact, is_gift,
            household_members, pets_at_home, other_info, discussion_topics,
            other_questions, extra_services, locale, status, created_at
        ) VALUES (
            '', :pet_id, :pet_name, :pet_name_en, :applicant_name, :address,
            :town_state_zip, :email, :preferred_phone, :preferred_contact, :is_gift,
            :household_members, :pets_at_home, :other_info, :discussion_topics,
            :other_questions, :extra_services, :locale, 'submitted', :created_at
        )
        """,
        {
            "pet_id": payload.get("pet_id"),
            "pet_name": payload.get("pet_name", ""),
            "pet_name_en": payload.get("pet_name_en", ""),
            "applicant_name": payload["applicant_name"],
            "address": payload.get("address", ""),
            "town_state_zip": payload.get("town_state_zip", ""),
            "email": payload["email"],
            "preferred_phone": payload.get("preferred_phone", ""),
            "preferred_contact": payload.get("preferred_contact", ""),
            "is_gift": int(bool(payload.get("is_gift"))),
            "household_members": payload.get("household_members", ""),
            "pets_at_home": json.dumps(payload.get("pets_at_home", []), ensure_ascii=False),
            "other_info": payload.get("other_info", ""),
            "discussion_topics": json.dumps(
                payload.get("discussion_topics", []), ensure_ascii=False
            ),
            "other_questions": payload.get("other_questions", ""),
            "extra_services": json.dumps(
                payload.get("extra_services", []), ensure_ascii=False
            ),
            "locale": payload.get("locale", "zh"),
            "created_at": created_at,
        },
    )
    application_id = int(cursor.lastrowid or 0)
    reference = _generate_reference(connection)
    connection.execute(
        "UPDATE applications SET reference = ? WHERE id = ?", [reference, application_id]
    )
    connection.commit()
    return {"id": application_id, "reference": reference}


def get_application(application_id: int) -> dict[str, Any] | None:
    """按主键查询领养申请。

    Args:
        application_id: 申请记录主键。

    Returns:
        申请详情字典（多选字段已解析为列表）；未找到时返回 ``None``。
    """
    row = get_db().execute(
        "SELECT * FROM applications WHERE id = ?", [application_id]
    ).fetchone()
    if row is None:
        return None
    return _decorate_application(dict(row))


def list_applications(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """按提交时间倒序列出领养申请。

    Args:
        limit: 返回条数上限。
        offset: 跳过的记录数，用于分页。

    Returns:
        申请详情字典列表。
    """
    rows = get_db().execute(
        "SELECT * FROM applications ORDER BY id DESC LIMIT ? OFFSET ?", [limit, offset]
    ).fetchall()
    return [_decorate_application(dict(row)) for row in rows]


def _decorate_application(data: dict[str, Any]) -> dict[str, Any]:
    """把申请记录行转换为模板可直接使用的字典。

    Args:
        data: ``applications`` 表的一行。

    Returns:
        多选字段解析为列表、并补充本地化宠物名与状态文案的字典。
    """

    def _load(key: str) -> list[str]:
        return _load_json_list(data.get(key))

    language = current_language()
    if _is_english(language):
        pet_name = data.get("pet_name_en") or data.get("pet_name") or ""
    else:
        pet_name = data.get("pet_name") or data.get("pet_name_en") or ""

    return {
        **data,
        "pets_at_home": _load("pets_at_home"),
        "discussion_topics": _load("discussion_topics"),
        "extra_services": _load("extra_services"),
        "is_gift": bool(data.get("is_gift")),
        "pet_display_name": pet_name,
        "status_label": APPLICATION_STATUS_LABELS.get(data.get("status", ""), "已提交"),
        "created_at_display": (data.get("created_at") or "").replace("T", " ")[:16],
    }
