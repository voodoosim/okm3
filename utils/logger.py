from typing import List, Tuple, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config import LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID, logger
from database.groups import get_notification_status


async def log_ban(
    bot: Bot,
    users: List[Tuple[str, int]],
    admin_id: int,
    admin_username: str,
    chat_title: str,
    chat_id: int,
    reason: str = "",
):
    logger.info("log_ban_called", chat_id=chat_id, user_count=len(users))
    if not users:
        logger.warning("log_ban_empty_users", chat_id=chat_id)
        return

    user_text = "\n".join(
        f"@{username} ({user_id})" if username != "Unknown" else f"<b>Unknown</b> ({user_id})"
        for username, user_id in users
    )
    log_message = (
        f"🐦‍⬛️ 사용자 차단 🚷\n"
        f"{user_text}\n"
        f"[{reason or '없음'}]\n"
        f"[{chat_title}]"
    )
    logger.info(
        "ban_log",
        user_ids=[user_id for _, user_id in users],
        admin_id=admin_id,
        chat_id=chat_id,
        reason=reason,
        channel_ids=[LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID],
    )
    # 음소거 상태 확인
    if not await get_notification_status(chat_id):
        logger.info("log_ban_skipped_muted", chat_id=chat_id)
        return

    for channel_id in [LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID]:
        if not channel_id:
            logger.warning(
                "log_ban_invalid_channel", channel_id=channel_id, chat_id=chat_id
            )
            continue
        try:
            await bot.send_message(channel_id, log_message, parse_mode="HTML")
            logger.info(
                "log_sent", channel_id=channel_id, chat_id=chat_id, message=log_message
            )
        except TelegramAPIError as e:
            logger.error(
                "log_ban_failed",
                channel_id=channel_id,
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
                bot_id=bot.id,
            )
        except Exception as e:
            logger.error(
                "log_ban_failed_unexpected",
                channel_id=chat_id,
                error=str(e),
            )


async def log_kick(
    bot: Bot,
    user_id: int,
    username: str,
    admin_id: int,
    admin_username: str,
    chat_title: str,
    chat_id: int,
    reason: str,
):
    """강퇴 로그 기록."""
    display_name = f"@{username}" if username != "Unknown" else f"<b>Unknown</b>"
    log_message = (
        f"👟 강퇴:\n"
        f"{display_name} ({user_id})\n"
        f"[{reason or '없음'}]\n"
        f"[{chat_title}]"
    )
    logger.info(
        "kick_log", user_id=user_id, admin_id=admin_id, chat_id=chat_id, reason=reason
    )
    if LOG_CHANNEL_ID:
        # 음소거 상태 확인
        if not await get_notification_status(chat_id):
            logger.info("log_kick_skipped_muted", chat_id=chat_id)
            return
        try:
            await bot.send_message(LOG_CHANNEL_ID, log_message, parse_mode="HTML")
            logger.info(
                "log_sent",
                channel_id=LOG_CHANNEL_ID,
                chat_id=chat_id,
                message=log_message,
            )
        except TelegramAPIError as e:
            logger.error(
                "log_kick_failed",
                channel_id=LOG_CHANNEL_ID,
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_kick_failed_unexpected",
                channel_id=LOG_CHANNEL_ID,
                chat_id=chat_id,
                error=str(e),
            )


async def log_unban(
    bot: Bot,
    user_id: int,
    username: str,
    admin_id: int,
    admin_username: str,
    chat_title: str,
    chat_id: int,
):
    """차단 해제 로그 기록."""
    display_name = f"@{username}" if username != "Unknown" else f"<b>Unknown</b>"
    log_message = (
        f"✅ 차단 해제:\n"
        f"{display_name} ({user_id})\n"
        f"[{chat_title}]"
    )
    logger.info("unban_log", user_id=user_id, admin_id=admin_id, chat_id=chat_id)
    # 음소거 상태 확인
    if not await get_notification_status(chat_id):
        logger.info("log_unban_skipped_muted", chat_id=chat_id)
        return
    for channel_id in [LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID]:
        if not channel_id:
            logger.warning(
                "log_unban_invalid_channel", channel_id=channel_id, chat_id=chat_id
            )
            continue
        try:
            await bot.send_message(channel_id, log_message, parse_mode="HTML")
            logger.info(
                "log_sent", channel_id=channel_id, chat_id=chat_id, message=log_message
            )
        except TelegramAPIError as e:
            logger.error(
                "log_unban_failed",
                channel_id=channel_id,
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_unban_failed_unexpected",
                channel_id=chat_id,
                error=str(e),
            )


async def log_group_add(
    bot: Bot, chat_title: str, chat_id: int, admin_id: int, admin_username: str
):
    """그룹 추가 로그 기록."""
    log_message = (
        f"➕ 그룹 추가:\n"
        f"[{chat_title} ({chat_id})]\n"
        f"관리자: @{admin_username} ({admin_id})"
    )
    logger.info("group_add_log", chat_id=chat_id, admin_id=admin_id)
    # 음소거 상태 확인
    if not await get_notification_status(chat_id):
        logger.info("log_group_add_skipped_muted", chat_id=chat_id)
        return
    for channel_id in [LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID]:
        if not channel_id:
            logger.warning(
                "log_group_add_invalid_channel", channel_id=channel_id, chat_id=chat_id
            )
            continue
        try:
            await bot.send_message(channel_id, log_message)
            logger.info(
                "log_sent", channel_id=channel_id, chat_id=chat_id, message=log_message
            )
        except TelegramAPIError as e:
            logger.error(
                "log_group_add_failed",
                channel_id=channel_id,
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_group_add_failed_unexpected",
                channel_id=chat_id,
                error=str(e),
            )


async def log_group_remove(
    bot: Bot, chat_title: str, chat_id: int, admin_id: int, admin_username: str
):
    """그룹 삭제 로그 기록."""
    log_message = (
        f"➖ 그룹 삭제:\n"
        f"[{chat_title} ({chat_id})]\n"
        f"관리자: @{admin_username} ({admin_id})"
    )
    logger.info("group_remove_log", chat_id=chat_id, admin_id=admin_id)
    # 음소거 상태 확인
    if not await get_notification_status(chat_id):
        logger.info("log_group_remove_skipped_muted", chat_id=chat_id)
        return
    for channel_id in [LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID]:
        if not channel_id:
            logger.warning(
                "log_group_remove_invalid_channel",
                channel_id=channel_id,
                chat_id=chat_id,
            )
            continue
        try:
            await bot.send_message(channel_id, log_message)
            logger.info(
                "log_sent", channel_id=channel_id, chat_id=chat_id, message=log_message
            )
        except TelegramAPIError as e:
            logger.error(
                "log_group_remove_failed",
                channel_id=channel_id,
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_group_remove_failed_unexpected",
                channel_id=chat_id,
                error=str(e),
            )


async def log_admin_add(
    bot: Bot, target_id: int, target_username: str, admin_id: int, admin_username: str
):
    """관리자 추가 로그 기록."""
    log_message = (
        f"👑 관리자 추가:\n"
        f"@{target_username} ({target_id})\n"
        f"관리자: @{admin_username} ({admin_id})"
    )
    logger.info("admin_add_log", target_id=target_id, admin_id=admin_id)
    if LOG_CHANNEL_ID:
        try:
            await bot.send_message(LOG_CHANNEL_ID, log_message)
            logger.info("log_sent", channel_id=LOG_CHANNEL_ID, message=log_message)
        except TelegramAPIError as e:
            logger.error(
                "log_admin_add_failed",
                channel_id=LOG_CHANNEL_ID,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_admin_add_failed_unexpected",
                channel_id=LOG_CHANNEL_ID,
                error=str(e),
            )


async def log_admin_remove(
    bot: Bot, target_id: int, target_username: str, admin_id: int, admin_username: str
):
    """관리자 제거 로그 기록."""
    log_message = (
        f"👑 관리자 제거:\n"
        f"@{target_username} ({target_id})\n"
        f"관리자: @{admin_username} ({admin_id})"
    )
    logger.info("admin_remove_log", target_id=target_id, admin_id=admin_id)
    if LOG_CHANNEL_ID:
        try:
            await bot.send_message(LOG_CHANNEL_ID, log_message)
            logger.info("log_sent", channel_id=LOG_CHANNEL_ID, message=log_message)
        except TelegramAPIError as e:
            logger.error(
                "log_admin_remove_failed",
                channel_id=LOG_CHANNEL_ID,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_admin_remove_failed_unexpected",
                channel_id=LOG_CHANNEL_ID,
                error=str(e),
            )


async def log_command(
    bot: Bot,
    command: str,
    user_id: int,
    username: str,
    chat_title: str,
    chat_id: int
):
    """명령어 사용 로그 기록."""
    display_name = f"@{username}" if username != "Unknown" else f"<b>Unknown</b>"
    log_message = (
        f"📜 명령어 사용:\n"
        f"명령어: {command}\n"
        f"사용자: {display_name} ({user_id})\n"
        f"[{chat_title} ({chat_id})]"
    )
    logger.info(
        "command_log",
        command=command,
        user_id=user_id,
        username=username,
        chat_id=chat_id,
        chat_title=chat_title
    )
    if LOG_CHANNEL_ID:
        try:
            await bot.send_message(LOG_CHANNEL_ID, log_message, parse_mode="HTML")
            logger.info(
                "log_sent",
                channel_id=LOG_CHANNEL_ID,
                chat_id=chat_id,
                message=log_message
            )
        except TelegramAPIError as e:
            logger.error(
                "log_command_failed",
                channel_id=LOG_CHANNEL_ID,
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_command_failed_unexpected",
                channel_id=chat_id,
                error=str(e),
            )


async def log_bot_added(
    bot: Bot,
    chat_title: str,
    chat_id: int,
    inviter_id: int,
    inviter_username: str,
    is_admin: bool,
    chat_link: Optional[str] = None
):
    """봇이 그룹에 추가된 경우 로그 기록."""
    inviter_display = f"@{inviter_username}" if inviter_username != "Unknown" else f"<b>Unknown</b>"
    admin_status = "예" if is_admin else "아니오"
    chat_link_text = f"\n링크: {chat_link}" if chat_link else ""
    log_message = (
        f"🤖 봇 추가:\n"
        f"그룹: [{chat_title} ({chat_id})]\n"
        f"초대자: {inviter_display} ({inviter_id})\n"
        f"관리자 권한: {admin_status}"
        f"{chat_link_text}"
    )
    logger.info(
        "bot_added_log",
        chat_id=chat_id,
        chat_title=chat_title,
        inviter_id=inviter_id,
        inviter_username=inviter_username,
        is_admin=is_admin,
        chat_link=chat_link
    )
    if LOG_CHANNEL_ID:
        try:
            await bot.send_message(LOG_CHANNEL_ID, log_message, parse_mode="HTML")
            logger.info(
                "log_sent",
                channel_id=LOG_CHANNEL_ID,
                chat_id=chat_id,
                message=log_message
            )
        except TelegramAPIError as e:
            logger.error(
                "log_bot_added_failed",
                channel_id=LOG_CHANNEL_ID,
                chat_id=chat_id,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "log_bot_added_failed_unexpected",
                channel_id=chat_id,
                error=str(e),
            )


async def test_channel_access(bot, channel_id):
    """채널 접근 테스트."""
    try:
        chat = await bot.get_chat(channel_id)
        logger.info("channel_access_success", channel_id=channel_id, chat_title=chat.title)
    except TelegramAPIError as e:
        logger.error(
            "channel_access_failed",
            channel_id=channel_id,
            error=str(e),
            error_type=type(e).__name__,
        )
