"""SQLite 数据访问基础设施模块。

提供连接管理、建表与种子数据初始化能力，供仓储层（``vv_pet01.services``）
与 Flask CLI 命令复用。所有连接按请求维度复用并随应用上下文销毁。

Typical usage example::

    from vv_pet01.db import get_db

    rows = get_db().execute("SELECT * FROM dogs").fetchall()

命令行用法::

    flask --app wsgi:app init-db     # 仅建表
    flask --app wsgi:app seed-db     # 建表并写入种子数据
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import click
from flask import Flask, current_app, g

#: 数据库文件名，存放于 Flask 实例目录下。
DB_FILENAME: str = "vv_pet01.sqlite"

#: 建表脚本路径。
SCHEMA_PATH: Path = Path(__file__).with_name("schema.sql")


def _resolve_database_path(app: Flask) -> str:
    """解析数据库文件路径。

    优先级：环境变量 ``VV_PET01_DATABASE`` > 已存在的 ``DATABASE`` 配置 >
    实例目录下的默认文件名。若配置值形如 ``sqlite:///...`` 会被自动剥离前缀。

    Args:
        app: Flask 应用实例。

    Returns:
        数据库文件的绝对路径。
    """
    env_path = os.environ.get("VV_PET01_DATABASE")
    configured = app.config.get("DATABASE")
    candidate = env_path or configured
    if not candidate:
        return str(Path(app.instance_path) / DB_FILENAME)

    candidate = str(candidate)
    if candidate == ":memory:":
        return candidate

    prefix = "sqlite:///"
    if candidate.startswith(prefix):
        candidate = candidate[len(prefix) :]
    return str(Path(candidate).expanduser().resolve())


def get_db() -> sqlite3.Connection:
    """获取当前请求上下文中的数据库连接。

    连接在首次调用时创建并缓存到 ``flask.g``，请求结束时自动关闭。

    Returns:
        已启用外键约束与 ``Row`` 行工厂的 SQLite 连接。
    """
    if "db" not in g:
        connection = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        # 多 worker 并发写入时减少 "database is locked"：开启忙等待，
        # 文件型数据库额外启用 WAL 日志模式（内存库不支持 WAL）
        connection.execute("PRAGMA busy_timeout = 5000")
        if current_app.config.get("DATABASE") != ":memory:":
            connection.execute("PRAGMA journal_mode = WAL")
        g.db = connection
    return g.db


def close_db(exception: BaseException | None = None) -> None:
    """关闭当前请求上下文中的数据库连接。

    Args:
        exception: 请求处理过程中抛出的异常，未使用时忽略。
    """
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> None:
    """按 ``schema.sql`` 创建全部数据表。

    脚本中使用 ``CREATE TABLE IF NOT EXISTS``，可重复执行。
    """
    connection = get_db()
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    connection.commit()


def is_seeded() -> bool:
    """判断数据库是否已写入种子数据。

    Returns:
        当 ``pets`` 表存在至少一条记录时返回 ``True``。
    """
    row = get_db().execute("SELECT COUNT(*) AS total FROM pets").fetchone()
    return bool(row and row["total"])


def seed_db(force: bool = False) -> int:
    """把内置的救助站与狗狗数据写入数据库。

    Args:
        force: 为 ``True`` 时先清空 ``shelters`` / ``pets`` 再重新写入。

    Returns:
        实际写入的宠物记录条数。
    """
    from vv_pet01.data.seed import build_seed_rows

    connection = get_db()
    shelters, pets = build_seed_rows()

    if force:
        connection.execute("DELETE FROM pets")
        connection.execute("DELETE FROM shelters")

    connection.executemany(
        """
        INSERT OR REPLACE INTO shelters (
            id, name, name_en, city, district, address, address_en,
            phone, lat, lng, founded_year, description, description_en
        ) VALUES (
            :id, :name, :name_en, :city, :district, :address, :address_en,
            :phone, :lat, :lng, :founded_year, :description, :description_en
        )
        """,
        shelters,
    )
    connection.executemany(
        """
        INSERT OR REPLACE INTO pets (
            id, species, name, name_en, breed, gender, age_months, size,
            weight_kg, shelter_id, status, vaccinated, neutered, traits,
            companions, description, description_en, image, intake_date
        ) VALUES (
            :id, :species, :name, :name_en, :breed, :gender, :age_months, :size,
            :weight_kg, :shelter_id, :status, :vaccinated, :neutered, :traits,
            :companions, :description, :description_en, :image, :intake_date
        )
        """,
        pets,
    )
    connection.commit()
    return len(pets)


def ensure_initialized() -> None:
    """确保数据库可用：缺失时建表，为空时写入种子数据。

    该方法在应用工厂中调用一次，使演示站点无需手动初始化即可运行。
    """
    init_db()
    if not is_seeded():
        seed_db()


def init_app(app: Flask) -> None:
    """把数据库能力挂载到应用实例。

    完成三件事：解析数据库路径并预先创建目录、注册连接回收钩子、
    注册 ``init-db`` 与 ``seed-db`` 两个 CLI 命令。

    Args:
        app: 需要初始化数据库能力的 Flask 应用实例。
    """
    database_path = _resolve_database_path(app)
    if database_path != ":memory:":
        # 只创建数据库文件所在目录；不主动创建 Flask 默认实例目录，
        # 以免在只读的 site-packages 场景（容器内 pip install 安装）下报权限错误
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    app.config["DATABASE"] = database_path

    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """创建数据库表结构。"""
        init_db()
        click.echo(f"数据库已初始化：{app.config['DATABASE']}")

    @app.cli.command("seed-db")
    def seed_db_command() -> None:
        """写入或刷新演示用的种子数据。"""
        init_db()
        total = seed_db(force=True)
        click.echo(f"已写入 {total} 条宠物数据：{app.config['DATABASE']}")
