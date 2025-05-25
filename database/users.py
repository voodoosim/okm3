import json
import os
from typing import Dict

from config import ADMINS_FILE, BANNED_USERS_FILE, logger


async def get_banned_users() -> Dict[str, Dict]:
    """차단된 사용자 데이터를 로드."""
    try:
        if os.path.exists(BANNED_USERS_FILE):
            with open(BANNED_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error("get_banned_users_failed", error=str(e))
        return {}


async def save_banned_users(users: Dict[str, Dict]) -> None:
    """차단된 사용자 데이터를 저장."""
    try:
        with open(BANNED_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("save_banned_users_failed", error=str(e))


async def get_admins() -> Dict[str, Dict]:
    """관리자 데이터를 로d."""
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error("get_admins_failed", error=str(e))
        return {}


async def save_admins(admins: Dict[str, Dict]) -> None:
    """관리자 데이터를 저장."""
    try:
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(admins, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("save_admins_failed", error=str(e))


async def ban_user(
    user_id: int,
    username: str,
    admin_id: int,
    admin_username: str,
    reason: str,
    chat_id: int,
) -> None:
    """사용자 차단 기록."""
    try:
        users = await get_banned_users()
        users[str(user_id)] = {
            "username": username,
            "admin_id": admin_id,
            "admin_username": admin_username,
            "reason": reason,
            "chat_id": chat_id,
        }
        await save_banned_users(users)
        logger.info("ban_user_success", user_id=user_id, chat_id=chat_id)
    except Exception as e:
        logger.error("ban_user_failed", user_id=user_id, chat_id=chat_id, error=str(e))
        raise


async def kick_user(
    user_id: int,
    username: str,
    admin_id: int,
    admin_username: str,
    reason: str,
    chat_id: int,
) -> None:
    """사용자 강퇴 기록."""
    try:
        logger.info(
            "kick_user_success",
            user_id=user_id,
            username=username,
            admin_id=admin_id,
            admin_username=admin_username,
            reason=reason,
            chat_id=chat_id,
        )
    except Exception as e:
        logger.error("kick_user_failed", user_id=user_id, chat_id=chat_id, error=str(e))
        raise


async def add_admin(
    user_id: int,
    username: str,
    admin_id: int,
    admin_username: str,
) -> None:
    """관리자 추가."""
    try:
        admins = await get_admins()
        admins[str(user_id)] = {
            "username": username,
            "added_by": admin_id,
            "added_by_username": admin_username,
        }
        await save_admins(admins)
        logger.info("add_admin_success", user_id=user_id)
    except Exception as e:
        logger.error("add_admin_failed", user_id=user_id, error=str(e))
        raise


async def remove_admin(user_id: int) -> bool:
    """관리자 제거."""
    try:
        admins = await get_admins()
        if str(user_id) in admins:
            del admins[str(user_id)]
            await save_admins(admins)
            logger.info("remove_admin_success", user_id=user_id)
            return True
        logger.warning("remove_admin_not_found", user_id=user_id)
        return False
    except Exception as e:
        logger.error("remove_admin_failed", user_id=user_id, error=str(e))
        raise


async def is_banned(user_id: int) -> bool:
    """사용자가 차단되었는지 확인."""
    try:
        users = await get_banned_users()
        return str(user_id) in users
    except Exception as e:
        logger.error("is_banned_failed", user_id=user_id, error=str(e))
        return False


async def unban_user(user_id: int) -> bool:
    """사용자 차단 해제."""
    try:
        users = await get_banned_users()
        if str(user_id) in users:
            del users[str(user_id)]
            await save_banned_users(users)
            logger.info("unban_user_success", user_id=user_id)
            return True
        logger.warning("unban_user_not_found", user_id=user_id)
        return False
    except Exception as e:
        logger.error("unban_user_failed", user_id=user_id, error=str(e))
        raise
