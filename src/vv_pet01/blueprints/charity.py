"""参与公益板块蓝图模块。

对应顶部导航「参与公益」下拉菜单，全部路由均带 ``<lang_code>`` 语言前缀：

* ``/charity/rescue``：动物救助页（说明可救助情形、定位查看最近救助站、提交救助工单）。
* ``/charity/rescue/<report_id>``：救助工单回执页。
* ``/charity/rescue/reports``：救助工单列表（工作人员可推进状态）。
* ``/charity/volunteer``：成为志愿者（工作内容介绍 + 申请表）。
* ``/charity/volunteer/<application_id>``：志愿者申请回执页。
* ``/charity/donate``：爱心捐款（一次性 / 每月定期，5 个预设档位或自定义金额）。
* ``/charity/donate/<donation_id>``：捐赠回执页。
* ``/charity/donations``：捐赠记录列表。
* ``/charity/activities``、``/charity/foster``：占位页面（已移出导航，链接仍可访问）。
"""

from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_babel import gettext as _

from vv_pet01.data.cities import city_center_from_text, city_names
from vv_pet01.data.taxonomy import (
    DONATION_AMOUNTS,
    DONATION_DESIGNATION_OPTIONS,
    DONATION_FREQUENCY_OPTIONS,
    RESCUE_ANIMAL_OPTIONS,
    RESCUE_HANDLING_OPTIONS,
    RESCUE_SITUATION_OPTIONS,
    RESCUE_STATUS_OPTIONS,
    RESCUE_STATUS_PENDING,
    RESCUE_STATUS_RESCUED,
    RESCUE_URGENCY_OPTIONS,
    VOLUNTEER_AVAILABILITY_OPTIONS,
    VOLUNTEER_COMMITMENT_OPTIONS,
    VOLUNTEER_SKILL_OPTIONS,
    VOLUNTEER_TASK_OPTIONS,
)
from vv_pet01.forms import (
    DonationForm,
    RescueReportForm,
    VolunteerApplicationForm,
)
from vv_pet01.services.charity import (
    advance_rescue_status,
    create_donation,
    create_rescue_report,
    create_volunteer_application,
    donation_summary,
    get_donation,
    get_rescue_report,
    get_volunteer_application,
    list_donations,
    list_rescue_reports,
    list_volunteer_applications,
    nearest_shelters,
    rescue_status_counts,
    save_photo,
    upload_dir,
)
from vv_pet01.services.adoption import current_language, paginate

charity_bp = Blueprint("charity", __name__, url_prefix="/<lang_code>/charity")

#: 记录列表单页展示条数。
RECORDS_PER_PAGE: int = 20


def _clean(value: str | None) -> str:
    """去除查询参数的首尾空白。

    Args:
        value: 原始查询参数值，可能为 ``None``。

    Returns:
        去除空白后的字符串。
    """
    return (value or "").strip()


def _parse_page(value: str | None) -> int:
    """解析页码查询参数。

    Args:
        value: 原始页码字符串。

    Returns:
        合法页码，非法输入回退为第 1 页。
    """
    try:
        return max(1, int(value or 1))
    except (TypeError, ValueError):
        return 1


def _parse_coordinates(args) -> tuple[float, float] | None:  # noqa: ANN001
    """从查询参数中解析经纬度。

    Args:
        args: Flask 的 ``request.args``。

    Returns:
        ``(纬度, 经度)``；缺失或非法时返回 ``None``。
    """
    raw_lat, raw_lng = args.get("lat"), args.get("lng")
    if raw_lat is None or raw_lng is None:
        return None
    try:
        lat, lng = float(raw_lat), float(raw_lng)
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return None
    return lat, lng


def _rescue_reference(address: str, coordinates: tuple[float, float] | None):
    """解析动物救助页的参考点。

    优先使用浏览器定位坐标，其次依据手填地址匹配城市中心。

    Args:
        address: 用户手动输入的地址。
        coordinates: 浏览器定位坐标。

    Returns:
        ``(参考点坐标, 参考点来源)``；无法确定时为 ``(None, "")``。
    """
    if coordinates is not None:
        return coordinates, "geo"
    center = city_center_from_text(address)
    if center is not None:
        return (center.lat, center.lng), "address"
    return None, ""


# --------------------------------------------------------------------------- #
# 动物救助
# --------------------------------------------------------------------------- #


@charity_bp.route("/rescue", methods=["GET", "POST"])
def rescue():
    """动物救助页。

    ``GET`` 渲染救助说明、定位/地址输入、最近救助站地图与救助申请表；
    ``POST`` 校验并写入救助工单，成功后重定向到回执页。

    Returns:
        GET 返回页面 HTML；POST 成功返回 302 重定向。
    """
    address = _clean(request.args.get("address"))
    coordinates = _parse_coordinates(request.args)
    reference, reference_source = _rescue_reference(address, coordinates)

    form = RescueReportForm()
    form.localize_choices()

    if request.method == "POST" and form.validate_on_submit():
        payload = form.to_payload()
        payload["locale"] = current_language()
        # 照片先落盘再存路径；未上传或格式不符时为空串
        payload["photo_path"] = save_photo(form.photo.data, prefix="rescue")

        # 记录参考点附近最近的救助站，便于指派跟进
        targets = nearest_shelters(reference, limit=1)
        payload["nearest_shelter_id"] = targets[0]["id"] if targets else None

        created = create_rescue_report(payload)
        return redirect(url_for("charity.rescue_detail", report_id=created["id"]))

    shelters = nearest_shelters(reference, limit=4)
    return render_template(
        "charity/rescue.html",
        page_title=_("动物救助"),
        page_desc=_("发现需要帮助的动物时，可以先确认附近救助站，也可以上传照片与位置由我们前往救助。"),
        form=form,
        address=address,
        reference=reference,
        reference_source=reference_source,
        shelters=shelters,
        map_shelters=[
            {
                "name": shelter["name"],
                "lat": shelter["lat"],
                "lng": shelter["lng"],
                "address": shelter["address"],
                "phone": shelter["phone"],
                "distance_km": shelter["distance_km"],
            }
            for shelter in shelters
        ],
        map_reference=(
            {"lat": reference[0], "lng": reference[1]} if reference else None
        ),
        cities=city_names(),
        animal_options=RESCUE_ANIMAL_OPTIONS,
        situation_options=RESCUE_SITUATION_OPTIONS,
        urgency_options=RESCUE_URGENCY_OPTIONS,
        handling_options=RESCUE_HANDLING_OPTIONS,
        status_options=RESCUE_STATUS_OPTIONS,
    )


@charity_bp.get("/rescue/reports")
def rescue_reports() -> str:
    """救助工单列表页（供工作人员推进状态）。

    Returns:
        工单列表模板渲染后的 HTML 字符串。
    """
    status = _clean(request.args.get("status"))
    page = _parse_page(request.args.get("page"))
    records = list_rescue_reports(limit=500, status=status)
    pagination = paginate(records, page, RECORDS_PER_PAGE)

    return render_template(
        "charity/rescue_reports.html",
        page_title=_("救助工单"),
        page_desc=_("这里展示全部救助上报记录，工作人员可以在此推进处理状态。"),
        pagination=pagination,
        status_filter=status,
        status_options=RESCUE_STATUS_OPTIONS,
        counts=rescue_status_counts(),
        base_params={"status": status} if status else {},
    )


@charity_bp.post("/rescue/reports/<int:report_id>/advance")
def rescue_advance(report_id: int) -> str:
    """推进救助工单状态。

    状态流转固定为「未被救助 → 正在救助中 → 救助成功」。

    Args:
        report_id: 工单主键。

    Returns:
        重定向到工单列表的 302 响应。

    Raises:
        werkzeug.exceptions.NotFound: 工单不存在或已是终态时抛出 404。
    """
    note = _clean(request.form.get("note"))
    next_status = advance_rescue_status(report_id, note=note)
    if next_status is None:
        abort(404)

    page = _parse_page(request.form.get("page"))
    status = _clean(request.form.get("status"))
    return redirect(
        url_for("charity.rescue_reports", page=page, status=status or None)
    )


@charity_bp.get("/rescue/<int:report_id>")
def rescue_detail(report_id: int) -> str:
    """救助工单回执页。

    Args:
        report_id: 工单主键。

    Returns:
        工单回执模板渲染后的 HTML 字符串。

    Raises:
        werkzeug.exceptions.NotFound: 工单不存在时抛出 404。
    """
    report = get_rescue_report(report_id)
    if report is None:
        abort(404)

    return render_template(
        "charity/rescue_success.html",
        page_title=_("救助请求已提交"),
        page_desc=_("我们已收到你的救助请求，工作人员会尽快联系并跟进。"),
        report=report,
        is_pending=report["status"] == RESCUE_STATUS_PENDING,
        is_rescued=report["status"] == RESCUE_STATUS_RESCUED,
    )


# --------------------------------------------------------------------------- #
# 成为志愿者
# --------------------------------------------------------------------------- #


@charity_bp.route("/volunteer", methods=["GET", "POST"])
def volunteer():
    """成为志愿者页面（工作内容介绍 + 申请表）。

    Returns:
        GET 返回页面 HTML；POST 成功返回 302 重定向。
    """
    form = VolunteerApplicationForm()
    form.localize_choices()

    if request.method == "POST" and form.validate_on_submit():
        payload = form.to_payload()
        payload["locale"] = current_language()
        created = create_volunteer_application(payload)
        return redirect(url_for("charity.volunteer_detail", application_id=created["id"]))

    return render_template(
        "charity/volunteer.html",
        page_title=_("成为志愿者"),
        page_desc=_("志愿者是救助站最重要的支持力量，欢迎了解工作内容并提交申请。"),
        form=form,
        task_options=VOLUNTEER_TASK_OPTIONS,
        skill_options=VOLUNTEER_SKILL_OPTIONS,
        availability_options=VOLUNTEER_AVAILABILITY_OPTIONS,
        commitment_options=VOLUNTEER_COMMITMENT_OPTIONS,
        recent_applications=list_volunteer_applications(limit=3),
    )


@charity_bp.get("/volunteer/<int:application_id>")
def volunteer_detail(application_id: int) -> str:
    """志愿者申请回执页。

    Args:
        application_id: 申请主键。

    Returns:
        申请回执模板渲染后的 HTML 字符串。

    Raises:
        werkzeug.exceptions.NotFound: 申请不存在时抛出 404。
    """
    application = get_volunteer_application(application_id)
    if application is None:
        abort(404)

    return render_template(
        "charity/volunteer_success.html",
        page_title=_("志愿者申请已提交"),
        page_desc=_("感谢你的加入！我们会在 5 个工作日内与你联系安排面谈与培训。"),
        application=application,
    )


# --------------------------------------------------------------------------- #
# 爱心捐款
# --------------------------------------------------------------------------- #


@charity_bp.route("/donate", methods=["GET", "POST"])
def donate():
    """爱心捐款页面。

    Returns:
        GET 返回页面 HTML；POST 成功返回 302 重定向。
    """
    form = DonationForm()
    form.localize_choices()

    if request.method == "POST" and form.validate_on_submit():
        amount = form.resolve_amount()
        if amount is None:
            form.custom_amount.errors.append("请输入有效的自定义金额")
        else:
            payload = form.to_payload()
            payload["locale"] = current_language()
            created = create_donation(payload)
            return redirect(url_for("charity.donation_detail", donation_id=created["id"]))

    return render_template(
        "charity/donate.html",
        page_title=_("爱心捐款"),
        page_desc=_("你的每一笔捐赠都会用于动物救助、医疗绝育与日常物资。"),
        form=form,
        amounts=DONATION_AMOUNTS,
        frequency_options=DONATION_FREQUENCY_OPTIONS,
        designation_options=DONATION_DESIGNATION_OPTIONS,
        summary=donation_summary(),
        recent_donations=list_donations(limit=5),
    )


@charity_bp.get("/donate/<int:donation_id>")
def donation_detail(donation_id: int) -> str:
    """捐赠回执页。

    Args:
        donation_id: 捐赠记录主键。

    Returns:
        捐赠回执模板渲染后的 HTML 字符串。

    Raises:
        werkzeug.exceptions.NotFound: 记录不存在时抛出 404。
    """
    donation = get_donation(donation_id)
    if donation is None:
        abort(404)

    return render_template(
        "charity/donate_success.html",
        page_title=_("感谢你的爱心捐赠"),
        page_desc=_("我们已记录你的捐赠意向，将按你选择的方式完成扣款。"),
        donation=donation,
    )


@charity_bp.get("/donations")
def donations() -> str:
    """捐赠记录列表页。

    Returns:
        捐赠记录模板渲染后的 HTML 字符串。
    """
    page = _parse_page(request.args.get("page"))
    records = list_donations(limit=500)
    pagination = paginate(records, page, RECORDS_PER_PAGE)

    return render_template(
        "charity/donations.html",
        page_title=_("捐赠记录"),
        page_desc=_("这里展示本站收到的全部爱心捐赠。"),
        pagination=pagination,
        summary=donation_summary(),
        base_params={},
    )


# --------------------------------------------------------------------------- #
# 上传文件访问
# --------------------------------------------------------------------------- #


@charity_bp.get("/uploads/<path:filename>")
def uploaded_photo(filename: str):
    """提供上传照片的读取入口。

    上传文件保存在实例目录而非静态目录，因此需要单独的只读路由；
    使用 ``send_from_directory`` 以避免路径穿越。

    Args:
        filename: 上传目录下的文件名。

    Returns:
        图片文件的响应。

    Raises:
        werkzeug.exceptions.NotFound: 文件不存在时抛出 404。
    """
    return send_from_directory(upload_dir(), filename)


# --------------------------------------------------------------------------- #
# 已移出导航的占位页面
# --------------------------------------------------------------------------- #


@charity_bp.get("/activities")
def activities() -> str:
    """公益活动页面（已移出导航，链接仍可访问）。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("公益活动"),
        page_desc=_("这里将展示近期公益活动安排与往期回顾。"),
    )


@charity_bp.get("/foster")
def foster() -> str:
    """寄养宠物页面（已移出导航，链接仍可访问）。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("寄养宠物"),
        page_desc=_("这里将介绍临时寄养家庭的申请与支持方案。"),
    )
