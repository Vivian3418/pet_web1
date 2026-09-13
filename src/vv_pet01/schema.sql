-- vv_pet01 数据库结构定义（SQLite）
--
-- 设计说明：
--   * 自由文本字段采用中英成对列（``xxx`` 中文 / ``xxx_en`` 英文），仓储层按
--     当前请求语言挑选字段并输出单一值，页面无需感知差异。
--   * 受控词表字段（类别 / 品种 / 性别 / 体型 / 状态 / 性格标签 / 相处对象 /
--     城市 / 区县）以中文作为规范值存储，展示时通过 gettext 翻译。好处是
--     筛选条件与数据库取值始终一致，也避免为同一批枚举值维护两份列。
--   * 多值字段以 JSON 数组字符串存储，避免演示项目引入额外关联表。
--   * 狗狗、猫咪与其他宠物统一存放于 ``pets`` 表，由 ``species`` 区分，
--     以支撑「合并领养界面」的检索需求。

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

CREATE INDEX IF NOT EXISTS idx_shelters_city ON shelters (city);

-- 待领养宠物档案（狗 / 猫 / 其他宠物）
CREATE TABLE IF NOT EXISTS pets (
    id          INTEGER PRIMARY KEY,
    species     TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    name_en     TEXT    NOT NULL,
    breed       TEXT    NOT NULL,
    gender      TEXT    NOT NULL,
    age_months  INTEGER NOT NULL,
    -- 体型仅对狗生效，猫与其他宠物留空
    size        TEXT    NOT NULL DEFAULT '',
    weight_kg   REAL    NOT NULL,
    shelter_id  TEXT    NOT NULL REFERENCES shelters (id) ON DELETE CASCADE,
    status      TEXT    NOT NULL,
    vaccinated  INTEGER NOT NULL DEFAULT 0,
    neutered    INTEGER NOT NULL DEFAULT 0,
    traits      TEXT    NOT NULL DEFAULT '[]',
    -- 适合与哪些对象相处（受控词表，多选）
    companions  TEXT    NOT NULL DEFAULT '[]',
    description TEXT    NOT NULL,
    description_en TEXT NOT NULL,
    image       TEXT    NOT NULL,
    intake_date TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pets_species ON pets (species);
CREATE INDEX IF NOT EXISTS idx_pets_shelter ON pets (shelter_id);
CREATE INDEX IF NOT EXISTS idx_pets_status ON pets (status);
CREATE INDEX IF NOT EXISTS idx_pets_breed ON pets (breed);

-- 领养申请记录（参考 Humane World "Adopters Welcome" 样本问卷设计）
CREATE TABLE IF NOT EXISTS applications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    reference           TEXT    NOT NULL UNIQUE,
    pet_id              INTEGER REFERENCES pets (id) ON DELETE SET NULL,
    pet_name            TEXT,
    pet_name_en         TEXT,
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
CREATE INDEX IF NOT EXISTS idx_applications_pet ON applications (pet_id);

-- 动物救助工单（用户发现需要救助的动物后提交，由救助站跟进）
CREATE TABLE IF NOT EXISTS rescue_reports (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    reference          TEXT    NOT NULL UNIQUE,
    animal_type        TEXT    NOT NULL,
    situation          TEXT    NOT NULL,
    urgency            TEXT    NOT NULL DEFAULT '',
    -- 用户选择的处理方式：自行送往救助站 / 申请工作人员前往救助
    handling           TEXT    NOT NULL DEFAULT '',
    description        TEXT    NOT NULL DEFAULT '',
    -- 上传照片在实例目录下的相对路径；为空表示未上传
    photo_path         TEXT    NOT NULL DEFAULT '',
    address_text       TEXT    NOT NULL DEFAULT '',
    lat                REAL,
    lng                REAL,
    -- 参考点附近最近的救助站，便于指派跟进
    nearest_shelter_id TEXT REFERENCES shelters (id) ON DELETE SET NULL,
    reporter_name      TEXT    NOT NULL DEFAULT '',
    reporter_phone     TEXT    NOT NULL DEFAULT '',
    reporter_email     TEXT    NOT NULL DEFAULT '',
    handler_note       TEXT    NOT NULL DEFAULT '',
    -- 状态规范值：未被救助 / 正在救助中 / 救助成功
    status             TEXT    NOT NULL DEFAULT '未被救助',
    locale             TEXT    NOT NULL DEFAULT 'zh',
    created_at         TEXT    NOT NULL,
    updated_at         TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rescue_status ON rescue_reports (status);
CREATE INDEX IF NOT EXISTS idx_rescue_created ON rescue_reports (created_at DESC);

-- 爱心捐赠记录（演示用，不含真实支付）
CREATE TABLE IF NOT EXISTS donations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reference   TEXT    NOT NULL UNIQUE,
    donor_name  TEXT    NOT NULL DEFAULT '',
    email       TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    -- 捐赠周期：once（一次性）/ monthly（每月定期）
    frequency   TEXT    NOT NULL DEFAULT 'once',
    designation TEXT    NOT NULL DEFAULT '',
    message     TEXT    NOT NULL DEFAULT '',
    anonymous   INTEGER NOT NULL DEFAULT 0,
    locale      TEXT    NOT NULL DEFAULT 'zh',
    status      TEXT    NOT NULL DEFAULT 'pledged',
    created_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_donations_created ON donations (created_at DESC);

-- 志愿者申请记录（表单字段参考 Best Friends《Volunteer Engagement》指南）
CREATE TABLE IF NOT EXISTS volunteer_applications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    reference           TEXT    NOT NULL UNIQUE,
    full_name           TEXT    NOT NULL,
    email               TEXT    NOT NULL,
    phone               TEXT    NOT NULL DEFAULT '',
    city                TEXT    NOT NULL DEFAULT '',
    occupation          TEXT    NOT NULL DEFAULT '',
    -- 是否已成年，未成年人需监护人同意
    is_adult            INTEGER NOT NULL DEFAULT 1,
    guardian_name       TEXT    NOT NULL DEFAULT '',
    skills              TEXT    NOT NULL DEFAULT '[]',
    skill_detail        TEXT    NOT NULL DEFAULT '',
    tasks               TEXT    NOT NULL DEFAULT '[]',
    availability        TEXT    NOT NULL DEFAULT '[]',
    commitment          TEXT    NOT NULL DEFAULT '',
    start_availability  TEXT    NOT NULL DEFAULT '',
    experience          TEXT    NOT NULL DEFAULT '',
    motivation          TEXT    NOT NULL DEFAULT '',
    physical_ok         INTEGER NOT NULL DEFAULT 1,
    accept_handbook     INTEGER NOT NULL DEFAULT 0,
    emergency_name      TEXT    NOT NULL DEFAULT '',
    emergency_phone     TEXT    NOT NULL DEFAULT '',
    locale              TEXT    NOT NULL DEFAULT 'zh',
    status              TEXT    NOT NULL DEFAULT 'submitted',
    created_at          TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_volunteers_created ON volunteer_applications (created_at DESC);
