import json
import os
from typing import Optional

from config import logger

USERNAME_CACHE_FILE = "data/username_cache.json"


async def cache_username(user_id: int, username: str) -> None:
    """사용자명 캐싱."""
    try:
        cache = {}
        if os.path.exists(USERNAME_CACHE_FILE):
            with open(USERNAME_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)

        cache[str(user_id)] = username
        with open(USERNAME_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        logger.info("cache_username_success", user_id=user_id, username=username)
    except Exception as e:
        logger.error("cache_username_failed", user_id=user_id, error=str(e))


async def get_user_id_from_cache(username: str) -> Optional[int]:
    """캐시에서 사용자 ID 조회."""
    try:
        if os.path.exists(USERNAME_CACHE_FILE):
            with open(USERNAME_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            for user_id, cached_username in cache.items():
                if cached_username == username.lstrip("@"):
                    return int(user_id)
        return None
    except Exception as e:
        logger.error("get_user_id_from_cache_failed", username=username, error=str(e))
        return None
