from datetime import datetime  # datetime 임포트 추가
from typing import Dict

from config import logger
from utils.storage import load_groups, save_groups


async def get_groups() -> Dict[str, Dict]:
    """그룹 데이터를 로드."""
    return await load_groups()


async def save_groups(groups: Dict[str, Dict]) -> None:
    """그룹 데이터를 저장."""
    await save_groups(groups)


async def get_notification_status(chat_id: int) -> bool:
    """그룹의 알림 상태 확인 (음소거 여부)."""
    groups = await get_groups()
    return not groups.get(str(chat_id), {}).get("muted", False)


async def set_mute_status(chat_id: int, muted: bool) -> None:
    """그룹의 음소거 상태 설정."""
    groups = await get_groups()
    if str(chat_id) not in groups:
        groups[str(chat_id)] = {"muted": False}
    groups[str(chat_id)]["muted"] = muted
    await save_groups(groups)
    logger.info("set_mute_status", chat_id=chat_id, muted=muted)


async def set_all_mute_status(muted: bool) -> None:
    """모든 그룹의 음소거 상태 설정."""
    groups = await get_groups()
    for chat_id in groups:
        groups[chat_id]["muted"] = muted
    await save_groups(groups)
    logger.info("set_all_mute_status", muted=muted, group_count=len(groups))


async def add_group(chat_id: int, title: str, admin_id: int) -> bool:
    """그룹 추가."""
    try:
        groups = await get_groups()
        groups[str(chat_id)] = {
            "title": title,
            "admin_id": admin_id,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "muted": groups.get(str(chat_id), {}).get("muted", False),
        }
        await save_groups(groups)
        logger.info("add_group_success", chat_id=chat_id, title=title)
        return True
    except Exception as e:
        logger.error("add_group_failed", chat_id=chat_id, error=str(e))
        return False


async def remove_group(chat_id: int) -> bool:
    """그룹 제거."""
    try:
        groups = await get_groups()
        if str(chat_id) in groups:
            del groups[str(chat_id)]
            await save_groups(groups)
            logger.info("remove_group_success", chat_id=chat_id)
            return True
        logger.warning("remove_group_not_found", chat_id=chat_id)
        return False
    except Exception as e:
        logger.error("remove_group_failed", chat_id=chat_id, error=str(e))
        return False
