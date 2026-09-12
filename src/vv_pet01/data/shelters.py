"""救助站种子数据模块。

提供合作救助站的档案信息，作为 SQLite 数据库的初始种子数据来源，
包含所在城市、详细地址与经纬度坐标。经纬度用于「附近救助站」距离计算。

自由文本字段（名称 / 地址 / 简介）以中英成对形式提供；城市与区县属于
受控词表，以中文为规范值存储，展示时通过 gettext 翻译。

Typical usage example::

    from vv_pet01.data.shelters import SHELTERS

    print(SHELTERS[0]["name_en"])
"""

from __future__ import annotations

from typing import Any

#: 救助站种子数据列表。
#:
#: 每项字段含义如下：
#:
#: * ``id``: 救助站唯一编号。
#: * ``name`` / ``name_en``: 救助站名称（中 / 英）。
#: * ``city`` / ``district``: 所在城市与区县（受控词表，中文规范值）。
#: * ``address`` / ``address_en``: 详细地址（中 / 英）。
#: * ``phone``: 联系电话。
#: * ``lat`` / ``lng``: 纬度与经度，用于计算与用户当前位置的直线距离。
#: * ``founded_year``: 成立年份。
#: * ``description`` / ``description_en``: 救助站简介（中 / 英）。
SHELTERS: list[dict[str, Any]] = [
    {
        "id": "SH001",
        "name": "暖阳流浪动物救助站",
        "name_en": "Warm Sun Stray Animal Rescue",
        "city": "上海市",
        "district": "闵行区",
        "address": "上海市闵行区华漕镇纪王路 128 号",
        "address_en": "No. 128 Jiwang Road, Huacao Town, Minhang District, Shanghai",
        "phone": "021-6000 1001",
        "lat": 31.2135,
        "lng": 121.3201,
        "founded_year": 2014,
        "description": "专注流浪犬只救助与康复训练，设有独立犬舍与户外活动场。",
        "description_en": (
            "Specialises in rescuing and rehabilitating stray dogs, with separate "
            "kennels and an outdoor play yard."
        ),
    },
    {
        "id": "SH002",
        "name": "浦江小动物之家",
        "name_en": "Pujiang Small Animal Home",
        "city": "上海市",
        "district": "浦东新区",
        "address": "上海市浦东新区周浦镇康新公路 356 号",
        "address_en": "No. 356 Kangxin Highway, Zhoupu Town, Pudong New Area, Shanghai",
        "phone": "021-6000 1002",
        "lat": 31.1052,
        "lng": 121.6038,
        "founded_year": 2017,
        "description": "以社区共建模式运营，提供流浪犬临时安置与领养匹配服务。",
        "description_en": (
            "Runs on a community co-building model, offering temporary shelter and "
            "adoption matching for stray dogs."
        ),
    },
    {
        "id": "SH003",
        "name": "京北动物救助中心",
        "name_en": "Jingbei Animal Rescue Centre",
        "city": "北京市",
        "district": "昌平区",
        "address": "北京市昌平区回龙观北清路 88 号",
        "address_en": "No. 88 Beiqing Road, Huilongguan, Changping District, Beijing",
        "phone": "010-8000 2001",
        "lat": 40.1009,
        "lng": 116.2365,
        "founded_year": 2012,
        "description": "华北地区规模较大的公益救助机构，具备完善的犬只医疗与寄养条件。",
        "description_en": (
            "One of North China's larger non-profit rescue organisations, with full "
            "veterinary and boarding facilities."
        ),
    },
    {
        "id": "SH004",
        "name": "云山流浪动物驿站",
        "name_en": "Yunshan Stray Animal Station",
        "city": "广州市",
        "district": "白云区",
        "address": "广州市白云区太和镇兴太三路 26 号",
        "address_en": "No. 26 Xingtai Third Road, Taihe Town, Baiyun District, Guangzhou",
        "phone": "020-7000 3001",
        "lat": 23.2985,
        "lng": 113.3712,
        "founded_year": 2016,
        "description": "华南地区志愿者联合救助站点，长期开展领养日与社区科普活动。",
        "description_en": (
            "A volunteer-run rescue station in South China that hosts regular adoption "
            "days and community outreach."
        ),
    },
    {
        "id": "SH005",
        "name": "锦江小动物保护站",
        "name_en": "Jinjiang Small Animal Protection Station",
        "city": "成都市",
        "district": "温江区",
        "address": "成都市温江区公平街道花都大道 199 号",
        "address_en": (
            "No. 199 Huadu Avenue, Gongping Subdistrict, Wenjiang District, Chengdu"
        ),
        "phone": "028-6000 4001",
        "lat": 30.6821,
        "lng": 103.8553,
        "founded_year": 2018,
        "description": "以「领养代替购买」为宗旨，提供犬只行为评估与新手家庭指导。",
        "description_en": (
            "Dedicated to 'adopt, don't shop', offering behaviour assessments and "
            "guidance for first-time adopters."
        ),
    },
    {
        "id": "SH006",
        "name": "西湖宠物公益之家",
        "name_en": "West Lake Pet Charity Home",
        "city": "杭州市",
        "district": "余杭区",
        "address": "杭州市余杭区良渚街道古墩路 1200 号",
        "address_en": "No. 1200 Gudun Road, Liangzhu Subdistrict, Yuhang District, Hangzhou",
        "phone": "0571-9000 5001",
        "lat": 30.4189,
        "lng": 120.0008,
        "founded_year": 2019,
        "description": "主打家庭式寄养与短期救助，注重犬只社会化训练。",
        "description_en": (
            "Focuses on family-style fostering and short-term rescue, with an emphasis "
            "on socialisation training."
        ),
    },
]
