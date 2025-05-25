import asyncio
from typing import Optional

from aiogram import Bot, Router, types
from aiogram.filters import Command

from config import logger
from database.groups import get_groups, get_notification_status
from database.users import is_banned, unban_user
from utils.common import extract_user_info
from utils.logger import log_unban
from utils.permissions import is_admin, is_group_admin

router = Router()


@router.message(Command(commands=["unban", "언벤"], prefix="."))
async def unban_user_cmd(message: types.Message, bot: Bot) -> None:
    """사용자 차단 해제 명령어 (.언벤)."""
    logger.info(
        "unban_cmd_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        text=message.text,
    )

    try:
        if not message.from_user:
            logger.error("unban_cmd_error", error="No user information")
            try:
                await message.reply("사용자 정보를 확인할 수 없습니다.")
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
            return

        is_admin_user = await is_admin(message.from_user.id)
        is_group_admin_user = await is_group_admin(
            bot, message.chat.id, message.from_user.id
        )
        logger.info(
            "permission_check",
            user_id=message.from_user.id,
            is_admin=is_admin_user,
            is_group_admin=is_group_admin_user,
        )

        if not (is_admin_user or is_group_admin_user):
            logger.warning(
                "permission_denied",
                user_id=message.from_user.id,
                chat_id=message.chat.id,
            )
            try:
                await message.reply("권한이 없습니다.")
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
            return

        chat_id = message.chat.id
        chat_title = message.chat.title or "Unknown"
        if message.chat.type == "private":
            logger.warning(
                "private_chat", user_id=message.from_user.id, chat_id=message.chat.id
            )
            try:
                await message.reply("그룹에서만 사용 가능합니다.")
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
            return

        user_info = await extract_user_info(message, bot)
        logger.info("user_info_extracted", user_info=user_info)

        if "user_ids" in user_info and user_info["user_ids"]:
            tasks = [
                process_unban(message, bot, target_id, None, user_info["reason"] or "")
                for target_id in user_info["user_ids"]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            return

        target_id = user_info["user_id"]
        target_username = user_info["username"]
        reason = user_info["reason"]

        if not target_id:
            try:
                await message.reply("사용자를 지정하세요 (답장, 사용자 ID 입력).")
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
            return

        await process_unban(message, bot, target_id, target_username, reason or "")
    except ValueError as e:
        logger.error("unban_cmd_value_error", chat_id=message.chat.id, error=str(e))
        try:
            await message.reply(f"입력 오류: {str(e)}")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
    except Exception as e:
        logger.error("unban_cmd_error", chat_id=message.chat.id, error=str(e))
        try:
            await message.reply("내부 오류가 발생했습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))


async def process_unban(
    message: types.Message,
    bot: Bot,
    target_id: int,
    target_username: Optional[str],
    reason: str,
) -> None:
    """사용자 차단 해제 처리 및 모든 그룹에 동기화."""
    chat_id = message.chat.id
    chat_title = message.chat.title or "Unknown"
    logger.info("process_unban_attempt", chat_id=chat_id, target_id=target_id)

    if not message.from_user:
        try:
            await message.reply("사용자 정보를 확인할 수 없습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    try:
        chat_member = await bot.get_chat_member(chat_id, target_id)
        user = chat_member.user
        target_username = user.username or "Unknown"
        if not await is_banned(target_id):
            try:
                await message.reply(
                    f"@{target_username} ({target_id})는 차단되지 않았습니다."
                )
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
            return

        await bot.unban_chat_member(chat_id, target_id)
        logger.info("unban_chat_member_success", chat_id=chat_id, target_id=target_id)

        reason_text = f"💬: {reason}" if reason else ""
        unban_message = (
            f"✅ @{target_username} ({target_id}) 차단 해제\n" f"{reason_text}"
        )
        try:
            await message.reply(unban_message)
            logger.info("reply_sent", chat_id=message.chat.id, message=unban_message)
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))

        await unban_user(target_id)

        groups = await get_groups()
        tasks = [
            unban_in_group(
                bot, int(group_id), target_id, target_username, reason, chat_title
            )
            for group_id in groups.keys()
            if group_id != str(chat_id)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for group_id, result in zip(groups.keys(), results):
            if isinstance(result, Exception):
                logger.error("group_unban_failed", group_id=group_id, error=str(result))

        await log_unban(
            bot,
            target_id,
            target_username,
            message.from_user.id,
            message.from_user.username or "Unknown",
            chat_title,
            chat_id,
        )
    except Exception as e:
        logger.error(
            "process_unban_error", chat_id=chat_id, target_id=target_id, error=str(e)
        )
        try:
            await message.reply("❌ 차단 해제 중 오류가 발생했습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))


async def unban_in_group(
    bot: Bot,
    group_id: int,
    target_id: int,
    target_username: Optional[str],
    reason: str,
    origin_chat_title: str,
) -> None:
    """특정 그룹에서 사용자 차단 해제 및 알림 전송."""
    logger.info("unban_in_group_attempt", group_id=group_id, target_id=target_id)
    try:
        notify = await get_notification_status(group_id)
        await bot.unban_chat_member(group_id, target_id)
        logger.info("unban_chat_member_success", group_id=group_id, target_id=target_id)
        if notify:
            reason_text = f"💬: {reason}" if reason else ""
            unban_notification = (
                f"✅ @{target_username or '알 수 없음'} ({target_id}) 차단 해제\n"
                f"{reason_text}\n"
                f" ~ {origin_chat_title}에서 연동"
            )
            await bot.send_message(group_id, unban_notification)
            logger.info("unban_notification_sent", group_id=group_id)
    except Exception as e:
        logger.error(
            "group_unban_failed", group_id=group_id, user_id=target_id, error=str(e)
        )
        raise
