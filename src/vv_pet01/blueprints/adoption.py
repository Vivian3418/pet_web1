"""领养宠物板块蓝图模块。

对应顶部导航「领养宠物」下拉菜单，全部路由均带 ``<lang_code>`` 语言前缀：

* ``/adoption/dogs``：领养狗狗搜索页（关键词、品种、体型、年龄、城市、
  救助站筛选，并可按「附近救助站」排序）。
* ``/adoption/dogs/<dog_id>``：狗狗详情页。
* ``/adoption/dogs/<dog_id>/apply``：领养申请表（GET 展示 / POST 提交）。
* ``/adoption/applications``：已提交申请列表。
* ``/adoption/applications/<application_id>``：申请提交成功回执。
* ``/adoption/cats``、``/adoption/others``、``/adoption/process``：占位页面。
"""

from __future__ import annotations

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_babel import gettext as _

from vv_pet01.data.dogs import STATUS_ADOPTABLE, STATUS_OPTIONS
from vv_pet01.forms import AdoptionApplicationForm
from vv_pet01.services.adoption import (
    DEFAULT_PER_PAGE,
    create_application,
    current_language,
    get_application,
    get_dog_detail,
    get_filter_options,
    list_applications,
    list_shelters,
    paginate,
    search_dogs,
)

adoption_bp = Blueprint("adoption", __name__, url_prefix="/<lang_code>/adoption")

#: 申请列表页单页展示条数。
_APPLICATIONS_PER_PAGE: int = 20


def _clean(value: str | None) -> str:
    """去除查询参数的首尾空白。

    Args:
        value: 原始查询参数值，可能为 ``None``。

    Returns:
        去除空白后的字符串；输入为 ``None`` 时返回空字符串。
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


def _parse_origin(args) -> tuple[float, float] | None:  # noqa: ANN001
    """从查询参数中解析用户当前位置。

    Args:
        args: Flask 的 ``request.args`` 多值字典。

    Returns:
        ``(纬度, 经度)`` 元组；缺少参数或数值非法时返回 ``None``。
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


def _collect_filters(args) -> dict[str, str]:  # noqa: ANN001
    """从查询参数中收集筛选条件。

    Args:
        args: Flask 的 ``request.args`` 多值字典。

    Returns:
        与 :func:`vv_pet01.services.adoption.search_dogs` 参数同名的筛选字典。
    """
    return {
        "keyword": _clean(args.get("q")),
        "breed": _clean(args.get("breed")),
        "gender": _clean(args.get("gender")),
        "size": _clean(args.get("size")),
        "age_group": _clean(args.get("age")),
        "city": _clean(args.get("city")),
        "shelter_id": _clean(args.get("shelter")),
        "status": _clean(args.get("status")) or STATUS_ADOPTABLE,
    }


def _build_base_params(
    filters: dict[str, str],
    sort: str,
    origin: tuple[float, float] | None,
) -> dict[str, str]:
    """构造用于生成分页链接的基础查询参数（不含 ``page``）。

    Args:
        filters: 当前生效的筛选条件。
        sort: 当前排序方式。
        origin: 用户当前位置。

    Returns:
        可直接展开传给 ``url_for`` 的查询参数字典。
    """
    params: dict[str, str] = {}
    for key, value in (
        ("q", filters["keyword"]),
        ("breed", filters["breed"]),
        ("gender", filters["gender"]),
        ("size", filters["size"]),
        ("age", filters["age_group"]),
        ("city", filters["city"]),
        ("shelter", filters["shelter_id"]),
    ):
        if value:
            params[key] = value
    if filters["status"] != STATUS_ADOPTABLE:
        params["status"] = filters["status"]
    if sort:
        params["sort"] = sort
    if origin is not None:
        params["lat"] = f"{origin[0]:.4f}"
        params["lng"] = f"{origin[1]:.4f}"
    return params


def _location_params(origin: tuple[float, float] | None) -> dict[str, str]:
    """构造仅包含定位信息的查询参数，用于在页面间保留定位状态。

    Args:
        origin: 用户当前位置。

    Returns:
        ``{"lat": ..., "lng": ...}``；未定位时为空字典。
    """
    if origin is None:
        return {}
    return {"lat": f"{origin[0]:.4f}", "lng": f"{origin[1]:.4f}"}


@adoption_bp.get("/dogs")
def dogs() -> str:
    """领养狗狗搜索页。

    解析查询参数并完成筛选、距离排序与分页，渲染搜索结果与附近救助站列表。

    Returns:
        狗狗搜索页模板渲染后的 HTML 字符串。
    """
    filters = _collect_filters(request.args)
    origin = _parse_origin(request.args)

    requested_sort = _clean(request.args.get("sort"))
    resolved_sort = requested_sort or ("distance" if origin else "latest")
    # 未选择坐标时无法按距离排序，回退为最新发布
    if resolved_sort == "distance" and origin is None:
        resolved_sort = "latest"

    results = search_dogs(**filters, origin=origin, sort=resolved_sort)
    pagination = paginate(results, _parse_page(request.args.get("page")), DEFAULT_PER_PAGE)
    filter_options = get_filter_options()

    return render_template(
        "adoption/dogs.html",
        page_title=_("领养狗狗"),
        page_desc=_("按品种、体型、年龄与所在城市筛选，或开启定位查找离你最近的救助站。"),
        pagination=pagination,
        shelters=list_shelters(filters, origin=origin),
        filters=filters,
        filter_options=filter_options,
        status_options=STATUS_OPTIONS,
        sort_options=filter_options["sorts"],
        origin=origin,
        sort=resolved_sort,
        base_params=_build_base_params(filters, resolved_sort, origin),
        location_params=_location_params(origin),
    )


@adoption_bp.get("/dogs/<int:dog_id>")
def dog_detail(dog_id: int) -> str:
    """狗狗详情页。

    Args:
        dog_id: 路径参数中的狗狗编号。

    Returns:
        狗狗详情模板渲染后的 HTML 字符串。

    Raises:
        werkzeug.exceptions.NotFound: 当狗狗编号不存在时抛出 404。
    """
    origin = _parse_origin(request.args)
    dog = get_dog_detail(dog_id, origin=origin)
    if dog is None:
        abort(404)

    return render_template(
        "adoption/dog_detail.html",
        page_title=dog["name"],
        dog=dog,
        origin=origin,
        location_params=_location_params(origin),
    )


@adoption_bp.route("/dogs/<int:dog_id>/apply", methods=["GET", "POST"])
def apply(dog_id: int):
    """领养申请表页面。

    ``GET`` 渲染预填了狗狗信息的申请表；``POST`` 校验并写入数据库，
    成功后重定向到申请回执页（PRG 模式，避免刷新重复提交）。

    Args:
        dog_id: 路径参数中的狗狗编号。

    Returns:
        GET 请求返回表单页 HTML；POST 成功返回 302 重定向。

    Raises:
        werkzeug.exceptions.NotFound: 当狗狗编号不存在时抛出 404。
    """
    origin = _parse_origin(request.args)
    dog = get_dog_detail(dog_id, origin=origin)
    if dog is None:
        abort(404)

    form = AdoptionApplicationForm()

    if request.method == "GET":
        # 从详情页进入时预填动物呼名，减少重复输入
        form.animal_name.data = dog["name"]

    if form.validate_on_submit():
        payload = form.to_payload()
        payload.update(
            {
                "dog_id": dog["id"],
                "dog_name": dog["name_zh"],
                "dog_name_en": dog["name_en"],
                "locale": current_language(),
            }
        )
        created = create_application(payload)
        return redirect(
            url_for("adoption.application_detail", application_id=created["id"])
        )

    return render_template(
        "adoption/apply.html",
        page_title=_("领养申请表"),
        page_desc=_("请如实填写以下信息，救助站会据此与你联系并安排后续沟通。"),
        dog=dog,
        form=form,
        origin=origin,
        location_params=_location_params(origin),
    )


@adoption_bp.get("/applications")
def applications() -> str:
    """已提交的领养申请列表页。

    Returns:
        申请列表模板渲染后的 HTML 字符串。
    """
    page = _parse_page(request.args.get("page"))
    all_records = list_applications(limit=500)
    pagination = paginate(all_records, page, _APPLICATIONS_PER_PAGE)

    return render_template(
        "adoption/applications.html",
        page_title=_("领养申请记录"),
        page_desc=_("这里展示本站收到的全部领养申请，可用于查看已提交记录。"),
        pagination=pagination,
        base_params={},
    )


@adoption_bp.get("/applications/<int:application_id>")
def application_detail(application_id: int) -> str:
    """领养申请回执页。

    Args:
        application_id: 申请记录主键。

    Returns:
        申请回执模板渲染后的 HTML 字符串。

    Raises:
        werkzeug.exceptions.NotFound: 当申请记录不存在时抛出 404。
    """
    application = get_application(application_id)
    if application is None:
        abort(404)

    return render_template(
        "adoption/apply_success.html",
        page_title=_("申请已提交"),
        page_desc=_("我们已收到你的领养申请，救助站会尽快与你联系。"),
        application=application,
    )


@adoption_bp.get("/cats")
def cats() -> str:
    """领养猫咪页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("领养猫咪"),
        page_desc=_("这里将展示等待领养的猫咪信息与领养条件。"),
    )


@adoption_bp.get("/others")
def others() -> str:
    """其他宠物领养页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("其他宠物"),
        page_desc=_("这里将展示兔子、鸟类等小动物的领养信息。"),
    )


@adoption_bp.get("/process")
def process() -> str:
    """领养流程说明页面。

    Returns:
        通用占位模板渲染后的 HTML 字符串。
    """
    return render_template(
        "page.html",
        page_title=_("领养流程"),
        page_desc=_("这里将介绍从申请、审核到交接的完整领养流程。"),
    )
