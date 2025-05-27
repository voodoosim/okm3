from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from config import logger

DATABASE = "data/bot.db"


async def execute_query(query: str, params: tuple = ()) -> None:
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute(query, params)
        await conn.commit()


async def fetch_query(query: str, params: tuple = ()) -> List[Tuple[Any, ...]]:
    async with aiosqlite.connect(DATABASE) as conn:
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [
            tuple(row) for row in rows
        ]  # Iterable[Row]를 List[Tuple[Any, ...]]로 변환


async def load_groups() -> Dict[str, Dict]:
    try:
        rows = await fetch_query(
            "SELECT chat_id, title, added_by, added_at, notification FROM groups"
        )
        return {
            row[0]: {
                "title": row[1],
                "admin_id": row[2],
                "added_at": row[3],
                "muted": not row[4],
            }
            for row in rows
        }
    except Exception as e:
        logger.error("load_groups_failed", error=str(e))
        return {}


async def save_groups(groups: Dict[str, Dict]) -> None:
    try:
        for chat_id, data in groups.items():
            await execute_query(
                "INSERT OR REPLACE INTO groups (chat_id, title, added_by, added_at, notification) VALUES (?, ?, ?, ?, ?)",
                (
                    chat_id,
                    data.get("title", ""),
                    data.get("admin_id", 0),
                    data.get("added_at", ""),
                    not data.get("muted", False),
                ),
            )
    except Exception as e:
        logger.error("save_groups_failed", error=str(e))


async def load_banned_users() -> Dict[str, Dict]:
    try:
        rows = await fetch_query(
            "SELECT user_id, username, admin_id, admin_username, reason, chat_id FROM banned_users"
        )
        return {
            row[0]: {
                "username": row[1],
                "admin_id": row[2],
                "admin_username": row[3],
                "reason": row[4],
                "chat_id": row[5],
            }
            for row in rows
        }
    except Exception as e:
        logger.error("load_banned_users_failed", error=str(e))
        return {}


async def save_banned_users(users: Dict[str, Dict]) -> None:
    try:
        for user_id, data in users.items():
            await execute_query(
                "INSERT OR REPLACE INTO banned_users (user_id, username, admin_id, admin_username, reason, chat_id, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    data.get("username", ""),
                    data.get("admin_id", 0),
                    data.get("admin_username", ""),
                    data.get("reason", ""),
                    data.get("chat_id", 0),
                    data.get("timestamp", ""),
                ),
            )
    except Exception as e:
        logger.error("save_banned_users_failed", error=str(e))


async def load_admins() -> Dict[str, Dict]:
    try:
        rows = await fetch_query(
            "SELECT admin_id, username, added_by_id, added_by_username FROM admins"
        )
        return {
            row[0]: {
                "username": row[1],
                "added_by": row[2],
                "added_by_username": row[3],
            }
            for row in rows
        }
    except Exception as e:
        logger.error("load_admins_failed", error=str(e))
        return {}


async def save_admins(admins: Dict[str, Dict]) -> None:
    try:
        for admin_id, data in admins.items():
            await execute_query(
                "INSERT OR REPLACE INTO admins (admin_id, username, added_by_id, added_by_username, timestamp) VALUES (?, ?, ?, ?, ?)",
                (
                    admin_id,
                    data.get("username", ""),
                    data.get("added_by", 0),
                    data.get("added_by_username", ""),
                    data.get("timestamp", ""),
                ),
            )
    except Exception as e:
        logger.error("save_admins_failed", error=str(e))


async def cache_username(user_id: int, username: str) -> None:
    try:
        await execute_query(
            "INSERT OR REPLACE INTO username_cache (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        logger.info("cache_username_success", user_id=user_id, username=username)
    except Exception as e:
        logger.error("cache_username_failed", user_id=user_id, error=str(e))


async def get_user_id_from_cache(username: str) -> Optional[int]:
    try:
        rows = await fetch_query(
            "SELECT user_id FROM username_cache WHERE username = ?",
            (username.lstrip("@"),),
        )
        return int(rows[0][0]) if rows else None
    except Exception as e:
        logger.error("get_user_id_from_cache_failed", username=username, error=str(e))
        return None
