"""待领养狗狗种子数据模块。

提供救助站在养的狗狗档案，作为 SQLite 数据库的初始种子数据来源，
并定义搜索表单所需的各类受控词表常量。

自由文本字段（呼名 / 简介）以中英成对形式提供；受控词表字段
（品种 / 性别 / 体型 / 状态 / 性格标签）以中文为规范值存储，
展示时通过 gettext 翻译，从而保证筛选条件与数据库取值一致。

Typical usage example::

    from vv_pet01.data.dogs import DOGS

    print(len(DOGS), DOGS[0]["name_en"])
"""

from __future__ import annotations

from typing import Any

#: 狗狗状态：可被领养。
STATUS_ADOPTABLE: str = "待领养"

#: 狗狗状态：领养申请审核中。
STATUS_PENDING: str = "审核中"

#: 狗狗状态：已完成领养。
STATUS_ADOPTED: str = "已领养"

#: 全部可选状态，顺序即前端下拉框展示顺序。
STATUS_OPTIONS: list[str] = [STATUS_ADOPTABLE, STATUS_PENDING, STATUS_ADOPTED]

#: 状态到 CSS 类名后缀的映射，避免在 HTML class 中直接使用中文。
STATUS_SLUGS: dict[str, str] = {
    STATUS_ADOPTABLE: "available",
    STATUS_PENDING: "pending",
    STATUS_ADOPTED: "adopted",
}

#: 体型选项，按由小到大排序。
SIZE_OPTIONS: list[str] = ["小型", "中型", "大型"]

#: 性别选项。
GENDER_OPTIONS: list[str] = ["公", "母"]

#: 年龄段选项：(查询值, 最小月龄, 最大月龄)。最大月龄为 ``None`` 表示不设上限。
AGE_GROUP_OPTIONS: list[tuple[str, int, int | None]] = [
    ("puppy", 0, 12),
    ("young", 12, 36),
    ("adult", 36, 84),
    ("senior", 84, None),
]

#: 排序选项值，展示文案由翻译目录提供。
SORT_OPTIONS: list[str] = ["distance", "latest", "age_asc", "name"]

#: 领养申请的联系偏好选项。
CONTACT_OPTIONS: list[str] = ["短信", "电话", "邮件"]

#: 家中现有宠物选项（参考 Adopters Welcome 问卷）。
PETS_AT_HOME_OPTIONS: list[str] = [
    "家中有狗",
    "家中有猫",
    "家中有小动物",
    "希望协助介绍新宠物与现有宠物认识",
    "家中没有饲养宠物",
]

#: 希望与救助站沟通的话题选项（对应问卷中的讨论清单）。
DISCUSSION_TOPIC_OPTIONS: list[str] = [
    "该宠物的喂养方式",
    "如厕 / 猫砂盆训练",
    "美容与修剪指甲",
    "运动、玩具与互动活动",
    "居家幼宠防护",
    "寻找训练师",
    "跳蚤与蜱虫预防",
    "心丝虫预防",
    "与新宠物介绍认识",
    "芯片与其他身份标识",
    "寻找兽医",
    "绝育手术",
    "笼内训练",
    "与新宠物介绍认识（儿童）",
    "基础训练",
    "兽医护理费用预估",
]

#: 额外服务与支持选项（对应问卷中的附加服务清单）。
EXTRA_SERVICE_OPTIONS: list[str] = [
    "为新领养宠物或家中宠物提供项圈与身份牌",
    "提供一袋该宠物正在食用的宠物粮",
    "告知基础宠物用品的购买地点",
    "本次领养可借用航空箱或运输笼",
    "下一次免费 / 低价疫苗接种活动信息",
    "下一次免费 / 低价芯片植入活动信息",
    "宠物食品援助站信息",
    "训练课程信息",
    "住房支持信息（含宠物押金与费用协助）",
    "免费 / 低价绝育及其他兽医服务信息",
    "志愿者或寄养家庭招募信息",
    "资金或实物捐赠支持方式信息",
]

#: 待领养狗狗种子数据列表。
#:
#: 每项字段含义如下：
#:
#: * ``id``: 狗狗唯一编号。
#: * ``name`` / ``name_en``: 呼名（中 / 英）。
#: * ``breed``: 品种（受控词表）。
#: * ``gender``: 性别（公 / 母）。
#: * ``age_months``: 月龄，用于年龄筛选与展示。
#: * ``size``: 体型（受控词表）。
#: * ``weight_kg``: 体重（千克）。
#: * ``shelter_id``: 所属救助站编号，关联 ``SHELTERS``。
#: * ``status``: 领养状态。
#: * ``vaccinated``: 是否已完成疫苗接种。
#: * ``neutered``: 是否已完成绝育。
#: * ``traits``: 性格标签（受控词表）。
#: * ``description`` / ``description_en``: 救助经历与性格描述（中 / 英）。
#: * ``image``: 展示图片地址。
#: * ``intake_date``: 入站日期（ISO 格式），用于「最新发布」排序。
DOGS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "豆豆",
        "name_en": "Doubao",
        "breed": "金毛寻回犬",
        "gender": "公",
        "age_months": 14,
        "size": "大型",
        "weight_kg": 26.5,
        "shelter_id": "SH001",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["亲人", "会握手", "安静"],
        "description": "因主人搬迁被送到救助站，性格极其温顺，喜欢趴在脚边陪人看书。",
        "description_en": (
            "Surrendered when his owner relocated. Extremely gentle and happiest "
            "lying at your feet while you read."
        ),
        "image": "https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-06-18",
    },
    {
        "id": 2,
        "name": "小满",
        "name_en": "Xiaoman",
        "breed": "中华田园犬",
        "gender": "母",
        "age_months": 8,
        "size": "中型",
        "weight_kg": 12.0,
        "shelter_id": "SH001",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": False,
        "traits": ["活泼", "亲人", "适合有孩子的家庭"],
        "description": "在小区门口被发现时还是奶狗，现已在救助站完成社会化训练。",
        "description_en": (
            "Found as a tiny puppy at a residential gate; has since completed "
            "socialisation training at the shelter."
        ),
        "image": "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-07-02",
    },
    {
        "id": 3,
        "name": "阿黄",
        "name_en": "Ahuang",
        "breed": "柴犬",
        "gender": "公",
        "age_months": 42,
        "size": "中型",
        "weight_kg": 11.5,
        "shelter_id": "SH001",
        "status": STATUS_PENDING,
        "vaccinated": True,
        "neutered": True,
        "traits": ["独立", "爱干净", "需要耐心"],
        "description": "性格偏独立，需要熟悉期，熟悉后会主动蹭手求抚摸。",
        "description_en": (
            "Fairly independent and needs a settling-in period, then happily nudges "
            "your hand for pets."
        ),
        "image": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-04-11",
    },
    {
        "id": 4,
        "name": "团子",
        "name_en": "Tuanzi",
        "breed": "比熊犬",
        "gender": "母",
        "age_months": 30,
        "size": "小型",
        "weight_kg": 6.2,
        "shelter_id": "SH001",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["黏人", "不掉毛", "适合公寓"],
        "description": "从繁殖场解救出来的狗狗，目前健康状况良好，非常适合公寓饲养。",
        "description_en": (
            "Rescued from a breeding facility. In good health now and ideally suited "
            "to apartment living."
        ),
        "image": "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-01",
    },
    {
        "id": 5,
        "name": "闪电",
        "name_en": "Shandian",
        "breed": "边境牧羊犬",
        "gender": "公",
        "age_months": 20,
        "size": "中型",
        "weight_kg": 18.4,
        "shelter_id": "SH002",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": False,
        "traits": ["聪明", "精力旺盛", "需要运动"],
        "description": "学习能力极强，已掌握坐下、趴下等基础指令，需要有运动空间的家庭。",
        "description_en": (
            "Exceptionally quick to learn — already knows sit and down. Needs a family "
            "with space to run."
        ),
        "image": "https://images.unsplash.com/photo-1503256207526-0d5d80fa2f47?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-07-20",
    },
    {
        "id": 6,
        "name": "奶糖",
        "name_en": "Naitang",
        "breed": "拉布拉多",
        "gender": "母",
        "age_months": 10,
        "size": "大型",
        "weight_kg": 21.0,
        "shelter_id": "SH002",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": False,
        "traits": ["贪吃", "友善", "喜欢玩水"],
        "description": "被遗弃在公园的幼犬，对人和狗都非常友好，正在学习牵引礼仪。",
        "description_en": (
            "Abandoned in a park as a puppy. Great with people and dogs, currently "
            "learning loose-leash manners."
        ),
        "image": "https://images.unsplash.com/photo-1561037404-61cd46aa615b?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-12",
    },
    {
        "id": 7,
        "name": "黑仔",
        "name_en": "Heizai",
        "breed": "德国牧羊犬",
        "gender": "公",
        "age_months": 66,
        "size": "大型",
        "weight_kg": 34.0,
        "shelter_id": "SH002",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["忠诚", "警觉", "沉稳"],
        "description": "退役工作犬，服从性极佳，适合有养犬经验且生活环境安静的家庭。",
        "description_en": (
            "A retired working dog with excellent obedience; best suited to an "
            "experienced owner in a quiet home."
        ),
        "image": "https://images.unsplash.com/photo-1589941013453-ec89f33b5e95?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-03-05",
    },
    {
        "id": 8,
        "name": "奶茶",
        "name_en": "Naicha",
        "breed": "泰迪犬",
        "gender": "母",
        "age_months": 26,
        "size": "小型",
        "weight_kg": 5.1,
        "shelter_id": "SH003",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["活泼", "亲人", "适合公寓"],
        "description": "在社区流浪时被志愿者救助，非常喜欢被抱，适合上班族陪伴。",
        "description_en": (
            "Rescued from the streets by volunteers. Loves being held and makes an "
            "ideal companion for office workers."
        ),
        "image": "https://images.unsplash.com/photo-1594149929911-78975a43d4f5?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-07-28",
    },
    {
        "id": 9,
        "name": "大白",
        "name_en": "Dabai",
        "breed": "萨摩耶",
        "gender": "公",
        "age_months": 38,
        "size": "大型",
        "weight_kg": 27.0,
        "shelter_id": "SH003",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["爱笑", "掉毛多", "友善"],
        "description": "因原家庭过敏被送养，性格开朗，需要定期梳理被毛。",
        "description_en": (
            "Surrendered because of a family member's allergy. Cheerful and needs "
            "regular coat brushing."
        ),
        "image": "https://images.unsplash.com/photo-1529429617124-95b109e86bb8?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-05-30",
    },
    {
        "id": 10,
        "name": "土豆",
        "name_en": "Tudou",
        "breed": "中华田园犬",
        "gender": "公",
        "age_months": 96,
        "size": "中型",
        "weight_kg": 15.0,
        "shelter_id": "SH003",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["安静", "不急躁", "适合养老家庭"],
        "description": "救助站里的「老大哥」，性格极其稳定，适合希望安静陪伴的家庭。",
        "description_en": (
            "The shelter's gentle 'big brother' with a rock-steady temperament — ideal "
            "for a quiet home."
        ),
        "image": "https://images.unsplash.com/photo-1477884213360-7e9d7dcc1e48?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-02-14",
    },
    {
        "id": 11,
        "name": "雪球",
        "name_en": "Xueqiu",
        "breed": "博美犬",
        "gender": "母",
        "age_months": 18,
        "size": "小型",
        "weight_kg": 3.8,
        "shelter_id": "SH003",
        "status": STATUS_PENDING,
        "vaccinated": True,
        "neutered": False,
        "traits": ["机警", "爱叫", "适合公寓"],
        "description": "体积小但气势足，对陌生人会叫，熟悉后非常黏主人。",
        "description_en": (
            "Small in size but big in confidence — barks at strangers and adores her "
            "person once settled."
        ),
        "image": "https://images.unsplash.com/photo-1560807707-8cc77767d783?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-06-25",
    },
    {
        "id": 12,
        "name": "阿福",
        "name_en": "Afu",
        "breed": "柯基犬",
        "gender": "公",
        "age_months": 22,
        "size": "小型",
        "weight_kg": 12.5,
        "shelter_id": "SH004",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["短腿", "精力旺盛", "爱撒娇"],
        "description": "因髋关节问题被弃养，现已康复，需控制体重并避免频繁上下楼梯。",
        "description_en": (
            "Surrendered due to a hip-joint condition. Now recovered; needs weight "
            "control and fewer stairs."
        ),
        "image": "https://images.unsplash.com/photo-1612536057832-2ff7ead58194?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-06",
    },
    {
        "id": 13,
        "name": "小黑",
        "name_en": "Xiaohei",
        "breed": "拉布拉多",
        "gender": "母",
        "age_months": 6,
        "size": "大型",
        "weight_kg": 14.0,
        "shelter_id": "SH004",
        "status": STATUS_ADOPTABLE,
        "vaccinated": False,
        "neutered": False,
        "traits": ["幼犬", "好奇心强", "需要陪伴"],
        "description": "台风天被救起的三月龄幼犬，需要耐心进行定点排便训练。",
        "description_en": (
            "Rescued as a twelve-week-old puppy during a typhoon; needs patient "
            "house-training."
        ),
        "image": "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-22",
    },
    {
        "id": 14,
        "name": "布丁",
        "name_en": "Buding",
        "breed": "比熊犬",
        "gender": "公",
        "age_months": 48,
        "size": "小型",
        "weight_kg": 6.8,
        "shelter_id": "SH004",
        "status": STATUS_ADOPTED,
        "vaccinated": True,
        "neutered": True,
        "traits": ["温顺", "不掉毛"],
        "description": "已由爱心家庭领养，档案保留用于回顾。",
        "description_en": "Already adopted by a loving family; this record is kept for reference.",
        "image": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-01-09",
    },
    {
        "id": 15,
        "name": "花卷",
        "name_en": "Huajuan",
        "breed": "柴犬",
        "gender": "母",
        "age_months": 33,
        "size": "中型",
        "weight_kg": 10.2,
        "shelter_id": "SH005",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["独立", "爱干净", "适合上班族"],
        "description": "自理能力强，独自在家时非常安静，适合白天不在家的上班族。",
        "description_en": (
            "Very self-sufficient and quiet when left alone — a great match for people "
            "who work during the day."
        ),
        "image": "https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-07-11",
    },
    {
        "id": 16,
        "name": "可乐",
        "name_en": "Kele",
        "breed": "哈士奇",
        "gender": "公",
        "age_months": 27,
        "size": "大型",
        "weight_kg": 24.0,
        "shelter_id": "SH005",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["话多", "精力旺盛", "需要围栏"],
        "description": "被多次退养的「拆家能手」，需要有经验且能提供充足运动的家庭。",
        "description_en": (
            "Returned several times for his demolition skills; needs an experienced "
            "home with plenty of exercise."
        ),
        "image": "https://images.unsplash.com/photo-1605568427561-40dd23c2acea?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-06-03",
    },
    {
        "id": 17,
        "name": "芝麻",
        "name_en": "Zhima",
        "breed": "中华田园犬",
        "gender": "母",
        "age_months": 4,
        "size": "小型",
        "weight_kg": 4.5,
        "shelter_id": "SH005",
        "status": STATUS_ADOPTABLE,
        "vaccinated": False,
        "neutered": False,
        "traits": ["幼犬", "黏人", "爱睡觉"],
        "description": "被人遗弃在纸箱里的奶狗，已完成体内外驱虫，等待合适的家庭。",
        "description_en": (
            "Found abandoned in a cardboard box. Dewormed and waiting for the right family."
        ),
        "image": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-28",
    },
    {
        "id": 18,
        "name": "将军",
        "name_en": "Jiangjun",
        "breed": "德国牧羊犬",
        "gender": "公",
        "age_months": 54,
        "size": "大型",
        "weight_kg": 32.0,
        "shelter_id": "SH006",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["服从性高", "警觉", "沉稳"],
        "description": "经训犬师评估具备良好服从性，适合有院落且愿意持续训练的家庭。",
        "description_en": (
            "Assessed by a trainer as highly obedient; suits a home with a yard and a "
            "commitment to training."
        ),
        "image": "https://images.unsplash.com/photo-1568572933382-74d440642117?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-05-16",
    },
    {
        "id": 19,
        "name": "棉花",
        "name_en": "Mianhua",
        "breed": "泰迪犬",
        "gender": "母",
        "age_months": 15,
        "size": "小型",
        "weight_kg": 4.9,
        "shelter_id": "SH006",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["黏人", "不掉毛", "爱撒娇"],
        "description": "前主人出国后被转送到救助站，非常依赖人，适合有较多陪伴时间的家庭。",
        "description_en": (
            "Rehomed after her owner emigrated. Very people-focused; suits a family "
            "with plenty of time."
        ),
        "image": "https://images.unsplash.com/photo-1591946614720-90a587da4a36?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-15",
    },
    {
        "id": 20,
        "name": "麦芽",
        "name_en": "Maiya",
        "breed": "金毛寻回犬",
        "gender": "母",
        "age_months": 90,
        "size": "大型",
        "weight_kg": 29.5,
        "shelter_id": "SH006",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["温和", "亲人", "适合养老家庭"],
        "description": "被原主人托付到救助站的老年犬，希望能找到愿意陪她走完后半生的家庭。",
        "description_en": (
            "A senior dog entrusted to the shelter, hoping to find a family for her "
            "golden years."
        ),
        "image": "https://images.unsplash.com/photo-1558788353-f76d92427f16?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-04-27",
    },
]
