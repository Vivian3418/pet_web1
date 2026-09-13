"""公益业务服务模块。

覆盖「参与公益」菜单下的三类业务：

* **动物救助**：提交救助工单（含照片与位置）、计算附近救助站、推进工单状态；
* **成为志愿者**：保存志愿者申请；
* **爱心捐款**：保存一次性 / 每月定期捐赠记录并汇总。

本模块只负责数据读写与业务规则，请求解析与渲染由蓝图与模板承担。

Typical usage example::

    from vv_pet01.services.charity import create_rescue_report

    created = create_rescue_report({"animal_type": "猫", "situation": "受伤"})
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from flask import current_app
from flask_babel import gettext
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from vv_pet01.data.taxonomy import (
    ALLOWED_IMAGE_EXTENSIONS,
    DONATION_FREQUENCY_OPTIONS,
    DONATION_FREQUENCY_ONCE,
    RESCUE_STATUS_FLOW,
    RESCUE_STATUS_PENDING,
    RESCUE_STATUS_SLUGS,
)
from vv_pet01.db import get_db
from vv_pet01.services.adoption import (
    all_shelters,
    current_language,
    haversine_km,
    pick_localized,
)

#: 上传图片存放的子目录名（位于 Flask 实例目录下）。
UPLOAD_DIR_NAME: str = "uploads"

#: 捐赠周期到展示文案（msgid）的映射。
DONATION_FREQUENCY_LABELS: dict[str, str] = dict(DONATION_FREQUENCY_OPTIONS)

#: 捐赠状态到展示文案（msgid）的映射。
DONATION_STATUS_LABELS: dict[str, str] = {
    "pledged": "待扣款",
    "paid": "已完成",
}

#: 志愿者申请状态到展示文案（msgid）的映射。
VOLUNTEER_STATUS_LABELS: dict[str, str] = {
    "submitted": "已提交",
    "interview": "待面谈",
    "onboarding": "入职培训中",
}


# --------------------------------------------------------------------------- #
# 通用工具
# --------------------------------------------------------------------------- #


def _load_list(raw: Any) -> list[str]:
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


def _now() -> str:
    """返回当前时间的 ISO 字符串。

    Returns:
        带时区偏移的 ISO 8601 时间字符串（精确到秒）。
    """
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _generate_reference(connection: sqlite3.Connection, table: str, prefix: str) -> str:
    """生成人类可读的业务编号。

    编号由「前缀 + 日期 + 当日序号」构成，便于口头核对。

    Args:
        connection: 数据库连接。
        table: 目标表名（内部常量，不接受外部输入）。
        prefix: 编号前缀，如 ``RESCUE``。

    Returns:
        形如 ``RESCUE-20260913-0001`` 的编号。
    """
    today = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d")
    full_prefix = f"{prefix}-{today}-"
    row = connection.execute(
        f"SELECT COUNT(*) AS total FROM {table} WHERE reference LIKE ?",
        [f"{full_prefix}%"],
    ).fetchone()
    sequence = int(row["total"]) + 1 if row else 1
    return f"{full_prefix}{sequence:04d}"


def upload_dir() -> Path:
    """返回上传图片的存放目录，并确保其存在。

    Returns:
        实例目录下的 ``uploads`` 目录路径。
    """
    directory = Path(current_app.instance_path) / UPLOAD_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_photo(file: FileStorage | None, prefix: str = "rescue") -> str:
    """保存用户上传的照片并返回可用于展示的相对路径。

    仅接受常见图片扩展名（jpg / jpeg / png / webp），文件名会做安全处理并
    追加随机串以避免冲突。

    Args:
        file: 上传的文件对象；为空或文件名为空时直接返回空字符串。
        prefix: 文件名前缀，便于区分业务来源。

    Returns:
        形如 ``uploads/rescue-<uuid>.jpg`` 的相对路径；未上传或校验失败时返回空串。
    """
    if file is None or not file.filename:
        return ""

    original = secure_filename(file.filename)
    extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return ""

    filename = f"{prefix}-{uuid.uuid4().hex[:12]}.{extension}"
    file.save(upload_dir() / filename)
    return f"{UPLOAD_DIR_NAME}/{filename}"


def nearest_shelters(
    reference: tuple[float, float] | None, limit: int = 4
) -> list[dict[str, Any]]:
    """查询距离参考点最近的若干救助站。

    Args:
        reference: 参考点坐标 ``(纬度, 经度)``；为 ``None`` 时按录入顺序返回。
        limit: 返回条数上限。

    Returns:
        救助站列表，每项附本地化文本与 ``distance_km``，按距离升序排列。
    """
    language = current_language()
    shelters: list[dict[str, Any]] = []

    for row in all_shelters():
        distance_km: float | None = None
        if reference is not None:
            distance_km = haversine_km(
                reference[0], reference[1], row["lat"], row["lng"]
            )
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
                "description": pick_localized(row, "description", language),
                "distance_km": distance_km,
            }
        )

    if reference is not None:
        shelters.sort(key=lambda item: (item["distance_km"], item["id"]))
    return shelters[:limit]


# --------------------------------------------------------------------------- #
# 动物救助工单
# --------------------------------------------------------------------------- #


def create_rescue_report(payload: dict[str, Any]) -> dict[str, Any]:
    """写入一条动物救助工单。

    Args:
        payload: 已通过表单校验的工单数据。

    Returns:
        含 ``id`` 与 ``reference`` 的新建记录摘要。
    """
    connection = get_db()
    timestamp = _now()
    cursor = connection.execute(
        """
        INSERT INTO rescue_reports (
            reference, animal_type, situation, urgency, handling, description,
            photo_path, address_text, lat, lng, nearest_shelter_id,
            reporter_name, reporter_phone, reporter_email, handler_note,
            status, locale, created_at, updated_at
        ) VALUES (
            '', :animal_type, :situation, :urgency, :handling, :description,
            :photo_path, :address_text, :lat, :lng, :nearest_shelter_id,
            :reporter_name, :reporter_phone, :reporter_email, '',
            :status, :locale, :created_at, :updated_at
        )
        """,
        {
            "animal_type": payload.get("animal_type", ""),
            "situation": payload.get("situation", ""),
            "urgency": payload.get("urgency", ""),
            "handling": payload.get("handling", ""),
            "description": payload.get("description", ""),
            "photo_path": payload.get("photo_path", ""),
            "address_text": payload.get("address_text", ""),
            "lat": payload.get("lat"),
            "lng": payload.get("lng"),
            "nearest_shelter_id": payload.get("nearest_shelter_id"),
            "reporter_name": payload.get("reporter_name", ""),
            "reporter_phone": payload.get("reporter_phone", ""),
            "reporter_email": payload.get("reporter_email", ""),
            "status": RESCUE_STATUS_PENDING,
            "locale": payload.get("locale", "zh"),
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )
    report_id = int(cursor.lastrowid or 0)
    reference = _generate_reference(connection, "rescue_reports", "RESCUE")
    connection.execute(
        "UPDATE rescue_reports SET reference = ? WHERE id = ?", [reference, report_id]
    )
    connection.commit()
    return {"id": report_id, "reference": reference}


def _decorate_rescue_report(data: dict[str, Any]) -> dict[str, Any]:
    """把救助工单行转换为模板可直接使用的字典。

    Args:
        data: ``rescue_reports`` 表的一行。

    Returns:
        补充状态样式类、时间显示格式与附近救助站名称的字典。
    """
    shelter_id = data.get("nearest_shelter_id")
    shelter_name = ""
    if shelter_id:
        row = get_db().execute(
            "SELECT name, name_en FROM shelters WHERE id = ?", [shelter_id]
        ).fetchone()
        if row:
            shelter_name = pick_localized(dict(row), "name")

    return {
        **data,
        "status_slug": RESCUE_STATUS_SLUGS.get(data.get("status", ""), "pending"),
        "nearest_shelter_name": shelter_name,
        "can_advance": data.get("status") in RESCUE_STATUS_FLOW,
        "next_status": RESCUE_STATUS_FLOW.get(data.get("status", "")),
        "created_at_display": (data.get("created_at") or "").replace("T", " ")[:16],
        "updated_at_display": (data.get("updated_at") or "").replace("T", " ")[:16],
    }


def get_rescue_report(report_id: int) -> dict[str, Any] | None:
    """按主键查询救助工单。

    Args:
        report_id: 工单主键。

    Returns:
        工单字典；未找到时返回 ``None``。
    """
    row = get_db().execute(
        "SELECT * FROM rescue_reports WHERE id = ?", [report_id]
    ).fetchone()
    if row is None:
        return None
    return _decorate_rescue_report(dict(row))


def list_rescue_reports(
    limit: int = 50, offset: int = 0, status: str = ""
) -> list[dict[str, Any]]:
    """按提交时间倒序列出救助工单。

    Args:
        limit: 返回条数上限。
        offset: 跳过的记录数。
        status: 可选的状态过滤；空字符串表示全部。

    Returns:
        工单字典列表。
    """
    sql = "SELECT * FROM rescue_reports"
    params: list[Any] = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = get_db().execute(sql, params).fetchall()
    return [_decorate_rescue_report(dict(row)) for row in rows]


def rescue_status_counts() -> dict[str, int]:
    """统计各状态的救助工单数量。

    Returns:
        状态到数量的映射；无记录的状为 0。
    """
    counts = {status: 0 for status in RESCUE_STATUS_SLUGS}
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS total FROM rescue_reports GROUP BY status"
    ).fetchall()
    for row in rows:
        counts[row["status"]] = int(row["total"])
    return counts


def advance_rescue_status(report_id: int, note: str = "") -> str | None:
    """把救助工单推进到下一个状态。

    状态流转固定为「未被救助 → 正在救助中 → 救助成功」；已是终态时不做变更。

    Args:
        report_id: 工单主键。
        note: 工作人员备注，会覆盖原有备注。

    Returns:
        推进后的状态；工单不存在或已是终态时返回 ``None``。
    """
    connection = get_db()
    row = connection.execute(
        "SELECT status FROM rescue_reports WHERE id = ?", [report_id]
    ).fetchone()
    if row is None:
        return None

    next_status = RESCUE_STATUS_FLOW.get(row["status"])
    if next_status is None:
        return None

    if note:
        connection.execute(
            "UPDATE rescue_reports SET status = ?, handler_note = ?, updated_at = ? WHERE id = ?",
            [next_status, note, _now(), report_id],
        )
    else:
        connection.execute(
            "UPDATE rescue_reports SET status = ?, updated_at = ? WHERE id = ?",
            [next_status, _now(), report_id],
        )
    connection.commit()
    return next_status


# --------------------------------------------------------------------------- #
# 志愿者申请
# --------------------------------------------------------------------------- #


def create_volunteer_application(payload: dict[str, Any]) -> dict[str, Any]:
    """写入一条志愿者申请。

    Args:
        payload: 已通过表单校验的申请数据，多选字段为 Python 列表。

    Returns:
        含 ``id`` 与 ``reference`` 的新建记录摘要。
    """
    connection = get_db()
    cursor = connection.execute(
        """
        INSERT INTO volunteer_applications (
            reference, full_name, email, phone, city, occupation, is_adult,
            guardian_name, skills, skill_detail, tasks, availability,
            commitment, start_availability, experience, motivation,
            physical_ok, accept_handbook, emergency_name, emergency_phone,
            locale, status, created_at
        ) VALUES (
            '', :full_name, :email, :phone, :city, :occupation, :is_adult,
            :guardian_name, :skills, :skill_detail, :tasks, :availability,
            :commitment, :start_availability, :experience, :motivation,
            :physical_ok, :accept_handbook, :emergency_name, :emergency_phone,
            :locale, 'submitted', :created_at
        )
        """,
        {
            "full_name": payload.get("full_name", ""),
            "email": payload.get("email", ""),
            "phone": payload.get("phone", ""),
            "city": payload.get("city", ""),
            "occupation": payload.get("occupation", ""),
            "is_adult": int(bool(payload.get("is_adult", True))),
            "guardian_name": payload.get("guardian_name", ""),
            "skills": json.dumps(payload.get("skills", []), ensure_ascii=False),
            "skill_detail": payload.get("skill_detail", ""),
            "tasks": json.dumps(payload.get("tasks", []), ensure_ascii=False),
            "availability": json.dumps(
                payload.get("availability", []), ensure_ascii=False
            ),
            "commitment": payload.get("commitment", ""),
            "start_availability": payload.get("start_availability", ""),
            "experience": payload.get("experience", ""),
            "motivation": payload.get("motivation", ""),
            "physical_ok": int(bool(payload.get("physical_ok", True))),
            "accept_handbook": int(bool(payload.get("accept_handbook"))),
            "emergency_name": payload.get("emergency_name", ""),
            "emergency_phone": payload.get("emergency_phone", ""),
            "locale": payload.get("locale", "zh"),
            "created_at": _now(),
        },
    )
    application_id = int(cursor.lastrowid or 0)
    reference = _generate_reference(connection, "volunteer_applications", "VOL")
    connection.execute(
        "UPDATE volunteer_applications SET reference = ? WHERE id = ?",
        [reference, application_id],
    )
    connection.commit()
    return {"id": application_id, "reference": reference}


def get_volunteer_application(application_id: int) -> dict[str, Any] | None:
    """按主键查询志愿者申请。

    Args:
        application_id: 申请主键。

    Returns:
        申请字典（多选字段已解析为列表）；未找到时返回 ``None``。
    """
    row = get_db().execute(
        "SELECT * FROM volunteer_applications WHERE id = ?", [application_id]
    ).fetchone()
    if row is None:
        return None
    return _decorate_volunteer_application(dict(row))


def list_volunteer_applications(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """按提交时间倒序列出志愿者申请。

    Args:
        limit: 返回条数上限。
        offset: 跳过的记录数。

    Returns:
        申请字典列表。
    """
    rows = get_db().execute(
        "SELECT * FROM volunteer_applications ORDER BY id DESC LIMIT ? OFFSET ?",
        [limit, offset],
    ).fetchall()
    return [_decorate_volunteer_application(dict(row)) for row in rows]


def _decorate_volunteer_application(data: dict[str, Any]) -> dict[str, Any]:
    """把志愿者申请行转换为模板可直接使用的字典。

    Args:
        data: ``volunteer_applications`` 表的一行。

    Returns:
        多选字段解析为列表、并补充状态文案与时间显示的字典。
    """
    return {
        **data,
        "skills": _load_list(data.get("skills")),
        "tasks": _load_list(data.get("tasks")),
        "availability": _load_list(data.get("availability")),
        "is_adult": bool(data.get("is_adult")),
        "physical_ok": bool(data.get("physical_ok")),
        "accept_handbook": bool(data.get("accept_handbook")),
        "status_label": VOLUNTEER_STATUS_LABELS.get(data.get("status", ""), "已提交"),
        "created_at_display": (data.get("created_at") or "").replace("T", " ")[:16],
    }


# --------------------------------------------------------------------------- #
# 爱心捐款
# --------------------------------------------------------------------------- #


def create_donation(payload: dict[str, Any]) -> dict[str, Any]:
    """写入一条捐赠记录。

    演示项目不接入支付渠道，记录以「待扣款」状态保存。

    Args:
        payload: 已通过表单校验的捐赠数据。

    Returns:
        含 ``id`` 与 ``reference`` 的新建记录摘要。
    """
    connection = get_db()
    cursor = connection.execute(
        """
        INSERT INTO donations (
            reference, donor_name, email, amount, frequency, designation,
            message, anonymous, locale, status, created_at
        ) VALUES (
            '', :donor_name, :email, :amount, :frequency, :designation,
            :message, :anonymous, :locale, 'pledged', :created_at
        )
        """,
        {
            "donor_name": payload.get("donor_name", ""),
            "email": payload.get("email", ""),
            "amount": float(payload.get("amount", 0)),
            "frequency": payload.get("frequency", DONATION_FREQUENCY_ONCE),
            "designation": payload.get("designation", ""),
            "message": payload.get("message", ""),
            "anonymous": int(bool(payload.get("anonymous"))),
            "locale": payload.get("locale", "zh"),
            "created_at": _now(),
        },
    )
    donation_id = int(cursor.lastrowid or 0)
    reference = _generate_reference(connection, "donations", "DN")
    connection.execute(
        "UPDATE donations SET reference = ? WHERE id = ?", [reference, donation_id]
    )
    connection.commit()
    return {"id": donation_id, "reference": reference}


def get_donation(donation_id: int) -> dict[str, Any] | None:
    """按主键查询捐赠记录。

    Args:
        donation_id: 捐赠记录主键。

    Returns:
        捐赠字典；未找到时返回 ``None``。
    """
    row = get_db().execute(
        "SELECT * FROM donations WHERE id = ?", [donation_id]
    ).fetchone()
    if row is None:
        return None
    return _decorate_donation(dict(row))


def list_donations(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """按提交时间倒序列出捐赠记录。

    Args:
        limit: 返回条数上限。
        offset: 跳过的记录数。

    Returns:
        捐赠字典列表。
    """
    rows = get_db().execute(
        "SELECT * FROM donations ORDER BY id DESC LIMIT ? OFFSET ?", [limit, offset]
    ).fetchall()
    return [_decorate_donation(dict(row)) for row in rows]


def donation_summary() -> dict[str, Any]:
    """汇总捐赠数据，用于页面展示。

    Returns:
        含 ``total_amount``（累计金额）、``monthly_amount``（每月定期金额）、
        ``count``（捐赠笔数）与 ``donor_count``（去重捐赠人数）的字典。
    """
    connection = get_db()
    total = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) AS amount FROM donations"
    ).fetchone()
    monthly = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) AS amount FROM donations WHERE frequency = 'monthly'"
    ).fetchone()
    count = connection.execute("SELECT COUNT(*) AS total FROM donations").fetchone()
    donors = connection.execute(
        "SELECT COUNT(DISTINCT email) AS total FROM donations"
    ).fetchone()

    return {
        "total_amount": round(float(total["amount"]), 2) if total else 0.0,
        "monthly_amount": round(float(monthly["amount"]), 2) if monthly else 0.0,
        "count": int(count["total"]) if count else 0,
        "donor_count": int(donors["total"]) if donors else 0,
    }


def _decorate_donation(data: dict[str, Any]) -> dict[str, Any]:
    """把捐赠行转换为模板可直接使用的字典。

    Args:
        data: ``donations`` 表的一行。

    Returns:
        补充周期文案、状态文案、时间显示与匿名展示名的字典。
    """
    anonymous = bool(data.get("anonymous"))
    donor_name = data.get("donor_name") or ""
    return {
        **data,
        "anonymous": anonymous,
        # 匿名或未填写称呼时统一展示为「爱心人士」，该文案需要跟随语言切换
        "display_name": gettext("爱心人士") if anonymous or not donor_name else donor_name,
        "frequency_label": DONATION_FREQUENCY_LABELS.get(
            data.get("frequency", ""), "一次性捐赠"
        ),
        "status_label": DONATION_STATUS_LABELS.get(data.get("status", ""), "待扣款"),
        "amount_display": f"{float(data.get('amount') or 0):.2f}",
        "created_at_display": (data.get("created_at") or "").replace("T", " ")[:16],
    }


def recent_donation_tiers() -> Sequence[int]:
    """返回可选捐赠档位。

    该函数仅用于模板侧的语义封装，实际档位定义见
    :data:`vv_pet01.data.taxonomy.DONATION_AMOUNTS`。

    Returns:
        捐赠档位列表。
    """
    from vv_pet01.data.taxonomy import DONATION_AMOUNTS

    return tuple(DONATION_AMOUNTS)
