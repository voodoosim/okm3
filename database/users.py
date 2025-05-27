import json
import os
from datetime import datetime
from typing import Optional

import aiofiles

from config import ADMINS_FILE, BANNED_USERS_FILE, logger


async def is_banned(user_id: int) -> bool:
    try:
        if os.path.exists(BANNED_USERS_FILE):
            async with aiofiles.open(BANNED_USERS_FILE, "r") as f:
                banned_users = json.loads(await f.read())
            return str(user_id) in banned_users
        return False
    except Exception as e:
        logger.error(f"Error checking banned user: {e}")
        return False


async def unban_user(user_id: int) -> None:
    try:
        if os.path.exists(BANNED_USERS_FILE):
            async with aiofiles.open(BANNED_USERS_FILE, "r") as f:
                banned_users = json.loads(await f.read())
            if str(user_id) in banned_users:
                del banned_users[str(user_id)]
                async with aiofiles.open(BANNED_USERS_FILE, "w") as f:
                    await f.write(json.dumps(banned_users, indent=2))
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")


async def ban_user(
    user_id: int,
    username: Optional[str],
    admin_id: int,
    admin_username: Optional[str],
    reason: str,
    chat_id: int,
) -> None:
    try:
        banned_users = {}
        if os.path.exists(BANNED_USERS_FILE):
            async with aiofiles.open(BANNED_USERS_FILE, "r") as f:
                banned_users = json.loads(await f.read())
        banned_users[str(user_id)] = {
            "username": username or "",
            "admin_id": admin_id,
            "admin_username": admin_username or "",
            "reason": reason,
            "chat_id": chat_id,
            "timestamp": datetime.now().isoformat(),
        }
        async with aiofiles.open(BANNED_USERS_FILE, "w") as f:
            await f.write(json.dumps(banned_users, indent=2))
    except Exception as e:
        logger.error(f"Error banning user: {e}")


async def kick_user(
    user_id: int,
    username: Optional[str],
    admin_id: int,
    admin_username: Optional[str],
    reason: str,
    chat_id: int,
) -> None:
    try:
        kicked_users = {}
        kicked_file = os.path.join(
            os.path.dirname(BANNED_USERS_FILE), "kicked_users.json"
        )
        if os.path.exists(kicked_file):
            async with aiofiles.open(kicked_file, "r") as f:
                kicked_users = json.loads(await f.read())
        kicked_users[str(user_id)] = {
            "username": username or "",
            "admin_id": admin_id,
            "admin_username": admin_username or "",
            "reason": reason,
            "chat_id": chat_id,
            "timestamp": datetime.now().isoformat(),
        }
        async with aiofiles.open(kicked_file, "w") as f:
            await f.write(json.dumps(kicked_users, indent=2))
    except Exception as e:
        logger.error(f"Error kicking user: {e}")


async def is_admin(user_id: int) -> bool:
    try:
        if os.path.exists(ADMINS_FILE):
            async with aiofiles.open(ADMINS_FILE, "r") as f:
                admins = json.loads(await f.read())
            return str(user_id) in admins
        return False
    except Exception as e:
        logger.error(f"Error checking admin: {e}")
        return False


async def add_admin(
    admin_id: int,
    username: Optional[str],
    added_by_id: int,
    added_by_username: Optional[str],
) -> bool:
    try:
        admins = {}
        if os.path.exists(ADMINS_FILE):
            async with aiofiles.open(ADMINS_FILE, "r") as f:
                admins = json.loads(await f.read())
        admins[str(admin_id)] = {
            "username": username or "",
            "added_by_id": added_by_id,
            "added_by_username": added_by_username or "",
            "timestamp": datetime.now().isoformat(),
        }
        async with aiofiles.open(ADMINS_FILE, "w") as f:
            await f.write(json.dumps(admins, indent=2))
        return True
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return False


async def remove_admin(admin_id: int) -> bool:
    try:
        if os.path.exists(ADMINS_FILE):
            async with aiofiles.open(ADMINS_FILE, "r") as f:
                admins = json.loads(await f.read())
            if str(admin_id) in admins:
                del admins[str(admin_id)]
                async with aiofiles.open(ADMINS_FILE, "w") as f:
                    await f.write(json.dumps(admins, indent=2))
                return True
        return False
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        return False


async def get_admins() -> dict:
    try:
        if os.path.exists(ADMINS_FILE):
            async with aiofiles.open(ADMINS_FILE, "r") as f:
                return json.loads(await f.read())
        return {}
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return {}
