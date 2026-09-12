-- vv_pet01 数据库结构定义（SQLite）
--
-- 设计说明：
--   * 自由文本字段采用中英成对列（``xxx`` 中文 / ``xxx_en`` 英文），仓储层按
--     当前请求语言挑选字段并输出单一值，页面无需感知差异。
--   * 受控词表字段（品种 / 性别 / 体型 / 状态 / 性格标签 / 城市 / 区县）以中文
--     作为规范值存储，展示时通过 gettext 翻译。好处是筛选条件与数据库取值
--     始终一致，也避免为同一批枚举值维护两份列。
--   * 多选类字段以 JSON 数组字符串存储，避免演示项目引入额外关联表。

-- 救助站档案
CREATE TABLE IF NOT EXISTS shelters (
    id              TEXT PRIMARY KEY,
    name            TEXT    NOT NULL,
    name_en         TEXT    NOT NULL,
    city            TEXT    NOT NULL,
    district        TEXT    NOT NULL,
    address         TEXT    NOT NULL,
    address_en      TEXT    NOT NULL,
    phone           TEXT    NOT NULL,
    lat             REAL    NOT NULL,
    lng             REAL    NOT NULL,
    founded_year    INTEGER NOT NULL,
    description     TEXT    NOT NULL,
    description_en  TEXT    NOT NULL
);

-- 待领养狗狗档案
CREATE TABLE IF NOT EXISTS dogs (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    name_en     TEXT    NOT NULL,
    breed       TEXT    NOT NULL,
    gender      TEXT    NOT NULL,
    age_months  INTEGER NOT NULL,
    size        TEXT    NOT NULL,
    weight_kg   REAL    NOT NULL,
    shelter_id  TEXT    NOT NULL REFERENCES shelters (id) ON DELETE CASCADE,
    status      TEXT    NOT NULL,
    vaccinated  INTEGER NOT NULL DEFAULT 0,
    neutered    INTEGER NOT NULL DEFAULT 0,
    traits      TEXT    NOT NULL DEFAULT '[]',
    description TEXT    NOT NULL,
    description_en TEXT NOT NULL,
    image       TEXT    NOT NULL,
    -- 救助人 / 领养人与宠物的合照，用于首页「救助故事」区块；为空时回退到 image
    story_image TEXT    NOT NULL DEFAULT '',
    intake_date TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dogs_shelter ON dogs (shelter_id);
CREATE INDEX IF NOT EXISTS idx_dogs_status ON dogs (status);
CREATE INDEX IF NOT EXISTS idx_dogs_breed ON dogs (breed);

-- 领养申请记录（参考 Humane World "Adopters Welcome" 样本问卷设计）
CREATE TABLE IF NOT EXISTS applications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    reference           TEXT    NOT NULL UNIQUE,
    dog_id              INTEGER REFERENCES dogs (id) ON DELETE SET NULL,
    dog_name            TEXT,
    dog_name_en         TEXT,
    applicant_name      TEXT    NOT NULL,
    address             TEXT    NOT NULL DEFAULT '',
    town_state_zip      TEXT    NOT NULL DEFAULT '',
    email               TEXT    NOT NULL,
    preferred_phone     TEXT    NOT NULL DEFAULT '',
    preferred_contact   TEXT    NOT NULL DEFAULT '',
    is_gift             INTEGER NOT NULL DEFAULT 0,
    household_members   TEXT    NOT NULL DEFAULT '',
    pets_at_home        TEXT    NOT NULL DEFAULT '[]',
    other_info          TEXT    NOT NULL DEFAULT '',
    discussion_topics   TEXT    NOT NULL DEFAULT '[]',
    other_questions     TEXT    NOT NULL DEFAULT '',
    extra_services      TEXT    NOT NULL DEFAULT '[]',
    locale              TEXT    NOT NULL DEFAULT 'zh',
    status              TEXT    NOT NULL DEFAULT 'submitted',
    created_at          TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_applications_created ON applications (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_dog ON applications (dog_id);
