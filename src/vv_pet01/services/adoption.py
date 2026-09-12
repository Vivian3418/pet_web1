"""领养业务服务模块。

集中实现狗狗搜索、附近救助站排序、分页与领养申请持久化等逻辑，
使蓝图只负责解析请求参数与渲染模板，模板只负责展示。

所有数据来自 SQLite。受控词表字段（品种 / 性别 / 体型 / 状态 / 性格标签）
以中文为规范值存取，展示时由模板通过 gettext 翻译；自由文本字段则按当前
请求语言挑选 ``xxx`` 或 ``xxx_en`` 列。

Typical usage example::

    from vv_pet01.services.adoption import search_dogs

    results = search_dogs(keyword="金毛", origin=(31.23, 121.47))
"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from typing import Any

from flask import current_app
from flask_babel import get_locale
from flask_babel import gettext as _

from vv_pet01.data.dogs import (
    AGE_GROUP_OPTIONS,
    GENDER_OPTIONS,
    SIZE_OPTIONS,
    STATUS_ADOPTABLE,
    STATUS_SLUGS,
)
from vv_pet01.db import get_db

#: 每页展示的狗狗数量。
DEFAULT_PER_PAGE: int = 9

#: 地球平均半径（千米），用于 Haversine 距离计算。
_EARTH_RADIUS_KM: float = 6371.0088

#: 年龄段查询值到展示文案（msgid）的映射。
_AGE_GROUP_LABELS: dict[str, str] = {
    "puppy": "幼犬（1 岁以下）",
    "young": "青年（1 - 3 岁）",
    "adult": "成年（3 - 7 岁）",
    "senior": "老年（7 岁以上）",
}

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


def _pick(row: dict[str, Any], base: str, language: str | None = None) -> str:
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


#: 狗狗查询语句：联表取出救助站信息，避免 N+1 查询。
_DOG_SELECT = """
    SELECT
        d.id, d.name, d.name_en, d.breed, d.gender, d.age_months, d.size,
        d.weight_kg, d.shelter_id, d.status, d.vaccinated, d.neutered,
        d.traits, d.description, d.description_en, d.image, d.story_image,
        d.intake_date,
        s.name AS shelter_name, s.name_en AS shelter_name_en,
        s.city AS city, s.district AS district,
        s.address AS shelter_address, s.address_en AS shelter_address_en,
        s.phone AS shelter_phone, s.lat AS shelter_lat, s.lng AS shelter_lng,
        s.founded_year AS shelter_founded_year,
        s.description AS shelter_description,
        s.description_en AS shelter_description_en
    FROM dogs d
    JOIN shelters s ON s.id = d.shelter_id
"""


def _build_filters(
    *,
    keyword: str,
    breed: str,
    gender: str,
    size: str,
    age_group: str,
    city: str,
    shelter_id: str,
    status: str,
) -> tuple[str, list[Any]]:
    """根据筛选条件构造 SQL WHERE 子句与参数列表。

    Args:
        keyword: 关键词，匹配多个文本字段。
        breed: 品种精确匹配。
        gender: 性别精确匹配。
        size: 体型精确匹配。
        age_group: 年龄段查询值，见 ``AGE_GROUP_OPTIONS``。
        city: 所在城市精确匹配。
        shelter_id: 救助站编号精确匹配。
        status: 领养状态；空字符串表示不限制。

    Returns:
        ``(where_sql, params)`` 二元组，``where_sql`` 以 ``WHERE`` 开头；
        无任何条件时返回 ``("", [])``。
    """
    clauses: list[str] = []
    params: list[Any] = []

    if status:
        clauses.append("d.status = ?")
        params.append(status)
    if breed:
        clauses.append("d.breed = ?")
        params.append(breed)
    if gender:
        clauses.append("d.gender = ?")
        params.append(gender)
    if size:
        clauses.append("d.size = ?")
        params.append(size)
    if shelter_id:
        clauses.append("d.shelter_id = ?")
        params.append(shelter_id)
    if city:
        clauses.append("s.city = ?")
        params.append(city)

    for value, min_months, max_months in AGE_GROUP_OPTIONS:
        if value != age_group:
            continue
        clauses.append("d.age_months >= ?")
        params.append(min_months)
        if max_months is not None:
            clauses.append("d.age_months < ?")
            params.append(max_months)
        break

    if keyword:
        pattern = f"%{keyword}%"
        clauses.append(
            "("
            "d.name LIKE ? OR d.name_en LIKE ? OR d.breed LIKE ? OR d.traits LIKE ? "
            "OR d.description LIKE ? OR d.description_en LIKE ? "
            "OR s.name LIKE ? OR s.name_en LIKE ? OR s.city LIKE ? OR s.district LIKE ?"
            ")"
        )
        params.extend([pattern] * 10)

    if not clauses:
        return "", []
    return "WHERE " + " AND ".join(clauses), params


def _decorate_dog(
    row: sqlite3.Row | dict[str, Any],
    origin: tuple[float, float] | None,
    language: str | None = None,
) -> dict[str, Any]:
    """把数据库行转换为模板可直接使用的狗狗字典。

    Args:
        row: 联表查询返回的原始行。
        origin: 用户当前位置 ``(纬度, 经度)``；为 ``None`` 时不计算距离。
        language: 语言代码；为 ``None`` 时使用当前请求语言。

    Returns:
        含本地化文本、救助站子字典、``age_text``、``status_slug`` 与
        ``distance_km`` 的字典。
    """
    data = dict(row)
    traits_raw = data.get("traits") or "[]"
    try:
        traits = json.loads(traits_raw)
    except (TypeError, ValueError):
        traits = []

    shelter = {
        "id": data["shelter_id"],
        "name": _pick(data, "shelter_name", language),
        "city": data["city"],
        "district": data["district"],
        "address": _pick(data, "shelter_address", language),
        "phone": data["shelter_phone"],
        "lat": data["shelter_lat"],
        "lng": data["shelter_lng"],
        "founded_year": data["shelter_founded_year"],
        "description": _pick(data, "shelter_description", language),
    }

    distance_km: float | None = None
    if origin is not None:
        distance_km = haversine_km(
            origin[0], origin[1], data["shelter_lat"], data["shelter_lng"]
        )

    return {
        "id": data["id"],
        "name": _pick(data, "name", language),
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
        "traits": traits,
        "description": _pick(data, "description", language),
        "image": data["image"],
        # 首页「救助故事」优先使用人与宠物的合影，缺失时回退到狗狗照片
        "story_image": data.get("story_image") or data["image"],
        "intake_date": data["intake_date"],
        "age_text": format_age(data["age_months"]),
        "shelter": shelter,
        "city": data["city"],
        "distance_km": distance_km,
    }


def _sort_dogs(
    dogs: list[dict[str, Any]],
    sort: str,
    origin: tuple[float, float] | None,
    language: str | None = None,
) -> list[dict[str, Any]]:
    """对狗狗列表排序。

    Args:
        dogs: 已完成字段补充的狗狗列表。
        sort: 排序方式，见 :func:`search_dogs`。
        origin: 用户当前位置，仅 ``distance`` 排序需要。
        language: 语言代码，用于「名字排序」选择排序键。

    Returns:
        排序后的狗狗列表；距离排序在缺少定位时回退为最新发布。
    """
    if sort == "distance" and origin is not None:
        return sorted(dogs, key=lambda d: (d["distance_km"] is None, d["distance_km"] or 0.0))
    if sort == "age_asc":
        return sorted(dogs, key=lambda d: d["age_months"])
    if sort == "name":
        key = "name_en" if _is_english(language) else "name_zh"
        return sorted(dogs, key=lambda d: d[key].lower())
    return sorted(dogs, key=lambda d: d["intake_date"], reverse=True)


def search_dogs(
    *,
    keyword: str = "",
    breed: str = "",
    gender: str = "",
    size: str = "",
    age_group: str = "",
    city: str = "",
    shelter_id: str = "",
    status: str = STATUS_ADOPTABLE,
    origin: tuple[float, float] | None = None,
    sort: str = "",
) -> list[dict[str, Any]]:
    """按条件搜索待领养狗狗。

    筛选条件之间为「与」关系；``origin`` 提供后即可计算并展示与救助站的距离。

    Args:
        keyword: 关键词，匹配呼名、品种、性格、简介与救助站信息。
        breed: 品种精确匹配。
        gender: 性别精确匹配。
        size: 体型精确匹配。
        age_group: 年龄段查询值，见 ``AGE_GROUP_OPTIONS``。
        city: 城市精确匹配。
        shelter_id: 救助站编号精确匹配。
        status: 领养状态；传入空字符串表示不限制状态。
        origin: 用户当前位置 ``(纬度, 经度)``。
        sort: 排序方式，可选 ``distance``、``latest``、``age_asc``、``name``；
            留空时，有定位则按距离、无定位则按最新发布。

    Returns:
        匹配并已补充派生字段的狗狗列表，按 ``sort`` 指定规则排序。
    """
    where_sql, params = _build_filters(
        keyword=keyword,
        breed=breed,
        gender=gender,
        size=size,
        age_group=age_group,
        city=city,
        shelter_id=shelter_id,
        status=status,
    )

    rows = get_db().execute(f"{_DOG_SELECT} {where_sql}", params).fetchall()
    language = current_language()
    dogs = [_decorate_dog(row, origin, language) for row in rows]

    resolved_sort = sort or ("distance" if origin is not None else "latest")
    return _sort_dogs(dogs, resolved_sort, origin, language)


def count_dogs(
    *,
    keyword: str = "",
    breed: str = "",
    gender: str = "",
    size: str = "",
    age_group: str = "",
    city: str = "",
    shelter_id: str = "",
    status: str = STATUS_ADOPTABLE,
) -> int:
    """统计符合筛选条件的狗狗数量。

    Args:
        各参数含义同 :func:`search_dogs`，其中 ``origin`` 与 ``sort`` 不参与统计。

    Returns:
        符合条件的记录条数。
    """
    where_sql, params = _build_filters(
        keyword=keyword,
        breed=breed,
        gender=gender,
        size=size,
        age_group=age_group,
        city=city,
        shelter_id=shelter_id,
        status=status,
    )
    sql = (
        "SELECT COUNT(*) AS total FROM dogs d JOIN shelters s ON s.id = d.shelter_id "
        f"{where_sql}"
    )
    row = get_db().execute(sql, params).fetchone()
    return int(row["total"]) if row else 0


def list_shelters(
    base_filters: dict[str, Any],
    origin: tuple[float, float] | None = None,
) -> list[dict[str, Any]]:
    """列出救助站，并统计其符合当前筛选条件的在养狗狗数量。

    统计时忽略 ``shelter_id`` 条件，以便用户在同一城市内切换救助站。

    Args:
        base_filters: 当前生效的筛选条件（同 :func:`search_dogs` 的参数）。
        origin: 用户当前位置 ``(纬度, 经度)``；提供后按距离升序返回。

    Returns:
        救助站列表，每项附本地化文本、``dog_count`` 与 ``distance_km``。
    """
    filters = {key: value for key, value in base_filters.items() if key != "shelter_id"}
    language = current_language()
    rows = get_db().execute("SELECT * FROM shelters ORDER BY rowid").fetchall()

    shelters: list[dict[str, Any]] = []
    for row in rows:
        data = dict(row)
        dog_count = count_dogs(**filters, shelter_id=data["id"])
        distance_km: float | None = None
        if origin is not None:
            distance_km = haversine_km(origin[0], origin[1], data["lat"], data["lng"])

        shelters.append(
            {
                "id": data["id"],
                "name": _pick(data, "name", language),
                "city": data["city"],
                "district": data["district"],
                "address": _pick(data, "address", language),
                "phone": data["phone"],
                "lat": data["lat"],
                "lng": data["lng"],
                "founded_year": data["founded_year"],
                "description": _pick(data, "description", language),
                "dog_count": dog_count,
                "distance_km": distance_km,
            }
        )

    # 仅保留当前筛选条件下仍有在养狗狗的救助站，避免点击后得到空结果
    shelters = [shelter for shelter in shelters if shelter["dog_count"] > 0]

    if origin is not None:
        shelters.sort(key=lambda s: (s["distance_km"] is None, s["distance_km"] or 0.0))
    return shelters


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


def get_filter_options() -> dict[str, Any]:
    """汇总搜索表单所需的全部受控词表选项。

    品种与城市选项由数据库实际数据生成，保证与数据保持一致；
    所有标签均为 msgid，由模板通过 gettext 翻译。

    Returns:
        包含 ``breeds``、``cities``、``sizes``、``genders``、``age_groups``、
        ``sorts`` 的字典。
    """
    connection = get_db()
    breeds = [
        row["breed"]
        for row in connection.execute("SELECT DISTINCT breed FROM dogs ORDER BY breed")
    ]
    cities = [
        row["city"]
        for row in connection.execute(
            "SELECT city FROM shelters GROUP BY city ORDER BY MIN(rowid)"
        )
    ]
    return {
        "breeds": breeds,
        "cities": cities,
        "sizes": SIZE_OPTIONS,
        "genders": GENDER_OPTIONS,
        "age_groups": [(value, _AGE_GROUP_LABELS[value]) for value, _min, _max in AGE_GROUP_OPTIONS],
        "sorts": [(value, _SORT_LABELS[value]) for value in ("distance", "latest", "age_asc", "name")],
    }


def get_dog_detail(dog_id: int, origin: tuple[float, float] | None = None) -> dict[str, Any] | None:
    """查询狗狗详情。

    Args:
        dog_id: 狗狗编号。
        origin: 用户当前位置 ``(纬度, 经度)``，用于计算与救助站的距离。

    Returns:
        补充派生字段后的狗狗档案；未找到时返回 ``None``。
    """
    row = get_db().execute(f"{_DOG_SELECT} WHERE d.id = ?", [dog_id]).fetchone()
    if row is None:
        return None
    return _decorate_dog(row, origin, current_language())


def list_stories(limit: int = 8) -> list[dict[str, Any]]:
    """获取首页「救助故事」展示用的狗狗条目。

    选取最新入站的待领养狗狗，取其救助经历作为故事内容；文案与图片
    均复用狗狗档案，因此卡片可直接跳转到详情页并进入领养申请。

    Args:
        limit: 返回条数上限。

    Returns:
        已补充本地化文本的狗狗列表，按入站日期倒序排列。
    """
    rows = get_db().execute(
        f"{_DOG_SELECT} WHERE d.status = ? ORDER BY d.intake_date DESC LIMIT ?",
        [STATUS_ADOPTABLE, max(1, limit)],
    ).fetchall()
    language = current_language()
    return [_decorate_dog(row, None, language) for row in rows]


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
            reference, dog_id, dog_name, dog_name_en, applicant_name, address,
            town_state_zip, email, preferred_phone, preferred_contact, is_gift,
            household_members, pets_at_home, other_info, discussion_topics,
            other_questions, extra_services, locale, status, created_at
        ) VALUES (
            '', :dog_id, :dog_name, :dog_name_en, :applicant_name, :address,
            :town_state_zip, :email, :preferred_phone, :preferred_contact, :is_gift,
            :household_members, :pets_at_home, :other_info, :discussion_topics,
            :other_questions, :extra_services, :locale, 'submitted', :created_at
        )
        """,
        {
            "dog_id": payload.get("dog_id"),
            "dog_name": payload.get("dog_name", ""),
            "dog_name_en": payload.get("dog_name_en", ""),
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
        多选字段解析为列表、并补充本地化狗狗名与状态文案的字典。
    """

    def _load(key: str) -> list[str]:
        try:
            value = json.loads(data.get(key) or "[]")
        except (TypeError, ValueError):
            return []
        return value if isinstance(value, list) else []

    language = current_language()
    if _is_english(language):
        dog_name = data.get("dog_name_en") or data.get("dog_name") or ""
    else:
        dog_name = data.get("dog_name") or data.get("dog_name_en") or ""

    return {
        **data,
        "pets_at_home": _load("pets_at_home"),
        "discussion_topics": _load("discussion_topics"),
        "extra_services": _load("extra_services"),
        "is_gift": bool(data.get("is_gift")),
        "dog_display_name": dog_name,
        "status_label": APPLICATION_STATUS_LABELS.get(data.get("status", ""), "已提交"),
        "created_at_display": (data.get("created_at") or "").replace("T", " ")[:16],
    }
