# vv_pet01

> 让每一个生命都被温柔以待。 / Let every life be met with gentleness.

`vv_pet01` 是一个以 **动物保护、宠物救助、宠物领养** 为核心的公益网站模拟系统。
站点采用简洁的蓝白配色与下拉式导航，提供领养、保护与公益参与三大板块的完整入口。

当前已完成的能力：

- **领养宠物（合并检索）**：狗 / 猫 / 其他宠物统一在一个页面检索，按「所在地 + 搜索距离 →
  宠物类别 → 细分条件」三步组织，品种与类别联动
- **领养申请表**：参考 Humane World《Adopters Welcome: Sample Questionnaire》设计，
  从「我要领养」按钮直达，提交后生成申请回执与申请记录列表
- **中英双语**：全站文案双语，通过 URL 语言前缀切换（`/zh/...` 与 `/en/...`）
- **SQLite 持久化**：救助站、宠物、领养申请三张表，首次启动自动建表并写入种子数据

占位页面（动物保护、参与公益下的子页面）仅展示页面名称。

## 功能板块

顶部导航结构如下：

| 菜单 | 类型 | 说明 |
| --- | --- | --- |
| 首页 | 直达 | 站点首页 |
| 领养宠物 | 直达 | 合并后的宠物领养检索页（不再使用下拉菜单） |
| 领养流程 | 直达 | 领养流程说明页 |
| 动物保护 | 下拉 | 动物福利 / 反动物虐待 / 灾害动物救助（占位页） |
| 参与公益 | 下拉 | 动物救助 / 成为志愿者 / 爱心捐款（均已实现） |

原有的「领养狗狗 / 领养猫咪 / 其他宠物」三个子菜单项已移除，改为检索页中的
**「宠物类别」**筛选条件；旧入口 `/adoption/dogs`、`/adoption/cats`、`/adoption/others`
保留为 301 永久重定向，会自动带上对应类别。

## 首页结构

首页自上而下由四个区块组成：

1. **Hero**：站点品牌、公益标语与关键数据。
2. **领养流程**：四步流程图（在线提交申请 → 救助站联系沟通 → 见面与匹配 → 签署协议与交接），
   桌面端横向排列并带连接箭头，窄屏自动转为纵向排列。
3. **行动号召**：捐赠与寄养入口。
4. **救助故事**：页面最底端的横向滚动图片卡片。每张卡片展示一张**救助人 / 领养人与
   宠物的合照**、宠物的类别与城市、呼名与救助经历，并可跳转到详情页发起领养申请。
   支持鼠标滚轮 / 触屏滑动 / 键盘左右键（容器可聚焦），并带有滚动吸附（scroll-snap）。

合影图库位于 `src/vv_pet01/data/stories.py`，按宠物类别分组，与宠物档案相互独立：
照片按卡片顺序分配，因此同一屏内不会出现重复构图。图片来自关键词图片服务，
全部条目均已人工目视筛选，确保画面中同时出现人与宠物（关键词检索可能返回
仅含宠物或仅含人物的照片）。

## 领养宠物检索

### 三步检索模型

| 步骤 | 控件 | 说明 |
| --- | --- | --- |
| **1. 所在地 + 搜索距离** | `city` / `radius` | 确定参考点并过滤附近救助站 |
| **2. 宠物类别** | `species` | 狗 / 猫 / 其他宠物；决定可选品种与是否展示体型 |
| **3. 细分条件** | `breed` / `gender` / `age` / `size` / `companion` | 选择类别后才显示 |

### 参考点与搜索距离

参考点按以下优先级确定：

1. 用户授权浏览器定位 → 使用实际坐标（`lat` + `lng`）；
2. 否则使用所选**城市中心坐标**（`src/vv_pet01/data/cities.py`，覆盖 5 个城市）。

参考点确定后，用 Haversine 公式计算各救助站距离，仅保留搜索距离（5 / 10 / 25 / 50 / 100 公里）
以内的救助站所辖宠物。这样**不授权定位也能按距离筛选**；未选择所在地时距离条件自动失效。

### 类别联动规则

- **品种随类别联动**：选择「狗」只显示犬类品种，选择「猫」只显示猫类品种，
  「其他宠物」显示兔 / 鸟等品种；未选择类别时显示全部品种。
- **体型仅对狗展示**：猫与其他宠物不显示体型筛选项。
- **切换类别自动清空无效条件**：前端在切换时清空品种与体型，服务端在
  `_sanitize_filters()` 中再次兜底清洗，并在页面上提示被清空的条件，
  避免出现「选了猫却仍按犬类品种过滤」的空结果。

### 全部筛选条件

| 参数 | 说明 |
| --- | --- |
| `species` | 宠物类别：狗 / 猫 / 其他宠物 |
| `city` | 所在地（城市名称） |
| `radius` | 搜索距离（千米），留空表示不限 |
| `breed` | 品种（与类别联动） |
| `gender` | 性别 |
| `age` | 年龄段：`baby`（一岁以下）/ `young`（一至三岁）/ `adult`（三至七岁）/ `senior`（七岁以上） |
| `size` | 体型（仅狗类别生效） |
| `companion` | 适合与哪些对象相处（可多选，命中任意一项即匹配） |
| `q` | 关键词，匹配呼名、品种、性格、简介与救助站信息 |
| `status` | 领养状态，默认仅展示「待领养」 |
| `shelter` | 限定某个救助站（与搜索距离取交集） |
| `sort` | `distance` / `latest` / `age_asc` / `name` |
| `page` | 分页，每页 9 条 |

侧栏列出**当前条件下仍有在养宠物**的救助站及其数量，点击即可把结果限定到该站。

## 领养申请表

### 入口（不新增导航菜单项）

| 位置 | 按钮 | 跳转目标 |
| --- | --- | --- |
| 检索结果卡片 | 我要领养 | `/<lang>/adoption/pets/<pet_id>/apply` |
| 宠物详情页 | 我要领养 | 同上（宠物呼名自动预填） |

### 表单结构

字段结构参考 Humane World for Animals 发布的 **Adopters Welcome: Sample Questionnaire**，
按五个部分分组：

1. **领养对象**：宠物呼名（从详情页自动预填，可修改）
2. **申请人信息**：姓名、邮箱、地址、城市/省州/邮编、联系电话、最佳联系方式（短信/电话/邮件）、是否为赠礼
3. **家庭成员与家中宠物**：家庭成员构成、家中现有宠物情况（多选）、其他希望分享的信息
4. **希望沟通的养护话题**：16 项养护话题多选（喂养、如厕训练、美容、疫苗预防、绝育、笼内训练等）
5. **感兴趣的额外服务**：12 项救助站支持多选（项圈与身份牌、宠物粮、借用航空箱、疫苗/芯片活动、寄养与捐赠信息等）

此外包含「我确认以上信息真实有效」的必选确认项。

### 提交与查看

- 表单通过 **Flask-WTF** 提供 CSRF 保护，服务端完成必填、长度与邮箱格式校验，
  错误提示就地显示在字段下方，并随语言切换（中文 / English）。
- 提交采用 **PRG 模式**（POST → 302 → GET），避免刷新导致重复提交。
- 提交成功后进入 **申请回执页**（`/<lang>/adoption/applications/<id>`），
  展示申请编号 `AV-YYYYMMDD-NNNN`、申请概要、所选话题与服务、后续流程说明。
- **申请记录页**（`/<lang>/adoption/applications`）以表格列出全部已提交申请，支持分页与查看回执。
- 申请记录会保存宠物名称快照，即使后续重新灌入种子数据，历史申请仍可正常展示。

## 参与公益

「参与公益」下拉菜单包含 **动物救助 / 成为志愿者 / 爱心捐款** 三项。
原有的「公益活动」「寄养宠物」已移出导航，但页面路由仍然保留，历史链接可直接访问。

### 1. 动物救助（`GET|POST /<lang>/charity/rescue`）

页面按四段组织，先说明再操作：

1. **哪些情况可以上报**：被遗弃 / 受伤 / 生病 / 被困求助 / 疑似遭受虐待 / 幼崽失去母兽，
   可上报狗、猫与其他小动物，无法判断种类时可选「不确定」。
2. **两种救助方式**：送到最近的救助站，或上传照片与位置由工作人员前往救助。
3. **确定位置，查看最近救助站**：可选择城市 / 手动输入地址 / 使用浏览器定位，
   确定参考点后渲染 **Leaflet 地图**（OpenStreetMap 瓦片，无需 API Key），
   标记参考点与最近 4 家救助站，并绘制连线与距离标签；右侧列表同步展示地址、电话与具体距离。
   - 演示站点未接入地理编码，手填地址按**城市名匹配**粗定位到城市中心（5 个已收录城市）。
   - 地图取景只参考参考点与最近的 2 家救助站，避免上千公里外的站点把视野拉散。
4. **提交救助信息**：动物与情况（类别 / 情况 / 紧急程度 / 希望的处理方式）、
   照片与位置（现场照片上传 + 发现地点）、联系方式与真实性确认。

照片保存在 Flask 实例目录的 `uploads/` 下，仅接受 jpg / jpeg / png / webp，
单张上限 5 MB，文件名经安全处理并追加随机串；数据库只存相对路径，
通过 `/<lang>/charity/uploads/<filename>` 提供读取。超出限制会返回友好的 413 提示页。

**救助进度**采用三态流转，与需求一致：

```
未被救助  ──开始救助──▶  正在救助中  ──标记救助成功──▶  救助成功
```

状态推进在 **救助工单列表页**（`GET /<lang>/charity/rescue/reports`）完成：
页面顶部是按状态统计且可点击过滤的统计卡片，每条工单带「开始救助 / 标记救助成功」按钮
与可选的处理备注；已是终态的工单显示「流程已完成」。
提交后会生成回执页（`RESCUE-YYYYMMDD-NNNN`），展示上报内容、现场照片、最近救助站与进度说明。

### 2. 成为志愿者（`GET|POST /<lang>/charity/volunteer`）

页面先介绍工作内容，再给出申请表。工作内容涵盖 **洗澡与基础美容、喂食与换水、
记录身体状况、运输动物、遛狗与陪玩、清洁犬舍猫舍、清理猫砂盆、摄影与宣传、
档案与数据录入、活动现场协助**；并说明「我们希望你有」的三点要求与四步参与流程。

申请表字段结构参考 **Best Friends Animal Society《Volunteer Engagement》** 指南，
该指南强调申请表除基本个人信息外，应给申请人充分机会描述其**知识、技能与专长**，
并配套志愿者手册与安全指南确认。据此设计为五个分组：

| 分组 | 字段 |
| --- | --- |
| 一、基本信息 | 姓名、邮箱、电话、所在城市、职业 / 专业、是否已满 18 周岁、监护人姓名 |
| 二、技能与专长 | 8 项技能多选、其他技能或相关资格 |
| 三、工作与时间 | 10 项工作内容多选、5 项可服务时段、时间投入承诺、可开始服务日期 |
| 四、经历与意愿 | 过往志愿服务经历、加入动机 |
| 五、健康与紧急联系 | 体力工作确认、志愿者手册与安全指南同意、紧急联系人及电话 |

提交后进入回执页（`VOL-YYYYMMDD-NNNN`），展示申请编号、技能与意向标签及后续流程四步。

### 3. 爱心捐款（`GET|POST /<lang>/charity/donate`）

- **捐赠方式**：一次性捐赠 / 每月定期捐赠（卡片式单选）。
- **捐赠金额**：预设 **5 个档位（10 / 25 / 50 / 75 / 100 元）**，或选择「自定义金额」
  手动输入；服务端同时校验档位与自定义金额的合法性。
- **捐赠人信息**：称呼、邮箱、捐赠用途（5 种，含「不限用途」）、留言、匿名捐赠。
- 页面右侧展示捐款去向说明、最近捐赠动态与汇总数据（累计金额 / 每月定期金额 / 笔数 / 人数）。
- 首页行动号召区的「我要捐赠」按钮直达本页。
- 演示站点不接入真实支付渠道，提交后仅生成状态为「待扣款」的捐赠意向记录，
  回执页按周期给出不同的后续说明（一次性付款 vs 定期签约）。
- `GET /<lang>/charity/donations` 为捐赠记录列表页，含汇总卡片与分页表格。

## 语言版本

站点所有页面都有中英两个版本，语言由 URL 的第一段路径决定：

| 语言 | 首页 | 领养检索 |
| --- | --- | --- |
| 中文 | `/zh/` | `/zh/adoption/pets` |
| English | `/en/` | `/en/adoption/pets` |

- 访问根路径 `/` 会依据「上次选择 → 浏览器 Accept-Language → 默认中文」的顺序重定向到对应语言。
- 导航条右侧提供语言切换器，切换时会**保留当前路径参数与全部查询参数**。
- 翻译目录位于 `src/vv_pet01/translations/en/LC_MESSAGES/messages.po`，
  以**中文作为 msgid**，因此中文无需翻译目录，只需维护一份英文目录。
- `.mo` 文件不纳入版本管理：应用启动时若发现 `.mo` 缺失或早于 `.po`，会自动编译一次。

### 翻译维护工作流

```bash
# 1. 抽取代码与模板中的字面量文案，更新基准文件
pybabel extract -F babel.cfg -o messages.pot src/vv_pet01

# 2. 补齐 .po 中的英文翻译
#    注意：通过 _(变量) 翻译的受控词表（类别、品种、性格标签、相处对象、城市、
#    表单选项等）不会被自动抽取，需要手工维护在 messages.po 中

# 3. 重新启动应用即可，.mo 会自动编译；也可手动编译：
pybabel compile -d src/vv_pet01/translations
```

## 数据模型（SQLite）

数据库文件默认位于 Flask 实例目录，首次启动自动建表并写入种子数据。
src-layout 下以 `pip install -e .` 安装时，实际路径为 `src/instance/vv_pet01.sqlite`；
也可用 `VV_PET01_DATABASE` 显式指定（容器内固定为 `/app/instance/vv_pet01.sqlite`）。

| 表 | 说明 | 记录数 |
| --- | --- | --- |
| `shelters` | 合作救助站档案（含经纬度） | 6 |
| `pets` | 待领养宠物档案（狗 20 / 猫 10 / 其他宠物 5） | 35 |
| `applications` | 领养申请记录 | 运行时产生 |
| `rescue_reports` | 动物救助工单（含照片路径、位置与三种状态） | 运行时产生 |
| `volunteer_applications` | 志愿者申请记录 | 运行时产生 |
| `donations` | 爱心捐赠记录（演示用，不含真实支付） | 运行时产生 |

- **多物种单表**：狗、猫与其他宠物统一存放于 `pets` 表，由 `species` 区分，
  这是「合并领养界面」的数据基础。
- **双语字段**：自由文本采用中英成对列（`name` / `name_en`、`address` / `address_en`、
  `description` / `description_en`），仓储层按当前请求语言挑选并输出单一值。
- **受控词表**：类别、品种、性别、体型、状态、性格标签、相处对象、城市、区县只存中文规范值，
  展示时通过 gettext 翻译。好处是筛选条件与数据库取值始终一致，也无需维护两份枚举列。
- **多值字段**：性格标签、相处对象，以及申请表中的家中宠物 / 沟通话题 / 额外服务，
  均以 JSON 数组字符串存储（相处对象筛选使用带引号的 LIKE 精确命中某一项）。
- **并发写入**：连接启用 `PRAGMA journal_mode=WAL` 与 `busy_timeout=5000`，
  缓解多 Gunicorn worker 并发写时的 `database is locked`。

## 技术栈

- **语言 / 运行时**：Python 3.11+
- **Web 框架**：Flask 3.x（应用工厂 + Blueprint，Jinja2 模板引擎）
- **数据库**：SQLite（标准库 `sqlite3`，无 ORM）
- **国际化**：Flask-Babel 4.x + gettext `.po`/`.mo` + URL 语言前缀
- **表单**：Flask-WTF / WTForms（内置 CSRF 保护）
- **生产 WSGI 服务器**：Gunicorn（`gthread` worker）
- **前端**：Jinja2 模板 + Bootstrap 5（CDN）+ 自定义 CSS（蓝白主题）+ 少量原生 JS 渐进增强
- **地图**：Leaflet 1.9（CDN）+ OpenStreetMap 瓦片，用于动物救助页展示最近救助站与距离
- **打包规范**：src-layout + PEP 517（hatchling）+ PEP 621 `pyproject.toml`
- **容器化**：Dockerfile + docker-compose.yml（SQLite 数据卷持久化）
- **注释风格**：Google 风格 docstring

## 目录结构

```
pet_web1/
├── pyproject.toml              # PEP 621 项目元数据与依赖声明
├── wsgi.py                     # 容器内 WSGI 入口（暴露 app 对象）
├── gunicorn.conf.py            # Gunicorn 运行配置
├── babel.cfg                   # Babel 文案抽取配置
├── messages.pot                # 抽取基准（由 pybabel extract 生成）
├── Dockerfile                  # 容器镜像构建文件
├── docker-compose.yml          # 服务编排配置（含 SQLite 数据卷）
├── update.sh                   # 一键更新脚本：拉取代码并重建、重启 Docker 服务
├── .gitignore / .dockerignore  # 忽略规则
└── src/
    └── vv_pet01/
        ├── __init__.py         # 应用工厂：装配 i18n / db / csrf / 蓝图 / 错误处理
        ├── config.py           # 开发 / 测试 / 生产环境配置类
        ├── db.py               # SQLite 连接管理、建表、种子数据与 CLI 命令
        ├── schema.sql          # 六张表的结构定义
        ├── i18n.py             # URL 语言前缀、翻译目录编译与语言切换器
        ├── forms.py            # 领养申请 / 救助上报 / 志愿者 / 捐款表单与校验规则
        ├── navigation.py       # 全站导航菜单结构（中文即 msgid）
        ├── blueprints/         # 业务蓝图（main / adoption / protection / charity）
        ├── data/               # 种子数据与受控词表
        │   ├── taxonomy.py     # 类别 / 品种 / 相处对象 / 体型 / 年龄段等词表
        │   ├── cities.py       # 城市中心坐标（用于按所在地算距离）
        │   ├── shelters.py     # 救助站档案（含经纬度，中英字段）
        │   ├── pets.py         # 宠物档案（狗 / 猫 / 其他宠物，中英字段）
        │   ├── stories.py      # 首页「救助故事」人宠合照图库（按类别分组）
        │   └── seed.py         # 种子数据到数据库行的装配
        ├── services/           # 业务服务层
        │   ├── adoption.py     # 检索、距离计算、附近救助站、分页、领养申请持久化
        │   └── charity.py      # 救助工单、附近救助站、志愿者申请、捐赠持久化与汇总
        ├── translations/
        │   └── en/LC_MESSAGES/messages.po   # 英文翻译目录
        ├── templates/
        │   ├── base.html       # 全站布局基类（导航 + 语言切换器 + 页脚）
        │   ├── index.html      # 首页
        │   ├── page.html       # 通用占位模板
        │   ├── adoption/
        │   │   ├── pets.html           # 宠物领养检索页（合并界面）
        │   │   ├── pet_detail.html     # 宠物详情页
        │   │   ├── apply.html          # 领养申请表
        │   │   ├── apply_success.html  # 申请回执页
        │   │   └── applications.html   # 申请记录列表页
        │   └── charity/
        │       ├── rescue.html             # 动物救助（说明 + 地图 + 上报表单）
        │       ├── rescue_success.html     # 救助工单回执
        │       ├── rescue_reports.html     # 救助工单列表（推进状态）
        │       ├── volunteer.html          # 成为志愿者（介绍 + 申请表）
        │       ├── volunteer_success.html  # 志愿者申请回执
        │       ├── donate.html             # 爱心捐款
        │       ├── donate_success.html     # 捐赠回执
        │       └── donations.html          # 捐赠记录列表
        └── static/css/style.css  # 蓝白主题自定义样式
```

## 快速开始

### 1. 创建虚拟环境并安装

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. 初始化数据库（可选）

首次启动时会自动建表并写入种子数据，通常无需手动执行。如需重置：

```bash
flask --app wsgi:app init-db       # 仅创建表结构
flask --app wsgi:app seed-db       # 清空并重新写入救助站与宠物种子数据
```

### 3. 启动服务

```bash
# 开发模式
flask --app wsgi:app run --debug --port 8000

# 生产模式（与容器内一致）
gunicorn -c gunicorn.conf.py wsgi:app
```

启动后访问：<http://127.0.0.1:8000>（会自动跳转到 `/zh/`）

### 4. 快速体验

```bash
# 合并后的领养检索（可叠加所在地与距离）
open "http://127.0.0.1:8000/zh/adoption/pets?city=上海市&radius=25&species=猫"

# 某只宠物的领养申请表
open http://127.0.0.1:8000/zh/adoption/pets/21/apply

# 已提交的申请记录
open http://127.0.0.1:8000/zh/adoption/applications
```

## Docker 运行

```bash
docker compose up --build -d       # 构建并后台启动
docker compose logs -f web         # 查看日志
docker compose down                # 停止并移除
```

- 容器内由 Gunicorn 监听 `0.0.0.0:8000`，日志输出到标准输出，便于采集。
- SQLite 数据库落在 `/app/instance`，通过具名数据卷 `vv_pet01_data` 持久化，容器重建后申请记录不丢失。

### 一键更新（update.sh）

在部署机上执行 `./update.sh` 即可完成「拉取最新代码 → 重新构建镜像 → 滚动重启 → 健康检查 → 清理旧镜像」的全流程：

```bash
./update.sh                # 标准更新：git pull + 重建镜像 + 滚动重启
./update.sh --skip-pull    # 跳过 git pull，仅用当前代码重建并重启
./update.sh --no-cache     # 不使用 Docker 层缓存重建（排查构建问题时用）
./update.sh --help         # 查看用法
```

脚本行为要点：

- **安全拉取**：工作区有未提交改动时中止（避免覆盖本地修改），`git pull --ff-only` 防止意外合并；
  可通过 `GIT_BRANCH` / `GIT_REMOTE` 环境变量指定分支与远端。
- **失败不中断服务**：镜像构建失败时旧容器继续运行；构建成功才执行 `up -d` 滚动重建。
- **健康检查**：重启后轮询容器 HEALTHCHECK 状态（默认最长 90s，可用 `HEALTH_TIMEOUT` 调整），
  超时则输出容器日志并退出非零，便于接入 CI/CD 或 crontab。
- **数据安全**：数据库与上传文件在数据卷 `vv_pet01_data` 中，更新全程不受影响。
- **磁盘清理**：每次更新后自动清理悬空旧镜像。

## 配置项

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `FLASK_CONFIG` | 配置环境：`development` / `testing` / `production` | `development` |
| `SECRET_KEY` | 会话与 CSRF 签名密钥，生产环境必须显式注入 | 开发用占位值；生产环境缺失时随机生成并告警 |
| `VV_PET01_DATABASE` | SQLite 数据库文件路径 | 实例目录下的 `vv_pet01.sqlite` |
| `VV_PET01_LANG` | 默认语言（`zh` / `en`） | `zh` |
| `MAX_CONTENT_LENGTH`（配置项，非环境变量） | 单次请求体上限，即救助照片大小上限 | 5 MB |
| `GUNICORN_BIND` | Gunicorn 监听地址 | `0.0.0.0:8000` |
| `GUNICORN_WORKERS` | Gunicorn 工作进程数 | CPU 核心数 × 2 + 1 |
| `GUNICORN_THREADS` | 每个进程的线程数 | `2` |
| `GUNICORN_LOG_LEVEL` | 日志级别 | `info` |

## 路由清单

| 路由 | 说明 |
| --- | --- |
| `/` | 语言重定向（302） |
| `/<lang>/` | 首页 |
| `/<lang>/adoption/pets` | 宠物领养检索（合并界面） |
| `/<lang>/adoption/pets/<id>` | 宠物详情 |
| `/<lang>/adoption/pets/<id>/apply` | 领养申请表（GET / POST） |
| `/<lang>/adoption/applications` | 申请记录列表 |
| `/<lang>/adoption/applications/<id>` | 申请回执 |
| `/<lang>/adoption/process` | 领养流程 |
| `/<lang>/adoption/dogs`、`cats`、`others` | 旧入口 → 301 重定向到检索页并预选类别 |
| `/<lang>/protection/welfare`、`anti-cruelty`、`disaster-rescue` | 占位页面 |
| `/<lang>/charity/rescue` | 动物救助（说明 + 定位地图 + 救助申请表，GET / POST） |
| `/<lang>/charity/rescue/<id>` | 救助工单回执 |
| `/<lang>/charity/rescue/reports` | 救助工单列表（工作人员推进状态） |
| `POST /<lang>/charity/rescue/reports/<id>/advance` | 推进工单状态 |
| `/<lang>/charity/uploads/<filename>` | 读取救助现场照片 |
| `/<lang>/charity/volunteer` | 成为志愿者（介绍 + 申请表，GET / POST） |
| `/<lang>/charity/volunteer/<id>` | 志愿者申请回执 |
| `/<lang>/charity/donate` | 爱心捐款（一次性 / 每月定期，GET / POST） |
| `/<lang>/charity/donate/<id>` | 捐赠回执 |
| `/<lang>/charity/donations` | 捐赠记录列表 |
| `/<lang>/charity/activities`、`foster` | 已移出导航的占位页面 |

## 上传文件

动物救助的现场照片保存在 `Flask 实例目录/uploads/`（容器内为 `/app/instance/uploads/`），
数据库只记录相对路径。该目录与 SQLite 数据库同处一个数据卷，**备份数据库时需一并备份**。
`.gitignore` / `.dockerignore` 已忽略 `instance/`，因此上传文件不会进入版本库与镜像。

## 后续规划

- 领养申请与救助工单的登录保护及后台管理界面（当前工单状态推进页面无鉴权，仅用于演示）
- 接入地理编码服务，把手填地址解析为精确坐标（当前仅按城市名粗定位）
- 接入真实支付渠道完成捐赠扣款，并为每月定期捐赠提供暂停 / 取消入口
- 将受控词表迁移到独立字典表，支持后台维护
- 允许多选宠物类别（当前为单选，切换会清空不适用条件）

## 许可证

本项目基于 [MIT License](LICENSE) 开源。
