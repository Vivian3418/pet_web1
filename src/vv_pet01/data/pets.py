"""待领养宠物种子数据模块。

提供救助站在养的狗狗、猫咪与其他宠物档案，作为 SQLite 数据库的初始
种子数据来源。三类宠物统一存放于同一列表，通过 ``species`` 区分，
以支撑合并后的领养检索界面。

自由文本字段（呼名 / 简介）以中英成对形式提供；受控词表字段
（类别 / 品种 / 性别 / 体型 / 状态 / 性格标签 / 相处对象）以中文为规范值
存储，展示时通过 gettext 翻译，从而保证筛选条件与数据库取值一致。

Typical usage example::

    from vv_pet01.data.pets import PETS

    print(len(PETS), PETS[0]["name_en"])
"""

from __future__ import annotations

from typing import Any

from vv_pet01.data.taxonomy import STATUS_ADOPTABLE

#: 待领养宠物种子数据列表（狗 20 只、猫 10 只、其他宠物 5 只）。
#:
#: 每项字段含义如下：
#:
#: * ``id``: 宠物唯一编号。
#: * ``species``: 宠物类别（狗 / 猫 / 其他宠物）。
#: * ``name`` / ``name_en``: 呼名（中 / 英）。
#: * ``breed``: 品种（受控词表，与类别联动）。
#: * ``gender``: 性别（公 / 母）。
#: * ``age_months``: 月龄，用于年龄筛选与展示。
#: * ``size``: 体型（仅狗有值，猫与其他宠物为空字符串）。
#: * ``weight_kg``: 体重（千克）。
#: * ``shelter_id``: 所属救助站编号，关联 ``SHELTERS``。
#: * ``status``: 领养状态。
#: * ``vaccinated``: 是否已完成疫苗接种。
#: * ``neutered``: 是否已完成绝育。
#: * ``traits``: 性格标签（受控词表）。
#: * ``companions``: 适合与哪些对象相处（受控词表，多选）。
#: * ``description`` / ``description_en``: 救助经历与性格描述（中 / 英）。
#: * ``image``: 展示图片地址。
#: * ``intake_date``: 入站日期（ISO 格式），用于「最新发布」排序。
PETS: list[dict[str, Any]] = [
    # ---------------------------------- 狗狗 ----------------------------------
    {
        "id": 1,
        "species": "狗",
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
        "companions": ["适合有孩子的家庭", "适合与其他狗相处"],
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
        "species": "狗",
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
        "traits": ["活泼", "亲人"],
        "companions": ["适合有孩子的家庭", "适合与其他狗相处"],
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
        "species": "狗",
        "name": "阿黄",
        "name_en": "Ahuang",
        "breed": "柴犬",
        "gender": "公",
        "age_months": 42,
        "size": "中型",
        "weight_kg": 11.5,
        "shelter_id": "SH001",
        "status": "审核中",
        "vaccinated": True,
        "neutered": True,
        "traits": ["独立", "爱干净", "需要耐心"],
        "companions": ["适合上班族（长时间独处）"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭"],
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
        "species": "狗",
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
        "companions": ["适合与其他狗相处", "适合有孩子的家庭"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭", "适合与其他狗相处"],
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
        "species": "狗",
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
        "companions": ["适合老年家庭"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭", "适合与其他狗相处"],
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
        "species": "狗",
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
        "traits": ["安静", "不急躁"],
        "companions": ["适合老年家庭", "适合与其他猫相处"],
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
        "species": "狗",
        "name": "雪球",
        "name_en": "Xueqiu",
        "breed": "博美犬",
        "gender": "母",
        "age_months": 18,
        "size": "小型",
        "weight_kg": 3.8,
        "shelter_id": "SH003",
        "status": "审核中",
        "vaccinated": True,
        "neutered": False,
        "traits": ["机警", "爱叫", "适合公寓"],
        "companions": ["适合老年家庭"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭", "适合与其他狗相处"],
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
        "species": "狗",
        "name": "布丁",
        "name_en": "Buding",
        "breed": "比熊犬",
        "gender": "公",
        "age_months": 48,
        "size": "小型",
        "weight_kg": 6.8,
        "shelter_id": "SH004",
        "status": "已领养",
        "vaccinated": True,
        "neutered": True,
        "traits": ["温顺", "不掉毛"],
        "companions": ["适合老年家庭"],
        "description": "已由爱心家庭领养，档案保留用于回顾。",
        "description_en": "Already adopted by a loving family; this record is kept for reference.",
        "image": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-01-09",
    },
    {
        "id": 15,
        "species": "狗",
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
        "traits": ["独立", "爱干净"],
        "companions": ["适合上班族（长时间独处）", "适合与其他猫相处"],
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
        "species": "狗",
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
        "companions": ["适合与其他狗相处"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭"],
        "description": "被人遗弃在纸箱里的奶狗，已完成体内外驱虫，等待合适的家庭。",
        "description_en": (
            "Found abandoned in a cardboard box. Dewormed and waiting for the right family."
        ),
        "image": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-28",
    },
    {
        "id": 18,
        "species": "狗",
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
        "companions": ["适合老年家庭"],
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
        "species": "狗",
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
        "companions": ["适合有孩子的家庭", "适合与其他猫相处"],
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
        "species": "狗",
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
        "traits": ["温和", "亲人"],
        "companions": ["适合老年家庭", "适合与其他猫相处", "适合与其他狗相处"],
        "description": "被原主人托付到救助站的老年犬，希望能找到愿意陪她走完后半生的家庭。",
        "description_en": (
            "A senior dog entrusted to the shelter, hoping to find a family for her "
            "golden years."
        ),
        "image": "https://images.unsplash.com/photo-1558788353-f76d92427f16?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-04-27",
    },
    # ---------------------------------- 猫咪 ----------------------------------
    {
        "id": 21,
        "species": "猫",
        "name": "咪咪",
        "name_en": "Mimi",
        "breed": "中华田园猫",
        "gender": "母",
        "age_months": 18,
        "size": "",
        "weight_kg": 3.8,
        "shelter_id": "SH001",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["亲人", "爱干净", "安静"],
        "companions": ["适合有孩子的家庭", "适合与其他猫相处"],
        "description": "在小区车库被救助的猫咪，性格温顺，最喜欢趴在窗台晒太阳。",
        "description_en": (
            "Rescued from a residential garage. Gentle and happiest sunbathing on the "
            "windowsill."
        ),
        "image": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-07-05",
    },
    {
        "id": 22,
        "species": "猫",
        "name": "汤圆",
        "name_en": "Tangyuan",
        "breed": "英国短毛猫",
        "gender": "公",
        "age_months": 24,
        "size": "",
        "weight_kg": 5.2,
        "shelter_id": "SH001",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["黏人", "安静", "爱干净"],
        "companions": ["适合有孩子的家庭"],
        "description": "因原家庭过敏被送养，毛发浓密，性格沉稳亲人，不喜欢吵闹环境。",
        "description_en": (
            "Surrendered because of an allergy in the family. Dense coat, calm and "
            "affectionate; dislikes noisy environments."
        ),
        "image": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-06-12",
    },
    {
        "id": 23,
        "species": "猫",
        "name": "雪梨",
        "name_en": "Xueli",
        "breed": "布偶猫",
        "gender": "母",
        "age_months": 14,
        "size": "",
        "weight_kg": 4.6,
        "shelter_id": "SH002",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": False,
        "traits": ["温顺", "亲人", "不掉毛"],
        "companions": ["适合有孩子的家庭", "适合与其他猫相处", "适合与其他狗相处"],
        "description": "从繁殖场解救的布偶猫，被毛雪白柔软，非常依赖人的陪伴。",
        "description_en": (
            "Rescued from a breeding facility. Snow-soft coat and very attached to "
            "people."
        ),
        "image": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-03",
    },
    {
        "id": 24,
        "species": "猫",
        "name": "阿橘",
        "name_en": "Aju",
        "breed": "橘猫",
        "gender": "公",
        "age_months": 36,
        "size": "",
        "weight_kg": 5.8,
        "shelter_id": "SH002",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["贪吃", "亲人", "活泼"],
        "companions": ["适合老年家庭"],
        "description": "在社区喂猫点长大的橘猫，性格随和，对食物有着极高的热情。",
        "description_en": (
            "Grew up at a community feeding spot. Easygoing with an enormous "
            "enthusiasm for food."
        ),
        "image": "https://images.unsplash.com/photo-1574158622682-e40e69881006?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-05-21",
    },
    {
        "id": 25,
        "species": "猫",
        "name": "牛奶",
        "name_en": "Niunai",
        "breed": "奶牛猫",
        "gender": "母",
        "age_months": 8,
        "size": "",
        "weight_kg": 2.9,
        "shelter_id": "SH003",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": False,
        "traits": ["活泼", "好奇心强", "黏人"],
        "companions": ["适合有孩子的家庭", "适合与其他猫相处"],
        "description": "被人放在纸箱里送到救助站的小猫，精力充沛，喜欢追逐逗猫棒。",
        "description_en": (
            "Left at the shelter in a cardboard box as a kitten. Full of energy and "
            "loves chasing a wand toy."
        ),
        "image": "https://images.unsplash.com/photo-1592194996308-7b43878e84a6?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-26",
    },
    {
        "id": 26,
        "species": "猫",
        "name": "豆花",
        "name_en": "Douhua",
        "breed": "美国短毛猫",
        "gender": "公",
        "age_months": 30,
        "size": "",
        "weight_kg": 5.0,
        "shelter_id": "SH003",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["独立", "爱干净", "安静"],
        "companions": ["适合上班族（长时间独处）", "适合与其他猫相处"],
        "description": "自理能力强，独自在家时非常安静，适合白天不在家的上班族。",
        "description_en": (
            "Very self-sufficient and quiet when alone — suits people who work during "
            "the day."
        ),
        "image": "https://images.unsplash.com/photo-1529778873920-4da4926a72c2?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-06-30",
    },
    {
        "id": 27,
        "species": "猫",
        "name": "咖啡",
        "name_en": "Kafei",
        "breed": "暹罗猫",
        "gender": "母",
        "age_months": 20,
        "size": "",
        "weight_kg": 4.1,
        "shelter_id": "SH004",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["话多", "黏人", "聪明"],
        "companions": ["适合有孩子的家庭"],
        "description": "非常爱叫也爱「聊天」，会主动跟人互动，需要有回应的家庭。",
        "description_en": (
            "Very talkative and interactive — needs a family who enjoys the conversation."
        ),
        "image": "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-07-18",
    },
    {
        "id": 28,
        "species": "猫",
        "name": "公主",
        "name_en": "Gongzhu",
        "breed": "波斯猫",
        "gender": "母",
        "age_months": 48,
        "size": "",
        "weight_kg": 4.4,
        "shelter_id": "SH005",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["温顺", "需要耐心", "爱干净"],
        "companions": ["适合上班族（长时间独处）", "适合老年家庭"],
        "description": "前主人出国后转送而来，需要每天梳理被毛，性格安静不吵闹。",
        "description_en": (
            "Rehomed after her owner emigrated. Needs daily brushing and is quiet and "
            "undemanding."
        ),
        "image": "https://images.unsplash.com/photo-1561948955-570b270e7c36?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-04-08",
    },
    {
        "id": 29,
        "species": "猫",
        "name": "奶昔",
        "name_en": "Naixi",
        "breed": "中华田园猫",
        "gender": "公",
        "age_months": 12,
        "size": "",
        "weight_kg": 3.5,
        "shelter_id": "SH005",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": False,
        "traits": ["亲人", "活泼", "适合公寓"],
        "companions": ["适合与其他猫相处", "适合与其他狗相处"],
        "description": "在公园被志愿者救助的年轻猫咪，与其他猫狗都能和平相处。",
        "description_en": (
            "A young cat rescued in a park by volunteers; gets along with other cats "
            "and dogs."
        ),
        "image": "https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-19",
    },
    {
        "id": 30,
        "species": "猫",
        "name": "阿灰",
        "name_en": "Ahui",
        "breed": "英国短毛猫",
        "gender": "母",
        "age_months": 60,
        "size": "",
        "weight_kg": 4.9,
        "shelter_id": "SH006",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["安静", "不急躁", "爱睡觉"],
        "companions": ["适合老年家庭"],
        "description": "救助站里的老年猫咪，喜欢待在安静角落，适合有耐心陪伴的家庭。",
        "description_en": (
            "A senior cat at the shelter who loves quiet corners and patient company."
        ),
        "image": "https://images.unsplash.com/photo-1591871937573-74dbba515c4c?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-03-17",
    },
    # -------------------------------- 其他宠物 --------------------------------
    {
        "id": 31,
        "species": "其他宠物",
        "name": "棉花糖",
        "name_en": "Marshmallow",
        "breed": "垂耳兔",
        "gender": "母",
        "age_months": 10,
        "size": "",
        "weight_kg": 1.9,
        "shelter_id": "SH001",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["温顺", "安静", "爱干净"],
        "companions": ["适合有孩子的家庭"],
        "description": "被人遗弃在宠物医院门口的垂耳兔，性格温和，会安静地待在怀里。",
        "description_en": (
            "A lop rabbit abandoned outside a vet clinic. Gentle and happy to sit "
            "quietly in your arms."
        ),
        "image": "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-07-24",
    },
    {
        "id": 32,
        "species": "其他宠物",
        "name": "麻薯",
        "name_en": "Mochi",
        "breed": "侏儒兔",
        "gender": "公",
        "age_months": 8,
        "size": "",
        "weight_kg": 1.4,
        "shelter_id": "SH003",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": False,
        "traits": ["活泼", "好奇心强", "喜欢啃咬"],
        "companions": ["适合上班族（长时间独处）"],
        "description": "精力旺盛的小型兔，喜欢啃咬磨牙棒，需要准备足够的安全玩具。",
        "description_en": (
            "A lively little rabbit who loves chewing willow sticks; needs plenty of "
            "safe toys."
        ),
        "image": "https://images.unsplash.com/photo-1535241749838-299277b6305f?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-08-09",
    },
    {
        "id": 33,
        "species": "其他宠物",
        "name": "叽叽",
        "name_en": "Jiji",
        "breed": "虎皮鹦鹉",
        "gender": "公",
        "age_months": 14,
        "size": "",
        "weight_kg": 0.05,
        "shelter_id": "SH004",
        "status": STATUS_ADOPTABLE,
        "vaccinated": False,
        "neutered": False,
        "traits": ["话多", "活泼", "叫声清脆"],
        "companions": ["适合老年家庭"],
        "description": "被主人送养的虎皮鹦鹉，已经学会几个词，喜欢在清晨鸣叫。",
        "description_en": (
            "A budgerigar rehomed by his owner. Knows a few words and sings at dawn."
        ),
        "image": "https://images.unsplash.com/photo-1552728089-57bdde30beb3?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-06-05",
    },
    {
        "id": 34,
        "species": "其他宠物",
        "name": "元宝",
        "name_en": "Yuanbao",
        "breed": "玄凤鹦鹉",
        "gender": "母",
        "age_months": 20,
        "size": "",
        "weight_kg": 0.09,
        "shelter_id": "SH006",
        "status": STATUS_ADOPTABLE,
        "vaccinated": False,
        "neutered": False,
        "traits": ["亲人", "聪明", "爱撒娇"],
        "companions": ["适合有孩子的家庭"],
        "description": "手养长大的玄凤鹦鹉，非常亲近人，喜欢站在肩膀上陪伴主人。",
        "description_en": (
            "A hand-raised cockatiel, very tame and fond of riding on a shoulder."
        ),
        "image": "https://images.unsplash.com/photo-1444464666168-49d633b86797?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-05-02",
    },
    {
        "id": 35,
        "species": "其他宠物",
        "name": "泡芙",
        "name_en": "Puff",
        "breed": "垂耳兔",
        "gender": "公",
        "age_months": 16,
        "size": "",
        "weight_kg": 2.2,
        "shelter_id": "SH002",
        "status": STATUS_ADOPTABLE,
        "vaccinated": True,
        "neutered": True,
        "traits": ["不急躁", "爱干净", "需要陪伴"],
        "companions": ["适合有孩子的家庭"],
        "description": "从小与孩子一起长大的兔子，习惯被抱，适合有耐心的家庭。",
        "description_en": (
            "Grew up around children and is used to being held; suits a patient family."
        ),
        "image": "https://images.unsplash.com/photo-1591389703635-e15a07b842d7?auto=format&fit=crop&w=800&q=80",
        "intake_date": "2026-04-19",
    },
]
