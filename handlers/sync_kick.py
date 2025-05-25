from typing import List, Tuple

from aiogram import Bot

from config import logger
from database.groups import get_notification_status


async def kick_in_group(
    bot: Bot,
    group_id: int,
    users: List[Tuple[str, int]],  # (username, user_id) 리스트
    reason: str,
    origin_chat_title: str,
) -> None:
    """특정 그룹에서 사용자 강퇴 및 통합 알림 전송."""
    logger.info(
        "kick_in_group_attempt",
        group_id=group_id,
        user_ids=[user_id for _, user_id in users],
    )
    if not users:
        logger.warning("kick_in_group_empty_users", group_id=group_id)
        return

    try:
        notify = await get_notification_status(group_id)
        # 모든 사용자 강퇴
        for _, target_id in users:
            await bot.ban_chat_member(group_id, target_id)
            await bot.unban_chat_member(group_id, target_id)
            logger.info(
                "kick_chat_member_success", group_id=group_id, target_id=target_id
            )

        if notify:
            user_text = "\n".join(
                (
                    f"@{username} ({user_id})"
                    if username
                    else f"<b>Nickname</b> ({user_id})"
                )
                for username, user_id in users
            )
            reason_text = f"[{reason}]" if reason else ""
            kick_notification = (
                f"👟 사용자 강퇴\n"
                f"{user_text}\n"
                f"[{origin_chat_title}]"
                f"{reason_text}"
            )
            await bot.send_message(group_id, kick_notification, parse_mode="HTML")
            logger.info(
                "kick_notification_sent", group_id=group_id, message=kick_notification
            )
    except Exception as e:
        logger.error(
            "group_kick_failed",
            group_id=group_id,
            user_ids=[user_id for _, user_id in users],
            error=str(e),
        )
        raise
