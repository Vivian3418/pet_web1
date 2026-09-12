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
from wtforms import (
    BooleanField,
    RadioField,
    SelectMultipleField,
    StringField,
    TextAreaField,
    widgets,
)
from wtforms.validators import DataRequired, Email, Length, Optional

from vv_pet01.data.dogs import (
    CONTACT_OPTIONS,
    DISCUSSION_TOPIC_OPTIONS,
    EXTRA_SERVICE_OPTIONS,
    PETS_AT_HOME_OPTIONS,
)


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
