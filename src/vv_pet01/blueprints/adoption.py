"""领养宠物板块蓝图模块。

对应顶部导航「领养宠物」，全部路由均带 ``<lang_code>`` 语言前缀：

* ``/adoption/pets``：合并后的宠物领养检索页（狗 / 猫 / 其他宠物统一检索）。
* ``/adoption/pets/<pet_id>``：宠物详情页。
* ``/adoption/pets/<pet_id>/apply``：领养申请表（GET 展示 / POST 提交）。
* ``/adoption/applications``：已提交申请列表。
* ``/adoption/applications/<application_id>``：申请提交成功回执。
* ``/adoption/process``：领养流程页。
* ``/adoption/dogs``、``/adoption/cats``、``/adoption/others``：旧入口，
  永久重定向到合并页并预选对应类别，保证历史链接仍可访问。
"""

from __future__ import annotations

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_babel import gettext as _

from vv_pet01.data.taxonomy import (
    COMPANION_OPTIONS,
    RADIUS_OPTIONS,
    STATUS_ADOPTABLE,
    STATUS_OPTIONS,
    breeds_for,
    shows_size,
)
from vv_pet01.forms import AdoptionApplicationForm
from vv_pet01.services.adoption import (
    DEFAULT_PER_PAGE,
    create_application,
    current_language,
    get_application,
    get_filter_options,
    get_pet_detail,
    list_applications,
    list_shelters,
    nearby_shelter_ids,
    paginate,
    resolve_reference,
    search_pets,
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


def _parse_radius(value: str | None) -> int:
    """解析搜索距离查询参数。

    Args:
        value: 原始距离字符串（千米）。

    Returns:
        合法的距离值；``0`` 或非法输入表示不限距离。
    """
    try:
        radius = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return radius if radius in RADIUS_OPTIONS else 0


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


def _collect_filters(args) -> dict[str, object]:  # noqa: ANN001
    """从查询参数中收集检索条件。

    Args:
        args: Flask 的 ``request.args`` 多值字典。

    Returns:
        与 :func:`vv_pet01.services.adoption.search_pets` 参数同名的检索字典。
    """
    return {
        "species": _clean(args.get("species")),
        "keyword": _clean(args.get("q")),
        "breed": _clean(args.get("breed")),
        "gender": _clean(args.get("gender")),
        "size": _clean(args.get("size")),
        "age_group": _clean(args.get("age")),
        "companions": [item for item in args.getlist("companion") if item in COMPANION_OPTIONS],
        "shelter_id": _clean(args.get("shelter")),
        "status": _clean(args.get("status")) or STATUS_ADOPTABLE,
    }


def _sanitize_filters(filters: dict[str, object]) -> list[str]:
    """清空与当前宠物类别不兼容的检索条件（就地修改）。

    切换类别时，原类别下选择的品种与体型对新类别无效，需要丢弃，
    否则会出现「选了猫却仍按犬类品种过滤」的空结果。

    Args:
        filters: 检索条件字典，会被就地修改。

    Returns:
        被清空的字段名称列表，供页面提示使用。
    """
    species = str(filters.get("species") or "")
    cleared: list[str] = []

    breed = str(filters.get("breed") or "")
    if breed and breed not in breeds_for(species):
        filters["breed"] = ""
        cleared.append("breed")

    if not shows_size(species) and filters.get("size"):
        filters["size"] = ""
        cleared.append("size")

    return cleared


def _location_params(
    origin: tuple[float, float] | None,
    city: str,
    radius: int,
) -> dict[str, object]:
    """构造用于在页面间保留定位与距离状态的查询参数。

    Args:
        origin: 用户定位坐标。
        city: 所在地（城市名称）。
        radius: 搜索距离（千米）。

    Returns:
        可直接展开传给 ``url_for`` 的参数字典。
    """
    params: dict[str, object] = {}
    if city:
        params["city"] = city
    if radius:
        params["radius"] = radius
    if origin is not None:
        params["lat"] = f"{origin[0]:.4f}"
        params["lng"] = f"{origin[1]:.4f}"
    return params


def _build_base_params(
    filters: dict[str, object],
    city: str,
    radius: int,
    sort: str,
    origin: tuple[float, float] | None,
) -> dict[str, object]:
    """构造用于生成分页链接的基础查询参数（不含 ``page``）。

    Args:
        filters: 当前生效的检索条件。
        city: 所在地。
        radius: 搜索距离。
        sort: 当前排序方式。
        origin: 用户定位坐标。

    Returns:
        可直接展开传给 ``url_for`` 的查询参数字典。
    """
    params: dict[str, object] = {}
    for key, value in (
        ("species", filters.get("species")),
        ("q", filters.get("keyword")),
        ("breed", filters.get("breed")),
        ("gender", filters.get("gender")),
        ("size", filters.get("size")),
        ("age", filters.get("age_group")),
        ("shelter", filters.get("shelter_id")),
    ):
        if value:
            params[key] = value
    companions = filters.get("companions") or []
    if companions:
        params["companion"] = list(companions)  # type: ignore[arg-type]
    if filters.get("status") != STATUS_ADOPTABLE:
        params["status"] = filters.get("status")
    if sort:
        params["sort"] = sort
    params.update(_location_params(origin, city, radius))
    return params


@adoption_bp.get("/pets")
def pets() -> str:
    """宠物领养检索页（狗 / 猫 / 其他宠物统一检索）。

    检索流程：所在地 + 搜索距离确定附近救助站，宠物类别决定可选品种与
    是否展示体型，相处对象支持多选。切换类别时自动清空无效条件。

    Returns:
        检索页模板渲染后的 HTML 字符串。
    """
    filters = _collect_filters(request.args)
    cleared = _sanitize_filters(filters)

    city = _clean(request.args.get("city"))
    radius = _parse_radius(request.args.get("radius"))
    origin = _parse_origin(request.args)
    reference = resolve_reference(city, origin)
    # 未选择所在地且未定位时，距离条件无法计算，按不限距离处理
    if reference is None:
        radius = 0

    shelter_ids = nearby_shelter_ids(reference, radius)

    # 侧栏选定救助站时，与半径结果取交集（未选则沿用半径结果）
    selected_shelter = str(filters.get("shelter_id") or "")
    if selected_shelter:
        if shelter_ids is None or selected_shelter in shelter_ids:
            shelter_ids = [selected_shelter]
        else:
            shelter_ids = []

    species = str(filters.get("species") or "")
    requested_sort = _clean(request.args.get("sort"))
    resolved_sort = requested_sort or ("distance" if reference else "latest")
    if resolved_sort == "distance" and reference is None:
        resolved_sort = "latest"

    # shelter_id 仅用于侧栏高亮与交集计算，检索函数使用 shelter_ids
    search_filters = {key: value for key, value in filters.items() if key != "shelter_id"}
    results = search_pets(
        **search_filters,  # type: ignore[arg-type]
        shelter_ids=shelter_ids,
        reference=reference,
        sort=resolved_sort,
    )
    pagination = paginate(results, _parse_page(request.args.get("page")), DEFAULT_PER_PAGE)
    filter_options = get_filter_options(species)

    return render_template(
        "adoption/pets.html",
        page_title=_("领养宠物"),
        page_desc=_("先选择所在地与搜索距离，再选择宠物类别，即可按品种、性格与家庭适配度筛选。"),
        pagination=pagination,
        shelters=list_shelters(filters, reference=reference, radius_km=radius),
        filters=filters,
        species=species,
        filter_options=filter_options,
        status_options=STATUS_OPTIONS,
        sort_options=filter_options["sorts"],
        city=city,
        radius=radius,
        origin=origin,
        reference=reference,
        sort=resolved_sort,
        cleared=cleared,
        base_params=_build_base_params(filters, city, radius, resolved_sort, origin),
        location_params=_location_params(origin, city, radius),
        radius_options=RADIUS_OPTIONS,
    )


@adoption_bp.get("/pets/<int:pet_id>")
def pet_detail(pet_id: int) -> str:
    """宠物详情页。

    Args:
        pet_id: 路径参数中的宠物编号。

    Returns:
        宠物详情模板渲染后的 HTML 字符串。

    Raises:
        werkzeug.exceptions.NotFound: 当宠物编号不存在时抛出 404。
    """
    city = _clean(request.args.get("city"))
    radius = _parse_radius(request.args.get("radius"))
    origin = _parse_origin(request.args)
    reference = resolve_reference(city, origin)

    pet = get_pet_detail(pet_id, reference=reference)
    if pet is None:
        abort(404)

    return render_template(
        "adoption/pet_detail.html",
        page_title=pet["name"],
        pet=pet,
        origin=origin,
        location_params=_location_params(origin, city, radius),
    )


@adoption_bp.route("/pets/<int:pet_id>/apply", methods=["GET", "POST"])
def apply(pet_id: int):
    """领养申请表页面。

    ``GET`` 渲染预填了宠物信息的申请表；``POST`` 校验并写入数据库，
    成功后重定向到申请回执页（PRG 模式，避免刷新重复提交）。

    Args:
        pet_id: 路径参数中的宠物编号。

    Returns:
        GET 请求返回表单页 HTML；POST 成功返回 302 重定向。

    Raises:
        werkzeug.exceptions.NotFound: 当宠物编号不存在时抛出 404。
    """
    city = _clean(request.args.get("city"))
    radius = _parse_radius(request.args.get("radius"))
    origin = _parse_origin(request.args)
    reference = resolve_reference(city, origin)

    pet = get_pet_detail(pet_id, reference=reference)
    if pet is None:
        abort(404)

    form = AdoptionApplicationForm()

    if request.method == "GET":
        # 从详情页进入时预填宠物呼名，减少重复输入
        form.animal_name.data = pet["name"]

    if form.validate_on_submit():
        payload = form.to_payload()
        payload.update(
            {
                "pet_id": pet["id"],
                "pet_name": pet["name_zh"],
                "pet_name_en": pet["name_en"],
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
        pet=pet,
        form=form,
        origin=origin,
        location_params=_location_params(origin, city, radius),
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


def _legacy_redirect(species: str):
    """构造旧入口到合并检索页的永久重定向。

    Args:
        species: 需要预设的宠物类别。

    Returns:
        302/301 重定向响应。
    """
    return redirect(url_for("adoption.pets", species=species), code=301)


@adoption_bp.get("/dogs")
def legacy_dogs():
    """旧「领养狗狗」入口，重定向到合并检索页（预选狗）。"""
    return _legacy_redirect("狗")


@adoption_bp.get("/cats")
def legacy_cats():
    """旧「领养猫咪」入口，重定向到合并检索页（预选猫）。"""
    return _legacy_redirect("猫")


@adoption_bp.get("/others")
def legacy_others():
    """旧「其他宠物」入口，重定向到合并检索页（预选其他宠物）。"""
    return _legacy_redirect("其他宠物")
