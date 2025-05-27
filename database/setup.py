from datetime import datetime

import aiosqlite

from config import logger


async def init_db():
    """SQLite 데이터베이스 초기화."""
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
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS username_cache (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            """
            )
            await conn.commit()
        logger.info("database_initialized", db_path="data/bot.db")
    except Exception as e:
        logger.error("database_init_error", error=str(e))
        raise
