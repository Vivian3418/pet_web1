# vv_pet01

> 让每一个生命都被温柔以待。 / Let every life be met with gentleness.

`vv_pet01` 是一个以 **动物保护、宠物救助、宠物领养** 为核心的公益网站模拟系统。
站点采用简洁的蓝白配色与下拉式导航，提供领养、保护与公益参与三大板块的完整入口。

当前已完成的能力：

- **领养狗狗**：多条件搜索、狗狗详情、按「附近救助站」距离排序
- **领养申请表**：参考 Humane World《Adopters Welcome: Sample Questionnaire》设计，
  从「我要领养」按钮直达，提交后生成申请回执与申请记录列表
- **中英双语**：全站文案双语，通过 URL 语言前缀切换（`/zh/...` 与 `/en/...`）
- **SQLite 持久化**：救助站、狗狗、领养申请三张表，首次启动自动建表并写入种子数据

其余子页面为占位页面，仅展示页面名称。

## 语言版本

站点所有页面都有中英两个版本，语言由 URL 的第一段路径决定：

| 语言 | 首页 | 领养狗狗搜索 |
| --- | --- | --- |
| 中文 | `/zh/` | `/zh/adoption/dogs` |
| English | `/en/` | `/en/adoption/dogs` |

- 访问根路径 `/` 会依据「上次选择 → 浏览器 Accept-Language → 默认中文」的顺序重定向到对应语言。
- 导航条右侧提供语言切换器，切换时会**保留当前路径参数与全部查询参数**
  （例如 `/zh/adoption/dogs?city=上海市&size=大型` → `/en/adoption/dogs?city=上海市&size=大型`）。
- 翻译目录位于 `src/vv_pet01/translations/en/LC_MESSAGES/messages.po`，
  以**中文作为 msgid**，因此中文无需翻译目录，只需维护一份英文目录。
- `.mo` 文件不纳入版本管理：应用启动时若发现 `.mo` 缺失或早于 `.po`，会自动编译一次。

### 翻译维护工作流

```bash
# 1. 抽取代码与模板中的字面量文案，更新基准文件
pybabel extract -F babel.cfg -o messages.pot src/vv_pet01

# 2. 补齐 .po 中的英文翻译
#    注意：通过 _(变量) 翻译的受控词表（品种、性格标签、城市、表单选项等）
#    不会被自动抽取，需要手工维护在 messages.po 中

# 3. 重新启动应用即可，.mo 会自动编译；也可手动编译：
pybabel compile -d src/vv_pet01/translations
```

## 功能板块

顶部导航采用下拉式菜单结构：

| 一级菜单 | 二级菜单 | 实现状态 |
| --- | --- | --- |
| 首页 | — | 已实现 |
| 领养宠物 | 领养狗狗 / 领养猫咪 / 其他宠物 / 领养流程 | **领养狗狗已实现搜索与领养申请**，其余为占位页 |
| 动物保护 | 动物福利 / 反动物虐待 / 灾害动物救助 | 占位页 |
| 参与公益 | 成为志愿者 / 公益活动 / 捐赠 / 寄养宠物 | 占位页 |

占位页面复用统一的占位模板，并带有面包屑导航与当前板块高亮。

## 首页结构

首页自上而下由四个区块组成：

1. **Hero**：站点品牌、公益标语、关键数据与狗狗配图。
2. **领养流程**：四步流程图（在线提交申请 → 救助站联系沟通 → 见面与匹配 → 签署协议与交接），
   桌面端横向排列并带连接箭头，窄屏自动转为纵向排列。
3. **行动号召**：捐赠与寄养入口。
4. **救助故事**：页面最底端的横向滚动图片卡片，每张卡片展示狗狗照片、品种与城市、
   呼名与救助经历，并可跳转到详情页发起领养申请。支持鼠标滚轮 / 触屏滑动 / 键盘左右键
   （容器可聚焦），并带有滚动吸附（scroll-snap）。

## 领养狗狗搜索功能

### 1. 多条件搜索（`GET /<lang>/adoption/dogs`）

| 条件 | 说明 |
| --- | --- |
| 关键词 `q` | 模糊匹配呼名、品种、性格标签、救助故事与救助站信息 |
| 城市 `city` | 按救助站所在城市筛选 |
| 品种 `breed` | 精确匹配品种 |
| 体型 `size` | 小型 / 中型 / 大型 |
| 性别 `gender` | 公 / 母 |
| 年龄 `age` | `puppy`（1 岁以下）/ `young`（1-3 岁）/ `adult`（3-7 岁）/ `senior`（7 岁以上） |
| 状态 `status` | 默认仅展示「待领养」，可切换为审核中或已领养 |
| 排序 `sort` | `distance`（距离最近）/ `latest`（最新发布）/ `age_asc` / `name` |
| 分页 `page` | 每页 9 条 |

筛选条件通过 URL 查询参数传递，可直接分享或收藏搜索结果链接。

### 2. 附近救助站（`lat` + `lng`）

- 侧栏列出当前筛选条件下仍有在养狗狗的合作救助站，并统计其在养数量。
- 点击「使用我的位置」调用浏览器 Geolocation API，把经纬度写入 URL（`?lat=&lng=`），
  页面随即用 Haversine 公式计算每家救助站与用户的球面距离，并在卡片上标注「距你 X km」。
- 已定位时默认按距离升序排列，救助站列表同样按由近到远排序。
- 该能力为渐进增强：不授权定位时，仍可通过城市与救助站筛选正常使用全部功能。

### 3. 狗狗详情（`GET /<lang>/adoption/dogs/<dog_id>`）

展示品种、性别、年龄、体型体重、疫苗与绝育情况、性格标签、救助故事，
以及所属救助站的城市、地址、电话、成立年份与距离；编号不存在时返回 404。
详情页主行动按钮为 **「我要领养」**，直接进入领养申请表。

## 领养申请表

### 入口（不新增导航菜单项）

| 位置 | 按钮 | 跳转目标 |
| --- | --- | --- |
| 搜索结果卡片 | 我要领养 | `/<lang>/adoption/dogs/<dog_id>/apply` |
| 狗狗详情页 | 我要领养 | 同上（动物呼名预填为该狗狗） |

### 表单结构

字段结构参考 Humane World for Animals 发布的 **Adopters Welcome: Sample Questionnaire**，
按五个部分分组：

1. **领养对象**：动物呼名（从详情页自动预填，可修改）
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
- 申请记录会保存狗狗名称快照，即使后续重新灌入种子数据，历史申请仍可正常展示。

## 数据模型（SQLite）

数据库文件默认位于 Flask 实例目录，首次启动自动建表并写入种子数据。
src-layout 下以 `pip install -e .` 安装时，实际路径为 `src/instance/vv_pet01.sqlite`；
也可用 `VV_PET01_DATABASE` 显式指定（容器内固定为 `/app/instance/vv_pet01.sqlite`）。

| 表 | 说明 | 记录数 |
| --- | --- | --- |
| `shelters` | 合作救助站档案（含经纬度） | 6 |
| `dogs` | 待领养狗狗档案 | 20 |
| `applications` | 领养申请记录 | 运行时产生 |

- **双语字段**：自由文本采用中英成对列（`name` / `name_en`、`address` / `address_en`、
  `description` / `description_en`），仓储层按当前请求语言挑选并输出单一值。
- **受控词表**：品种、性别、体型、状态、性格标签、城市、区县只存中文规范值，
  展示时通过 gettext 翻译。好处是筛选条件与数据库取值始终一致，也无需维护两份枚举列。
- **多值字段**：家中宠物、沟通话题、额外服务以 JSON 数组字符串存储。
- **并发写入**：连接启用 `PRAGMA journal_mode=WAL` 与 `busy_timeout=5000`，
  缓解多 Gunicorn worker 并发写时的 `database is locked`。

## 技术栈

- **语言 / 运行时**：Python 3.11+
- **Web 框架**：Flask 3.x（应用工厂 + Blueprint，Jinja2 模板引擎）
- **数据库**：SQLite（标准库 `sqlite3`，无 ORM）
- **国际化**：Flask-Babel 4.x + gettext `.po`/`.mo` + URL 语言前缀
- **表单**：Flask-WTF / WTForms（内置 CSRF 保护）
- **生产 WSGI 服务器**：Gunicorn（`gthread` worker）
- **前端**：Jinja2 模板 + Bootstrap 5（CDN）+ 自定义 CSS（蓝白主题）
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
├── .gitignore / .dockerignore  # 忽略规则
└── src/
    └── vv_pet01/
        ├── __init__.py         # 应用工厂：装配 i18n / db / csrf / 蓝图 / 错误处理
        ├── config.py           # 开发 / 测试 / 生产环境配置类
        ├── db.py               # SQLite 连接管理、建表、种子数据与 CLI 命令
        ├── schema.sql          # 三张表的结构定义
        ├── i18n.py             # URL 语言前缀、翻译目录编译与语言切换器
        ├── forms.py            # 领养申请表（WTForms）与校验规则
        ├── navigation.py       # 全站导航菜单数据结构（中文即 msgid）
        ├── blueprints/         # 业务蓝图（main / adoption / protection / charity）
        ├── data/               # 种子数据与受控词表常量
        │   ├── shelters.py     # 救助站档案（含经纬度，中英字段）
        │   ├── dogs.py         # 待领养狗狗档案与筛选项常量
        │   └── seed.py         # 种子数据到数据库行的装配
        ├── services/           # 业务服务层
        │   └── adoption.py     # 狗狗搜索、距离计算、救助站统计、分页、申请持久化
        ├── translations/
        │   └── en/LC_MESSAGES/messages.po   # 英文翻译目录
        ├── templates/
        │   ├── base.html       # 全站布局基类（下拉导航 + 语言切换器 + 页脚）
        │   ├── index.html      # 首页
        │   ├── page.html       # 通用占位模板
        │   └── adoption/
        │       ├── dogs.html           # 领养狗狗搜索页
        │       ├── dog_detail.html     # 狗狗详情页
        │       ├── apply.html          # 领养申请表
        │       ├── apply_success.html  # 申请回执页
        │       └── applications.html   # 申请记录列表页
        └── static/css/style.css  # 蓝白主题自定义样式
```

## 快速开始

### 1. 创建虚拟环境并安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 以可编辑模式安装项目（含 Flask、Flask-Babel、Flask-WTF、Gunicorn 等依赖）
pip install -e .
```

### 2. 初始化数据库（可选）

首次启动时会自动建表并写入种子数据，通常无需手动执行。如需重置：

```bash
flask --app wsgi:app init-db       # 仅创建表结构
flask --app wsgi:app seed-db       # 清空并重新写入救助站与狗狗种子数据
```

### 3. 启动服务

开发模式（Flask 内置服务器，自动重载）：

```bash
flask --app wsgi:app run --debug --port 8000
```

生产模式（Gunicorn，与容器内一致）：

```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

启动后访问：<http://127.0.0.1:8000>（会自动跳转到 `/zh/`）

### 4. 快速体验领养申请

```bash
# 打开某只狗狗的领养申请表
open http://127.0.0.1:8000/zh/adoption/dogs/1/apply

# 查看已提交的申请记录
open http://127.0.0.1:8000/zh/adoption/applications
```

## Docker 运行

```bash
# 构建并后台启动
docker compose up --build -d

# 查看日志
docker compose logs -f web

# 停止并移除
docker compose down
```

- 容器内由 Gunicorn 监听 `0.0.0.0:8000`，访问日志与错误日志输出到标准输出，便于日志采集。
- SQLite 数据库落在 `/app/instance`，通过具名数据卷 `vv_pet01_data` 持久化，容器重建后申请记录不丢失。
- 健康检查会请求 `/`，由语言重定向返回 200。

## 配置项

配置通过环境变量注入，容器内默认使用 `production`：

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `FLASK_CONFIG` | 配置环境：`development` / `testing` / `production` | `development` |
| `SECRET_KEY` | 会话与 CSRF 签名密钥，生产环境必须显式注入 | 开发用占位值；生产环境缺失时随机生成并告警 |
| `VV_PET01_DATABASE` | SQLite 数据库文件路径 | 实例目录下的 `vv_pet01.sqlite` |
| `VV_PET01_LANG` | 默认语言（`zh` / `en`） | `zh` |
| `GUNICORN_BIND` | Gunicorn 监听地址 | `0.0.0.0:8000` |
| `GUNICORN_WORKERS` | Gunicorn 工作进程数 | CPU 核心数 × 2 + 1 |
| `GUNICORN_THREADS` | 每个进程的线程数 | `2` |
| `GUNICORN_LOG_LEVEL` | 日志级别 | `info` |

## 路由清单

| 路由 | 说明 |
| --- | --- |
| `/` | 语言重定向（302） |
| `/<lang>/` | 首页 |
| `/<lang>/adoption/dogs` | 领养狗狗搜索 |
| `/<lang>/adoption/dogs/<id>` | 狗狗详情 |
| `/<lang>/adoption/dogs/<id>/apply` | 领养申请表（GET / POST） |
| `/<lang>/adoption/applications` | 申请记录列表 |
| `/<lang>/adoption/applications/<id>` | 申请回执 |
| `/<lang>/adoption/cats`、`others`、`process` | 占位页面 |
| `/<lang>/protection/welfare`、`anti-cruelty`、`disaster-rescue` | 占位页面 |
| `/<lang>/charity/volunteer`、`activities`、`donate`、`foster` | 占位页面 |

## 后续规划

- 领养申请的审核流转与状态回写（`applications.status` 已预留）
- 领养申请的登录保护与后台管理界面
- 志愿者报名、捐赠与寄养申请表单
- 将受控词表迁移到独立字典表，支持后台维护

## 许可证

本项目基于 [MIT License](LICENSE) 开源。
