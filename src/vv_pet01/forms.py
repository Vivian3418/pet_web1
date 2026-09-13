"""表单定义模块。

包含领养申请表，字段结构参考 Humane World for Animals 的
**Adopters Welcome: Sample questionnaire**：

* 申请人信息与最佳联系方式
* 新宠物家庭成员构成与家中现有宠物情况
* 希望与救助站沟通的养护话题清单
* 救助站可提供的额外服务与支持清单

校验消息统一使用中文 msgid，模板通过 gettext 翻译，从而实现中英双语提示。
"""

from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DecimalField,
    HiddenField,
    RadioField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
    widgets,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

from vv_pet01.data.taxonomy import (
    ALLOWED_IMAGE_EXTENSIONS,
    CONTACT_OPTIONS,
    DISCUSSION_TOPIC_OPTIONS,
    DONATION_AMOUNTS,
    DONATION_DESIGNATION_OPTIONS,
    DONATION_FREQUENCY_OPTIONS,
    DONATION_MAX_AMOUNT,
    DONATION_MIN_AMOUNT,
    EXTRA_SERVICE_OPTIONS,
    PETS_AT_HOME_OPTIONS,
    RESCUE_ANIMAL_OPTIONS,
    RESCUE_HANDLING_OPTIONS,
    RESCUE_SITUATION_OPTIONS,
    RESCUE_URGENCY_OPTIONS,
    VOLUNTEER_AVAILABILITY_OPTIONS,
    VOLUNTEER_COMMITMENT_OPTIONS,
    VOLUNTEER_SKILL_OPTIONS,
    VOLUNTEER_TASK_OPTIONS,
)

#: 自定义捐赠金额在单选组中使用的取值。
CUSTOM_AMOUNT_VALUE: str = "custom"

#: 常见校验消息（中文 msgid，模板通过 gettext 翻译）。
_REQUIRED = "此项为必填"
_TOO_LONG = "长度不能超过 %(max)d 个字符"


class MultiCheckboxField(SelectMultipleField):
    """以复选框组渲染的多选字段。

    默认的 ``SelectMultipleField`` 会渲染成 ``<select multiple>``，
    对长清单不友好；此处改用 ``ListWidget`` + ``CheckboxInput``，
    使每个选项独立成行，便于移动端点选。
    """

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


def _checkbox_choices(options: list[str]) -> list[tuple[str, str]]:
    """把选项文本列表转换为 WTForms 所需的 ``(value, label)`` 结构。

    值与标签同为中文规范值，标签在模板中翻译，从而保证入库数据稳定。

    Args:
        options: 中文选项列表。

    Returns:
        ``(值, 标签)`` 二元组列表。
    """
    return [(option, option) for option in options]


def _localize_choices(field: object, options: list[str]) -> None:
    """把某个字段的选项标签替换为当前请求语言下的文案。

    ``SelectField`` 由 WTForms 直接渲染 ``<option>``，模板无法再包一层
    gettext，因此需要在渲染前把标签翻译好。选项的值保持中文规范值不变，
    以保证入库数据稳定。

    Args:
        field: 需要处理的下拉 / 单选字段。
        options: 该字段的选项列表（中文规范值）。
    """
    from flask_babel import gettext

    if field is not None and hasattr(field, "choices"):
        field.choices = [(option, gettext(option)) for option in options]


class AdoptionApplicationForm(FlaskForm):
    """领养申请表。

    Attributes:
        animal_name: 动物呼名（从详情页带出，可修改）。
        applicant_name: 申请人姓名。
        address: 联系地址。
        town_state_zip: 城市 / 省州 / 邮编。
        email: 电子邮箱。
        preferred_phone: 联系电话。
        preferred_contact: 最佳联系方式。
        is_gift: 是否为赠送给他人而领养。
        household_members: 家庭成员构成说明。
        pets_at_home: 家中现有宠物情况（多选）。
        other_info: 其他希望分享的信息。
        discussion_topics: 希望沟通的养护话题（多选）。
        other_questions: 其他疑问。
        extra_services: 感兴趣的额外服务（多选）。
        confirm_accuracy: 确认所填信息真实。
    """

    animal_name = StringField(
        "动物呼名",
        validators=[Optional(), Length(max=120, message="长度不能超过 %(max)d 个字符")],
    )
    applicant_name = StringField(
        "申请人姓名",
        validators=[
            DataRequired(message="此项为必填"),
            Length(max=120, message="长度不能超过 %(max)d 个字符"),
        ],
    )
    address = StringField(
        "联系地址",
        validators=[Optional(), Length(max=255, message="长度不能超过 %(max)d 个字符")],
    )
    town_state_zip = StringField(
        "城市 / 省州 / 邮编",
        validators=[Optional(), Length(max=120, message="长度不能超过 %(max)d 个字符")],
    )
    email = StringField(
        "电子邮箱",
        validators=[
            DataRequired(message="此项为必填"),
            Email(message="请输入有效的电子邮箱地址"),
            Length(max=160, message="长度不能超过 %(max)d 个字符"),
        ],
    )
    preferred_phone = StringField(
        "联系电话",
        validators=[Optional(), Length(max=40, message="长度不能超过 %(max)d 个字符")],
    )
    preferred_contact = RadioField(
        "最佳联系方式",
        choices=_checkbox_choices(CONTACT_OPTIONS),
        default=CONTACT_OPTIONS[-1],
        validators=[DataRequired(message="此项为必填")],
    )
    is_gift = BooleanField("这份领养是送给他人")

    household_members = TextAreaField(
        "新宠物的家庭成员构成",
        validators=[
            DataRequired(message="此项为必填"),
            Length(max=2000, message="长度不能超过 %(max)d 个字符"),
        ],
        render_kw={"rows": 4},
    )
    pets_at_home = MultiCheckboxField(
        "家中现有宠物情况",
        choices=_checkbox_choices(PETS_AT_HOME_OPTIONS),
    )
    other_info = TextAreaField(
        "其他希望分享的信息",
        validators=[Optional(), Length(max=2000, message="长度不能超过 %(max)d 个字符")],
        render_kw={"rows": 3},
    )
    discussion_topics = MultiCheckboxField(
        "希望与救助站沟通的话题",
        choices=_checkbox_choices(DISCUSSION_TOPIC_OPTIONS),
    )
    other_questions = TextAreaField(
        "其他疑问",
        validators=[Optional(), Length(max=2000, message="长度不能超过 %(max)d 个字符")],
        render_kw={"rows": 3},
    )
    extra_services = MultiCheckboxField(
        "感兴趣的额外服务与支持",
        choices=_checkbox_choices(EXTRA_SERVICE_OPTIONS),
    )
    confirm_accuracy = BooleanField(
        "我确认以上信息真实有效",
        validators=[DataRequired(message="请确认信息真实有效后再提交")],
    )

    def to_payload(self) -> dict[str, object]:
        """把表单数据整理为可写入数据库的字典。

        Returns:
            与 ``applications`` 表字段对应的字典，多选字段为 Python 列表。
        """
        return {
            "applicant_name": (self.applicant_name.data or "").strip(),
            "address": (self.address.data or "").strip(),
            "town_state_zip": (self.town_state_zip.data or "").strip(),
            "email": (self.email.data or "").strip(),
            "preferred_phone": (self.preferred_phone.data or "").strip(),
            "preferred_contact": self.preferred_contact.data or "",
            "is_gift": bool(self.is_gift.data),
            "household_members": (self.household_members.data or "").strip(),
            "pets_at_home": self.pets_at_home.data or [],
            "other_info": (self.other_info.data or "").strip(),
            "discussion_topics": self.discussion_topics.data or [],
            "other_questions": (self.other_questions.data or "").strip(),
            "extra_services": self.extra_services.data or [],
        }


class RescueReportForm(FlaskForm):
    """动物救助工单表单（参与公益 → 动物救助）。

    收集待救助动物的类别与情况、处理方式、现场照片与位置，
    并由前端配合浏览器定位写入经纬度。

    Attributes:
        animal_type: 需要救助的动物类别。
        situation: 动物目前的情况（被遗弃 / 受伤 / 生病等）。
        urgency: 紧急程度。
        handling: 希望的救助方式（自行送往救助站 / 申请工作人员前来）。
        description: 情况补充描述。
        address_text: 发现地点（用户手动输入或由定位反填）。
        lat / lng: 经纬度（隐藏字段，由前端定位脚本写入）。
        photo: 现场照片。
        reporter_name: 报告人称呼。
        reporter_phone: 报告人联系电话。
        reporter_email: 报告人邮箱。
        confirm_accuracy: 确认信息真实。
    """

    animal_type = SelectField(
        "需要救助的动物",
        choices=_checkbox_choices(RESCUE_ANIMAL_OPTIONS),
        validators=[DataRequired(message=_REQUIRED)],
    )
    situation = SelectField(
        "动物目前的情况",
        choices=_checkbox_choices(RESCUE_SITUATION_OPTIONS),
        validators=[DataRequired(message=_REQUIRED)],
    )
    urgency = SelectField(
        "紧急程度",
        choices=_checkbox_choices(RESCUE_URGENCY_OPTIONS),
        validators=[DataRequired(message=_REQUIRED)],
    )
    handling = RadioField(
        "希望的救助方式",
        choices=_checkbox_choices(RESCUE_HANDLING_OPTIONS),
        validators=[DataRequired(message=_REQUIRED)],
    )
    description = TextAreaField(
        "情况补充描述",
        validators=[Optional(), Length(max=2000, message=_TOO_LONG)],
        render_kw={"rows": 4},
    )
    address_text = StringField(
        "发现地点",
        validators=[
            DataRequired(message=_REQUIRED),
            Length(max=255, message=_TOO_LONG),
        ],
    )
    lat = HiddenField()
    lng = HiddenField()
    photo = FileField(
        "现场照片",
        validators=[
            FileAllowed(
                list(ALLOWED_IMAGE_EXTENSIONS),
                message="仅支持 jpg / jpeg / png / webp 格式的图片",
            )
        ],
    )
    reporter_name = StringField(
        "你的称呼",
        validators=[Optional(), Length(max=60, message=_TOO_LONG)],
    )
    reporter_phone = StringField(
        "联系电话",
        validators=[Optional(), Length(max=40, message=_TOO_LONG)],
    )
    reporter_email = StringField(
        "电子邮箱",
        validators=[
            Optional(),
            Email(message="请输入有效的电子邮箱地址"),
            Length(max=160, message=_TOO_LONG),
        ],
    )
    confirm_accuracy = BooleanField(
        "我确认以上信息真实有效",
        validators=[DataRequired(message="请确认信息真实有效后再提交")],
    )

    def localize_choices(self) -> None:
        """按当前请求语言翻译下拉选项标签。"""
        _localize_choices(self.animal_type, RESCUE_ANIMAL_OPTIONS)
        _localize_choices(self.situation, RESCUE_SITUATION_OPTIONS)
        _localize_choices(self.urgency, RESCUE_URGENCY_OPTIONS)
        _localize_choices(self.handling, RESCUE_HANDLING_OPTIONS)

    def coordinates(self) -> tuple[float | None, float | None]:
        """解析隐藏字段中的经纬度。

        Returns:
            ``(纬度, 经度)``；字段缺失、非法或超出范围时返回 ``(None, None)``。
        """

        def _parse(raw: str | None, low: float, high: float) -> float | None:
            try:
                value = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return None
            return value if low <= value <= high else None

        lat = _parse(self.lat.data, -90, 90)
        lng = _parse(self.lng.data, -180, 180)
        if lat is None or lng is None:
            return None, None
        return lat, lng

    def to_payload(self) -> dict[str, object]:
        """把表单数据整理为可写入数据库的字典。

        Returns:
            与 ``rescue_reports`` 表字段对应的字典。
        """
        lat, lng = self.coordinates()
        return {
            "animal_type": self.animal_type.data or "",
            "situation": self.situation.data or "",
            "urgency": self.urgency.data or "",
            "handling": self.handling.data or "",
            "description": (self.description.data or "").strip(),
            "address_text": (self.address_text.data or "").strip(),
            "lat": lat,
            "lng": lng,
            "reporter_name": (self.reporter_name.data or "").strip(),
            "reporter_phone": (self.reporter_phone.data or "").strip(),
            "reporter_email": (self.reporter_email.data or "").strip(),
        }


class VolunteerApplicationForm(FlaskForm):
    """志愿者申请表。

    字段结构参考 Best Friends Animal Society《Volunteer Engagement》指南：
    除基本个人信息外，申请表应给申请人充分机会描述其知识、技能与专长，
    并配合志愿者手册与安全指南确认。

    Attributes:
        full_name: 姓名。
        email: 电子邮箱。
        phone: 联系电话。
        city: 所在城市。
        occupation: 职业 / 专业。
        is_adult: 是否已满 18 周岁。
        guardian_name: 监护人姓名（未满 18 周岁填写）。
        skills: 可提供的技能与专长（多选）。
        skill_detail: 其他技能或相关资格。
        tasks: 希望参与的工作内容（多选）。
        availability: 可服务时段（多选）。
        commitment: 可投入的时间。
        start_availability: 可开始服务的日期。
        experience: 过往志愿服务经历。
        motivation: 加入志愿者的原因。
        physical_ok: 可胜任体力工作。
        accept_handbook: 已阅读并同意志愿者手册与安全指南。
        emergency_name: 紧急联系人。
        emergency_phone: 紧急联系人电话。
    """

    full_name = StringField(
        "姓名",
        validators=[
            DataRequired(message=_REQUIRED),
            Length(max=60, message=_TOO_LONG),
        ],
    )
    email = StringField(
        "电子邮箱",
        validators=[
            DataRequired(message=_REQUIRED),
            Email(message="请输入有效的电子邮箱地址"),
            Length(max=160, message=_TOO_LONG),
        ],
    )
    phone = StringField(
        "联系电话",
        validators=[Optional(), Length(max=40, message=_TOO_LONG)],
    )
    city = StringField(
        "所在城市",
        validators=[Optional(), Length(max=60, message=_TOO_LONG)],
    )
    occupation = StringField(
        "职业 / 专业",
        validators=[Optional(), Length(max=80, message=_TOO_LONG)],
    )
    is_adult = BooleanField("我已年满 18 周岁", default=True)
    guardian_name = StringField(
        "监护人姓名（未满 18 周岁填写）",
        validators=[Optional(), Length(max=60, message=_TOO_LONG)],
    )
    skills = MultiCheckboxField(
        "可提供的技能与专长",
        choices=_checkbox_choices(VOLUNTEER_SKILL_OPTIONS),
    )
    skill_detail = TextAreaField(
        "其他技能或相关资格",
        validators=[Optional(), Length(max=1000, message=_TOO_LONG)],
        render_kw={"rows": 3},
    )
    tasks = MultiCheckboxField(
        "希望参与的工作内容",
        choices=_checkbox_choices(VOLUNTEER_TASK_OPTIONS),
    )
    availability = MultiCheckboxField(
        "可服务时段",
        choices=_checkbox_choices(VOLUNTEER_AVAILABILITY_OPTIONS),
    )
    commitment = SelectField(
        "可投入的时间",
        choices=_checkbox_choices(VOLUNTEER_COMMITMENT_OPTIONS),
        validators=[DataRequired(message=_REQUIRED)],
    )
    start_availability = StringField(
        "可开始服务的日期",
        validators=[Optional(), Length(max=40, message=_TOO_LONG)],
    )
    experience = TextAreaField(
        "过往志愿服务经历",
        validators=[Optional(), Length(max=2000, message=_TOO_LONG)],
        render_kw={"rows": 4},
    )
    motivation = TextAreaField(
        "为什么想加入志愿者",
        validators=[
            DataRequired(message=_REQUIRED),
            Length(max=2000, message=_TOO_LONG),
        ],
        render_kw={"rows": 4},
    )
    physical_ok = BooleanField(
        "我可以胜任需要体力或长时间站立的工作",
        default=True,
    )
    accept_handbook = BooleanField(
        "我已阅读并同意遵守志愿者手册与安全指南",
        validators=[DataRequired(message="请先阅读并同意志愿者手册与安全指南")],
    )
    emergency_name = StringField(
        "紧急联系人",
        validators=[Optional(), Length(max=60, message=_TOO_LONG)],
    )
    emergency_phone = StringField(
        "紧急联系人电话",
        validators=[Optional(), Length(max=40, message=_TOO_LONG)],
    )

    def localize_choices(self) -> None:
        """按当前请求语言翻译选项标签。"""
        _localize_choices(self.skills, VOLUNTEER_SKILL_OPTIONS)
        _localize_choices(self.tasks, VOLUNTEER_TASK_OPTIONS)
        _localize_choices(self.availability, VOLUNTEER_AVAILABILITY_OPTIONS)
        _localize_choices(self.commitment, VOLUNTEER_COMMITMENT_OPTIONS)

    def to_payload(self) -> dict[str, object]:
        """把表单数据整理为可写入数据库的字典。

        Returns:
            与 ``volunteer_applications`` 表字段对应的字典，多选字段为列表。
        """
        return {
            "full_name": (self.full_name.data or "").strip(),
            "email": (self.email.data or "").strip(),
            "phone": (self.phone.data or "").strip(),
            "city": (self.city.data or "").strip(),
            "occupation": (self.occupation.data or "").strip(),
            "is_adult": bool(self.is_adult.data),
            "guardian_name": (self.guardian_name.data or "").strip(),
            "skills": self.skills.data or [],
            "skill_detail": (self.skill_detail.data or "").strip(),
            "tasks": self.tasks.data or [],
            "availability": self.availability.data or [],
            "commitment": self.commitment.data or "",
            "start_availability": (self.start_availability.data or "").strip(),
            "experience": (self.experience.data or "").strip(),
            "motivation": (self.motivation.data or "").strip(),
            "physical_ok": bool(self.physical_ok.data),
            "accept_handbook": bool(self.accept_handbook.data),
            "emergency_name": (self.emergency_name.data or "").strip(),
            "emergency_phone": (self.emergency_phone.data or "").strip(),
        }


class DonationForm(FlaskForm):
    """爱心捐款表单。

    支持一次性捐赠与每月定期捐赠，金额可在 5 个预设档位中选择，
    也可自行输入（选择「自定义金额」时以 ``custom_amount`` 为准）。

    Attributes:
        frequency: 捐赠方式（一次性 / 每月定期）。
        amount_choice: 预设档位或 ``custom``。
        custom_amount: 自定义金额。
        donor_name: 捐赠人称呼。
        email: 电子邮箱。
        designation: 捐赠用途。
        message: 留言。
        anonymous: 是否匿名捐赠。
    """

    frequency = RadioField(
        "捐赠方式",
        choices=list(DONATION_FREQUENCY_OPTIONS),
        default=DONATION_FREQUENCY_OPTIONS[0][0],
        validators=[DataRequired(message=_REQUIRED)],
    )
    amount_choice = RadioField(
        "捐赠金额（元）",
        choices=[
            *[(str(amount), f"{amount} 元") for amount in DONATION_AMOUNTS],
            (CUSTOM_AMOUNT_VALUE, "自定义金额"),
        ],
        default=str(DONATION_AMOUNTS[2]),
        validators=[DataRequired(message=_REQUIRED)],
    )
    custom_amount = DecimalField(
        "自定义金额（元）",
        validators=[
            Optional(),
            NumberRange(
                min=DONATION_MIN_AMOUNT,
                max=DONATION_MAX_AMOUNT,
                message="请输入 %(min)s 至 %(max)s 之间的金额",
            ),
        ],
        places=2,
        render_kw={"placeholder": "请输入金额"},
    )
    donor_name = StringField(
        "你的称呼",
        validators=[Optional(), Length(max=60, message=_TOO_LONG)],
    )
    email = StringField(
        "电子邮箱",
        validators=[
            DataRequired(message=_REQUIRED),
            Email(message="请输入有效的电子邮箱地址"),
            Length(max=160, message=_TOO_LONG),
        ],
    )
    designation = SelectField(
        "捐赠用途",
        choices=_checkbox_choices(DONATION_DESIGNATION_OPTIONS),
    )
    message = TextAreaField(
        "留言",
        validators=[Optional(), Length(max=500, message=_TOO_LONG)],
        render_kw={"rows": 3},
    )
    anonymous = BooleanField("以匿名方式捐赠")

    def localize_choices(self) -> None:
        """按当前请求语言翻译选项标签。

        捐赠方式与金额档位的「值」与「标签」并不相同（如值为 ``50``、
        标签为 ``50 元``），因此需要单独构造。
        """
        from flask_babel import gettext

        self.frequency.choices = [
            (value, gettext(label)) for value, label in DONATION_FREQUENCY_OPTIONS
        ]
        self.amount_choice.choices = [
            *[(str(amount), gettext(f"{amount} 元")) for amount in DONATION_AMOUNTS],
            (CUSTOM_AMOUNT_VALUE, gettext("自定义金额")),
        ]
        _localize_choices(self.designation, DONATION_DESIGNATION_OPTIONS)

    def resolve_amount(self) -> float | None:
        """计算最终捐赠金额。

        Returns:
            选择预设档位时返回该档位金额，选择自定义时返回输入金额；
            自定义金额缺失或非正数时返回 ``None``。
        """
        choice = (self.amount_choice.data or "").strip()
        if choice != CUSTOM_AMOUNT_VALUE:
            try:
                value = float(choice)
            except (TypeError, ValueError):
                return None
            return value if value > 0 else None

        amount = self.custom_amount.data
        if amount is None:
            return None
        value = float(amount)
        return value if value > 0 else None

    def to_payload(self) -> dict[str, object]:
        """把表单数据整理为可写入数据库的字典。

        Returns:
            与 ``donations`` 表字段对应的字典；金额非法时 ``amount`` 为 0。
        """
        return {
            "donor_name": (self.donor_name.data or "").strip(),
            "email": (self.email.data or "").strip(),
            "amount": self.resolve_amount() or 0.0,
            "frequency": self.frequency.data or DONATION_FREQUENCY_OPTIONS[0][0],
            "designation": self.designation.data or "",
            "message": (self.message.data or "").strip(),
            "anonymous": bool(self.anonymous.data),
        }
