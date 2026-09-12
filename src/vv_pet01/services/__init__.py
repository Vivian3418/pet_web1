"""业务服务层包。

承载跨蓝图复用的查询与业务逻辑，隔离数据来源与展示层。
"""

from __future__ import annotations

from vv_pet01.services.adoption import (
    APPLICATION_STATUS_LABELS,
    DEFAULT_PER_PAGE,
    count_dogs,
    create_application,
    current_language,
    format_age,
    get_application,
    get_dog_detail,
    get_filter_options,
    haversine_km,
    list_applications,
    list_shelters,
    list_stories,
    paginate,
    search_dogs,
)

__all__ = [
    "APPLICATION_STATUS_LABELS",
    "DEFAULT_PER_PAGE",
    "count_dogs",
    "create_application",
    "current_language",
    "format_age",
    "get_application",
    "get_dog_detail",
    "get_filter_options",
    "haversine_km",
    "list_applications",
    "list_shelters",
    "list_stories",
    "paginate",
    "search_dogs",
]
