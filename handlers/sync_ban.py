from typing import List, Tuple

from aiogram import Bot
from config import logger
from database.groups import get_notification_status


async def ban_in_group(
    bot: Bot,
    group_id: int,
    users: List[Tuple[str, int]],  # (username, user_id) 리스트
    reason: str,
    origin_chat_title: str,
) -> None:
    """특정 그룹에서 사용자 차단 및 통합 알림 전송."""
    logger.info(
        "ban_in_group_attempt",
        group_id=group_id,
        user_ids=[user_id for _, user_id in users],
    )
    if not users:
        logger.warning("ban_in_group_empty_users", group_id=group_id)
        return

    try:
        notify = await get_notification_status(group_id)
        # 모든 사용자 차단
        for _, target_id in users:
            await bot.ban_chat_member(group_id, target_id)
            logger.info(
                "ban_chat_member_success", group_id=group_id, target_id=target_id
            )

        if notify:
            user_text = "\n".join(
                f"@{username} ({user_id})" if username else f"<b>Nickname</b> ({user_id})"
                for username, user_id in users
            )
            reason_text = f"[{reason}]" if reason else ""
            ban_notification = (
                f"🐦‍⬛️ 사용자 차단 🚷\n"
                f"{user_text}\n"
                f"[{origin_chat_title}]"
                f"{reason_text}"
            )
            await bot.send_message(group_id, ban_notification, parse_mode="HTML")
            logger.info(
                "ban_notification_sent", group_id=group_id, message=ban_notification
            )
    except Exception as e:
        logger.error(
            "group_ban_failed",
            group_id=group_id,
            user_ids=[user_id for _, user_id in users],
            error=str(e),
        )
        raise
