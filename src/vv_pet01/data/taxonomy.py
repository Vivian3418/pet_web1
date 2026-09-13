"""宠物分类词表模块。

集中维护「宠物类别 / 品种 / 性别 / 体型 / 年龄段 / 领养状态 / 相处对象 /
搜索距离」等受控词表，供检索联动、表单选项与展示翻译复用。

所有词表取值均以中文作为规范值（与数据库存储一致），展示时通过 gettext
翻译；品种按类别分组，用于实现「选择狗只显示犬类品种、选择猫只显示猫类
品种」的联动效果。

Typical usage example::

    from vv_pet01.data.taxonomy import BREEDS_BY_SPECIES

    print(BREEDS_BY_SPECIES["狗"])
"""

from __future__ import annotations

#: 宠物类别选项（狗 / 猫 / 其他宠物）。
SPECIES_OPTIONS: list[str] = ["狗", "猫", "其他宠物"]

#: 不展示「体型」筛选的类别：体型仅对狗有意义。
NON_DOG_SPECIES: tuple[str, ...] = ("猫", "其他宠物")

#: 类别到品种列表的映射，用于实现品种与类别的联动。
BREEDS_BY_SPECIES: dict[str, list[str]] = {
    "狗": [
        "金毛寻回犬",
        "拉布拉多",
        "德国牧羊犬",
        "边境牧羊犬",
        "中华田园犬",
        "柴犬",
        "柯基犬",
        "萨摩耶",
        "哈士奇",
        "比熊犬",
        "泰迪犬",
        "博美犬",
    ],
    "猫": [
        "中华田园猫",
        "英国短毛猫",
        "美国短毛猫",
        "布偶猫",
        "暹罗猫",
        "橘猫",
        "奶牛猫",
        "波斯猫",
    ],
    "其他宠物": ["垂耳兔", "侏儒兔", "虎皮鹦鹉", "玄凤鹦鹉"],
}

#: 全部品种（按类别顺序展开）。
ALL_BREEDS: list[str] = [breed for breeds in BREEDS_BY_SPECIES.values() for breed in breeds]

#: 性别选项。
GENDER_OPTIONS: list[str] = ["公", "母"]

#: 体型选项（仅对狗生效），按由小到大排序。
SIZE_OPTIONS: list[str] = ["小型", "中型", "大型"]

#: 领养状态：可被领养。
STATUS_ADOPTABLE: str = "待领养"

#: 领养状态：领养申请审核中。
STATUS_PENDING: str = "审核中"

#: 领养状态：已完成领养。
STATUS_ADOPTED: str = "已领养"

#: 全部可选状态，顺序即前端下拉框展示顺序。
STATUS_OPTIONS: list[str] = [STATUS_ADOPTABLE, STATUS_PENDING, STATUS_ADOPTED]

#: 状态到 CSS 类名后缀的映射，避免在 HTML class 中直接使用中文。
STATUS_SLUGS: dict[str, str] = {
    STATUS_ADOPTABLE: "available",
    STATUS_PENDING: "pending",
    STATUS_ADOPTED: "adopted",
}

#: 年龄段选项：(查询值, 展示文案 msgid, 最小月龄, 最大月龄)。
#: 最大月龄为 ``None`` 表示不设上限。
AGE_GROUP_OPTIONS: list[tuple[str, str, int, int | None]] = [
    ("baby", "一岁以下", 0, 12),
    ("young", "一至三岁", 12, 36),
    ("adult", "三至七岁", 36, 84),
    ("senior", "七岁以上", 84, None),
]

#: 排序选项值，展示文案由翻译目录提供。
SORT_OPTIONS: list[str] = ["distance", "latest", "age_asc", "name"]

#: 「适合与哪些对象相处」多选项，用于筛选家庭适配度。
COMPANION_OPTIONS: list[str] = [
    "适合有孩子的家庭",
    "适合与其他狗相处",
    "适合与其他猫相处",
    "适合上班族（长时间独处）",
    "适合老年家庭",
]

#: 搜索距离档位（千米），用于从参考点筛选附近救助站。
RADIUS_OPTIONS: list[int] = [5, 10, 25, 50, 100]

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

# --------------------------------------------------------------------------- #
# 动物救助（参与公益 → 动物救助）
# --------------------------------------------------------------------------- #

#: 待救助动物的类别选项（在宠物类别基础上增加「不确定」，便于无法判断时提交）。
RESCUE_ANIMAL_OPTIONS: list[str] = ["狗", "猫", "其他宠物", "不确定"]

#: 可救助的情形说明，同时也是表单中的「情况」选项。
RESCUE_SITUATION_OPTIONS: list[str] = [
    "被遗弃",
    "受伤",
    "生病",
    "被困求助",
    "疑似遭受虐待",
    "幼崽失去母兽",
]

#: 紧急程度选项。
RESCUE_URGENCY_OPTIONS: list[str] = [
    "情况紧急（需立即处理）",
    "情况较急（24 小时内）",
    "情况稳定（可安排时间）",
]

#: 处理方式选项：自行送往救助站，或申请工作人员前往救助。
RESCUE_HANDLING_OPTIONS: list[str] = [
    "我会送到最近的救助站",
    "请安排工作人员前来救助",
]

#: 救助工单状态规范值，顺序即流程顺序。
RESCUE_STATUS_PENDING: str = "未被救助"
RESCUE_STATUS_IN_PROGRESS: str = "正在救助中"
RESCUE_STATUS_RESCUED: str = "救助成功"

#: 全部救助状态，顺序即流程顺序。
RESCUE_STATUS_OPTIONS: list[str] = [
    RESCUE_STATUS_PENDING,
    RESCUE_STATUS_IN_PROGRESS,
    RESCUE_STATUS_RESCUED,
]

#: 救助状态到 CSS 类名后缀的映射，避免在 HTML class 中使用中文。
RESCUE_STATUS_SLUGS: dict[str, str] = {
    RESCUE_STATUS_PENDING: "pending",
    RESCUE_STATUS_IN_PROGRESS: "progress",
    RESCUE_STATUS_RESCUED: "rescued",
}

#: 状态推进时允许的后继状态，用于校验工作人员操作是否合法。
RESCUE_STATUS_FLOW: dict[str, str] = {
    RESCUE_STATUS_PENDING: RESCUE_STATUS_IN_PROGRESS,
    RESCUE_STATUS_IN_PROGRESS: RESCUE_STATUS_RESCUED,
}

#: 允许的图片扩展名。
ALLOWED_IMAGE_EXTENSIONS: tuple[str, ...] = ("jpg", "jpeg", "png", "webp")

#: 上传图片大小上限（字节），默认 5 MB。
MAX_IMAGE_BYTES: int = 5 * 1024 * 1024

# --------------------------------------------------------------------------- #
# 成为志愿者（表单字段参考 Best Friends《Volunteer Engagement》指南）
# --------------------------------------------------------------------------- #

#: 志愿者工作内容说明，用于页面介绍与表单选项。
VOLUNTEER_TASK_OPTIONS: list[str] = [
    "洗澡与基础美容",
    "喂食与换水",
    "记录身体状况",
    "运输动物",
    "遛狗与陪玩",
    "清洁犬舍与猫舍",
    "清理猫砂盆",
    "摄影与宣传",
    "档案与数据录入",
    "活动现场协助",
]

#: 可提供的技能与专长选项（对应指南中「知识与技能」条目）。
VOLUNTEER_SKILL_OPTIONS: list[str] = [
    "动物护理经验",
    "兽医或护理专业背景",
    "驾驶与动物运输",
    "摄影与视频剪辑",
    "设计与新媒体运营",
    "活动组织与执行",
    "外语翻译",
    "表格与数据整理",
]

#: 可服务时段选项。
VOLUNTEER_AVAILABILITY_OPTIONS: list[str] = [
    "工作日上午",
    "工作日下午",
    "周末上午",
    "周末下午",
    "可远程协助",
]

#: 时间投入承诺选项。
VOLUNTEER_COMMITMENT_OPTIONS: list[str] = [
    "每周 2 小时以内",
    "每周 2 - 4 小时",
    "每周 4 - 8 小时",
    "每周 8 小时以上",
    "仅活动日参与",
]

# --------------------------------------------------------------------------- #
# 爱心捐款（参与公益 → 爱心捐款）
# --------------------------------------------------------------------------- #

#: 预设捐赠档位（元），共 5 档，同时支持自定义金额。
DONATION_AMOUNTS: list[int] = [10, 25, 50, 75, 100]

#: 捐赠金额下限与上限（元），用于自定义金额校验。
DONATION_MIN_AMOUNT: float = 1.0
DONATION_MAX_AMOUNT: float = 100000.0

#: 捐赠周期：一次性 / 每月定期。
DONATION_FREQUENCY_ONCE: str = "once"
DONATION_FREQUENCY_MONTHLY: str = "monthly"

#: 捐赠周期到展示文案（msgid）的映射。
DONATION_FREQUENCY_OPTIONS: list[tuple[str, str]] = [
    (DONATION_FREQUENCY_ONCE, "一次性捐赠"),
    (DONATION_FREQUENCY_MONTHLY, "每月定期捐赠"),
]

#: 捐赠用途选项。
DONATION_DESIGNATION_OPTIONS: list[str] = [
    "不限用途（由救助站统一分配）",
    "动物救助行动",
    "医疗与绝育",
    "粮食与日常物资",
    "志愿者培训",
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


def breeds_for(species: str) -> list[str]:
    """获取某个类别下的品种列表。

    Args:
        species: 宠物类别；空字符串表示不限类别。

    Returns:
        对应类别的品种列表；类别为空或无法识别时返回全部品种。
    """
    if not species:
        return ALL_BREEDS
    return BREEDS_BY_SPECIES.get(species, [])


def shows_size(species: str) -> bool:
    """判断某个类别是否需要展示「体型」筛选。

    Args:
        species: 宠物类别。

    Returns:
        仅狗返回 ``True``；未选择类别时返回 ``True``（默认展示）。
    """
    if not species:
        return True
    return species not in NON_DOG_SPECIES


def age_group_range(age_group: str) -> tuple[int, int | None] | None:
    """查询年龄段对应的月龄区间。

    Args:
        age_group: 年龄段查询值。

    Returns:
        ``(最小月龄, 最大月龄)``；最大月龄为 ``None`` 表示不设上限，
        查询值无法识别时返回 ``None``。
    """
    for value, _label, min_months, max_months in AGE_GROUP_OPTIONS:
        if value == age_group:
            return min_months, max_months
    return None
