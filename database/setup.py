import json
import os
from datetime import datetime

import aiosqlite

from config import ADMINS_FILE, BANNED_USERS_FILE, GROUPS_FILE, logger


async def init_db():
    """SQLite 데이터베이스 초기화 및 JSON 데이터 마이그레이션."""
    try:
        async with aiosqlite.connect("data/bot.db") as conn:
            # 테이블 생성
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS groups (
                    chat_id TEXT PRIMARY KEY,
                    title TEXT,
                    added_by INTEGER,
                    added_at TEXT,
                    notification BOOLEAN
                )
            """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    admin_id INTEGER,
                    admin_username TEXT,
                    reason TEXT,
                    chat_id INTEGER,
                    timestamp TEXT
                )
            """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    admin_id TEXT PRIMARY KEY,
                    username TEXT,
                    added_by_id INTEGER,
                    added_by_username TEXT,
                    timestamp TEXT
                )
            """
            )
            await conn.commit()

            # JSON 데이터 마이그레이션
            await migrate_groups(conn)
            await migrate_banned_users(conn)
            await migrate_admins(conn)

        logger.info("database_initialized", db_path="data/bot.db")
    except Exception as e:
        logger.error("database_init_error", error=str(e))
        raise


async def migrate_groups(conn):
    """groups.json 데이터를 SQLite로 마이그레이션."""
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as file:
                groups = json.load(file)
            for chat_id, data in groups.items():
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO groups (chat_id, title, added_by, added_at, notification)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chat_id,
                        data.get("title", ""),
                        data.get("added_by", 0),
                        data.get(
                            "added_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ),
                        data.get("notification", True),
                    ),
                )
            await conn.commit()
            logger.info("groups_migrated", count=len(groups))
        except Exception as e:
            logger.error("groups_migration_error", error=str(e))


async def migrate_banned_users(conn):
    """banned_users.json 데이터를 SQLite로 마이그레이션."""
    if os.path.exists(BANNED_USERS_FILE):
        try:
            with open(BANNED_USERS_FILE, "r", encoding="utf-8") as file:
                banned_users = json.load(file)
            for user_id, data in banned_users.items():
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO banned_users (user_id, username, admin_id, admin_username, reason, chat_id, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        data.get("username", ""),
                        data.get("admin_id", 0),
                        data.get("admin_username", ""),
                        data.get("reason", ""),
                        data.get("chat_id", 0),
                        data.get("timestamp", datetime.now().isoformat()),
                    ),
                )
            await conn.commit()
            logger.info("banned_users_migrated", count=len(banned_users))
        except Exception as e:
            logger.error("banned_users_migration_error", error=str(e))


async def migrate_admins(conn):
    """admins.json 데이터를 SQLite로 마이그레이션."""
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, "r", encoding="utf-8") as file:
                admins = json.load(file)
            for admin_id, data in admins.items():
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO admins (admin_id, username, added_by_id, added_by_username, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        admin_id,
                        data.get("username", ""),
                        data.get("added_by_id", 0),
                        data.get("added_by_username", ""),
                        data.get("timestamp", datetime.now().isoformat()),
                    ),
                )
            await conn.commit()
            logger.info("admins_migrated", count=len(admins))
        except Exception as e:
            logger.error("admins_migration_error", error=str(e))
