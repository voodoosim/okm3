from typing import Optional

from config import logger
from utils.storage import cache_username, get_user_id_from_cache


async def cache_username(user_id: int, username: str) -> None:
    """사용자명 캐싱."""
    await cache_username(user_id, username)


async def get_user_id_from_cache(username: str) -> Optional[int]:
    """캐시에서 사용자 ID 조회."""
    return await get_user_id_from_cache(username)
