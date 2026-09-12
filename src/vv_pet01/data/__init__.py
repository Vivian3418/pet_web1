"""数据层包。

存放站点种子数据与受控词表常量。真正的数据访问由
:mod:`vv_pet01.services` 通过 SQLite 完成，本包仅提供初始数据来源，
使得更换数据源时无需改动业务与模板层。
"""

from __future__ import annotations

from vv_pet01.data.dogs import (
    AGE_GROUP_OPTIONS,
    CONTACT_OPTIONS,
    DISCUSSION_TOPIC_OPTIONS,
    DOGS,
    EXTRA_SERVICE_OPTIONS,
    GENDER_OPTIONS,
    PETS_AT_HOME_OPTIONS,
    SIZE_OPTIONS,
    SORT_OPTIONS,
    STATUS_ADOPTABLE,
    STATUS_OPTIONS,
    STATUS_SLUGS,
)
from vv_pet01.data.seed import build_seed_rows
from vv_pet01.data.shelters import SHELTERS

__all__ = [
    "AGE_GROUP_OPTIONS",
    "CONTACT_OPTIONS",
    "DISCUSSION_TOPIC_OPTIONS",
    "DOGS",
    "EXTRA_SERVICE_OPTIONS",
    "GENDER_OPTIONS",
    "PETS_AT_HOME_OPTIONS",
    "SHELTERS",
    "SIZE_OPTIONS",
    "SORT_OPTIONS",
    "STATUS_ADOPTABLE",
    "STATUS_OPTIONS",
    "STATUS_SLUGS",
    "build_seed_rows",
]
