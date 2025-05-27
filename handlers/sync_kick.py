from typing import List, Optional, Set, Tuple

from aiogram import Bot

from config import logger
from database.groups import get_notification_status


async def kick_in_group(
    bot: Bot,
    group_id: int,
    users: List[Tuple[Optional[str], int]],
    reason: str,
    origin_chat_title: Optional[str],
    processed_groups: Set[str] = set(),
):
    if str(group_id) in processed_groups or not users:
        return

    processed_groups.add(str(group_id))

    try:
        for _, target_id in users:
            await bot.ban_chat_member(group_id, target_id)
            await bot.unban_chat_member(group_id, target_id)

        if get_notification_status(group_id):
            user_text = "\n".join(f"{u or 'Unknown'} ({i})" for u, i in users)
            await bot.send_message(
                group_id,
                f"👟 Kick\n{user_text}\n[{origin_chat_title or 'Unknown'}][{reason}]",
                parse_mode="HTML",
            )

    except Exception as e:
        logger.error(f"group_kick_failed: group_id={group_id}, error={e}")
        raise
