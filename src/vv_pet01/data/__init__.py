"""数据层包。

存放站点种子数据（救助站、宠物）与受控词表常量。真正的数据访问由
:mod:`vv_pet01.services` 通过 SQLite 完成，本包仅提供初始数据来源，
使得更换数据源时无需改动业务与模板层。
"""

from __future__ import annotations

from vv_pet01.data.cities import CITIES, CityCenter, city_center, city_names
from vv_pet01.data.pets import PETS
from vv_pet01.data.seed import build_seed_rows
from vv_pet01.data.shelters import SHELTERS
from vv_pet01.data.stories import STORY_IMAGES, story_image
from vv_pet01.data.taxonomy import (
    AGE_GROUP_OPTIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    ALL_BREEDS,
    BREEDS_BY_SPECIES,
    COMPANION_OPTIONS,
    CONTACT_OPTIONS,
    DISCUSSION_TOPIC_OPTIONS,
    DONATION_AMOUNTS,
    DONATION_DESIGNATION_OPTIONS,
    DONATION_FREQUENCY_OPTIONS,
    EXTRA_SERVICE_OPTIONS,
    GENDER_OPTIONS,
    MAX_IMAGE_BYTES,
    PETS_AT_HOME_OPTIONS,
    RADIUS_OPTIONS,
    RESCUE_ANIMAL_OPTIONS,
    RESCUE_HANDLING_OPTIONS,
    RESCUE_SITUATION_OPTIONS,
    RESCUE_STATUS_OPTIONS,
    RESCUE_STATUS_SLUGS,
    RESCUE_URGENCY_OPTIONS,
    SIZE_OPTIONS,
    SORT_OPTIONS,
    SPECIES_OPTIONS,
    STATUS_ADOPTABLE,
    STATUS_OPTIONS,
    STATUS_SLUGS,
    VOLUNTEER_AVAILABILITY_OPTIONS,
    VOLUNTEER_COMMITMENT_OPTIONS,
    VOLUNTEER_SKILL_OPTIONS,
    VOLUNTEER_TASK_OPTIONS,
    age_group_range,
    breeds_for,
    shows_size,
)

__all__ = [
    "AGE_GROUP_OPTIONS",
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALL_BREEDS",
    "BREEDS_BY_SPECIES",
    "CITIES",
    "COMPANION_OPTIONS",
    "CONTACT_OPTIONS",
    "DISCUSSION_TOPIC_OPTIONS",
    "DONATION_AMOUNTS",
    "DONATION_DESIGNATION_OPTIONS",
    "DONATION_FREQUENCY_OPTIONS",
    "EXTRA_SERVICE_OPTIONS",
    "GENDER_OPTIONS",
    "MAX_IMAGE_BYTES",
    "PETS",
    "PETS_AT_HOME_OPTIONS",
    "RADIUS_OPTIONS",
    "RESCUE_ANIMAL_OPTIONS",
    "RESCUE_HANDLING_OPTIONS",
    "RESCUE_SITUATION_OPTIONS",
    "RESCUE_STATUS_OPTIONS",
    "RESCUE_STATUS_SLUGS",
    "RESCUE_URGENCY_OPTIONS",
    "SHELTERS",
    "SIZE_OPTIONS",
    "SORT_OPTIONS",
    "SPECIES_OPTIONS",
    "STATUS_ADOPTABLE",
    "STATUS_OPTIONS",
    "STATUS_SLUGS",
    "STORY_IMAGES",
    "VOLUNTEER_AVAILABILITY_OPTIONS",
    "VOLUNTEER_COMMITMENT_OPTIONS",
    "VOLUNTEER_SKILL_OPTIONS",
    "VOLUNTEER_TASK_OPTIONS",
    "CityCenter",
    "age_group_range",
    "breeds_for",
    "build_seed_rows",
    "city_center",
    "city_names",
    "shows_size",
    "story_image",
]
