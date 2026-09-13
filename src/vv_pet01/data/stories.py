"""首页「救助故事」合影图库模块。

首页救助故事区块使用「救助人 / 领养人与宠物合照」而非宠物单独的照片，
以呈现人与动物之间的联结。图库按宠物类别分组，与宠物档案相互独立：
照片按卡片顺序分配，因此无需为每条记录单独维护图片字段。

图片来自按关键词检索的图片服务，URL 末尾的 ``/all`` 表示必须同时匹配全部
标签（而非匹配任意一个），``lock`` 用于锁定到具体的某一张照片，
从而保证每次渲染结果稳定。

.. note::
   关键词匹配仍可能返回不含人物或宠物的照片，因此下列条目均已人工目视
   筛选，确保画面中同时出现人与宠物；替换时请先确认画面内容。

Typical usage example::

    from vv_pet01.data.stories import story_image

    print(story_image("猫", 0))
"""

from __future__ import annotations

#: 按类别分组的「人与宠物合照」图库。
STORY_IMAGES: dict[str, tuple[str, ...]] = {
    "狗": (
        "https://loremflickr.com/640/440/dog,owner/all?lock=3",
        "https://loremflickr.com/640/440/dog,owner/all?lock=1",
        "https://loremflickr.com/640/440/dog,person/all?lock=5",
        "https://loremflickr.com/640/440/dog,person/all?lock=6",
        "https://loremflickr.com/640/440/dog,person/all?lock=12",
        "https://loremflickr.com/640/440/dog,person/all?lock=13",
        "https://loremflickr.com/640/440/dog,person/all?lock=18",
        "https://loremflickr.com/640/440/dog,person/all?lock=11",
    ),
    "猫": (
        "https://loremflickr.com/640/440/cat,woman/all?lock=7",
        "https://loremflickr.com/640/440/cat,owner/all?lock=7",
        "https://loremflickr.com/640/440/cat,man/all?lock=3",
        "https://loremflickr.com/640/440/cat,owner/all?lock=9",
        "https://loremflickr.com/640/440/cat,man/all?lock=12",
        "https://loremflickr.com/640/440/cat,woman/all?lock=10",
        "https://loremflickr.com/640/440/cat,owner/all?lock=12",
        "https://loremflickr.com/640/440/cat,woman/all?lock=2",
    ),
    "其他宠物": (
        "https://loremflickr.com/640/440/rabbit,person/all?lock=7",
        "https://loremflickr.com/640/440/rabbit,person/all?lock=8",
        "https://loremflickr.com/640/440/rabbit,person/all?lock=3",
        "https://loremflickr.com/640/440/rabbit,person/all?lock=4",
        "https://loremflickr.com/640/440/parrot,person/all?lock=3",
        "https://loremflickr.com/640/440/parrot,person/all?lock=10",
        "https://loremflickr.com/640/440/rabbit,woman/all?lock=7",
        "https://loremflickr.com/640/440/rabbit,woman/all?lock=12",
    ),
}

#: 图库缺失时使用的兜底类别。
_FALLBACK_SPECIES: str = "狗"


def story_image(species: str, index: int) -> str:
    """按类别与卡片顺序取一张合影照片。

    Args:
        species: 宠物类别（狗 / 猫 / 其他宠物）。
        index: 卡片在本页中的序号（从 0 开始）。

    Returns:
        对应类别图库中该位置的照片地址；类别未收录时回退到默认图库，
        序号超出图库长度时循环取值。
    """
    images = STORY_IMAGES.get(species) or STORY_IMAGES[_FALLBACK_SPECIES]
    return images[index % len(images)]
