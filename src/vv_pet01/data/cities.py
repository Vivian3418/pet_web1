"""城市中心坐标模块。

用户只需选择「所在地」即可按城市中心计算与各救助站的距离，再叠加
「搜索距离」筛选出附近救助站；无需授权浏览器定位也能使用距离检索。
若用户授权定位，则以实际坐标覆盖城市中心。

Typical usage example::

    from vv_pet01.data.cities import city_center

    print(city_center("上海市"))
"""

from __future__ import annotations

from typing import NamedTuple


class CityCenter(NamedTuple):
    """城市中心参考点。

    Attributes:
        name: 城市名称（中文规范值，展示时翻译）。
        lat: 中心点纬度。
        lng: 中心点经度。
    """

    name: str
    lat: float
    lng: float


#: 有合作救助站覆盖的城市及其中心坐标，顺序即下拉框展示顺序。
CITIES: tuple[CityCenter, ...] = (
    CityCenter("上海市", 31.2304, 121.4737),
    CityCenter("北京市", 39.9042, 116.4074),
    CityCenter("广州市", 23.1291, 113.2644),
    CityCenter("成都市", 30.5728, 104.0668),
    CityCenter("杭州市", 30.2741, 120.1551),
)

#: 城市名称到中心坐标的索引。
_CITY_INDEX: dict[str, CityCenter] = {city.name: city for city in CITIES}


def city_center(name: str) -> CityCenter | None:
    """查询城市中心坐标。

    Args:
        name: 城市名称。

    Returns:
        对应的城市中心；未收录时返回 ``None``。
    """
    return _CITY_INDEX.get(name)


def city_names() -> list[str]:
    """列出全部可选城市名称。

    Returns:
        城市名称列表，顺序与 :data:`CITIES` 一致。
    """
    return [city.name for city in CITIES]


def city_center_from_text(text: str) -> CityCenter | None:
    """从自由文本地址中推断城市并返回其中心坐标。

    演示项目未接入地理编码服务，因此采用「城市名匹配」的方式把用户输入的
    地址粗定位到城市级别，足以支撑「显示最近救助站与距离」的演示需求。

    Args:
        text: 用户输入的地址文本。

    Returns:
        匹配到的城市中心；无法识别时返回 ``None``。
    """
    if not text:
        return None

    for city in CITIES:
        # 同时匹配带「市」的全称与去掉「市」的简称（如「上海」）
        short_name = city.name.rstrip("市")
        if city.name in text or (short_name and short_name in text):
            return city
    return None
