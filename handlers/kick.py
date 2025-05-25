import asyncio
from typing import Any, Dict, List, Optional, Tuple

from aiogram import Bot, Router, types
from aiogram.filters import Command

from config import logger
from database.users import kick_user
from handlers.sync_kick import kick_in_group
from utils.common import extract_user_info
from utils.logger import log_kick
from utils.permissions import is_admin, is_group_admin
from database.groups import get_groups

router = Router()


@router.message(Command(commands=["kick", "킷"], prefix="."))
async def kick_user_cmd(message: types.Message, bot: Bot) -> None:
    """사용자 강퇴 명령어 (.킷)."""
    logger.info(
        "kick_cmd_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        text=message.text,
    )

    try:
        if not message.from_user:
            logger.error("kick_cmd_error", error="No user information")
            await message.reply("사용자 정보를 확인할 수 없습니다.")
            return

        is_admin_user = await is_admin(message.from_user.id)
        is_group_admin_user = await is_group_admin(bot, message.chat.id, message.from_user.id)
        logger.info(
            "permission_check",
            user_id=message.from_user.id,
            is_admin=is_admin_user,
            is_group_admin=is_group_admin_user,
        )

        if not (is_admin_user or is_group_admin_user):
            logger.warning("permission_denied", user_id=message.from_user.id, chat_id=message.chat.id)
            await message.reply("권한이 없습니다.")
            return

        if message.chat.type == "private":
            logger.warning("private_chat", user_id=message.from_user.id, chat_id=message.chat.id)
            await message.reply("그룹에서만 사용 가능합니다.")
            return

        user_info = await extract_user_info(message, bot)
        logger.info("user_info_extracted", user_info=user_info)
        chat_id = message.chat.id

        if "user_ids" in user_info and user_info["user_ids"]:
            # 멀티 강퇴 처리
            results = []
            tasks = [
                process_kick(message, bot, target_id, None, user_info["reason"] or "")
                for target_id in user_info["user_ids"]
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 통합 알림 메시지 생성
            success_users = []
            failed_users = []
            for target_id, result in zip(user_info["user_ids"], results):
                if isinstance(result, Exception):
                    failed_users.append(f"{target_id} (실패: {str(result)})")
                else:
                    success_users.append(result)  # (username, target_id)

            # 그룹 내 통합 메시지
            message_text = ["👟 사용자 강퇴"]
            if success_users:
                user_text = "\n".join(
                    f"{username} ({target_id})" for username, target_id in success_users
                )
                message_text.append(user_text)
            if failed_users:
                message_text.append(f"강퇴 실패: {', '.join(failed_users)}")

            reason_text = f"[{user_info['reason']}]" if user_info["reason"] else ""
            group_text = f"[{message.chat.title or 'Unknown'}]"
            full_message = "\n".join(message_text) + f"\n{reason_text}\n{group_text}"

            try:
                await message.reply(full_message, parse_mode="HTML")
                logger.info("reply_sent", chat_id=chat_id, message=full_message)
            except Exception as e:
                logger.error("reply_failed", chat_id=chat_id, error=str(e))

            # 통합 로그 전송
            if success_users:
                logger.info(
                    "calling_log_kick_multi",
                    chat_id=chat_id,
                    user_count=len(success_users),
                )
                for username, target_id in success_users:
                    await log_kick(
                        bot,
                        target_id,
                        username,
                        message.from_user.id,
                        message.from_user.username or "Unknown",
                        message.chat.title or "Unknown",
                        chat_id,
                        user_info["reason"] or "",
                    )

            # 연동된 그룹에 통합 알림 전송
            groups = await get_groups()
            tasks = [
                kick_in_group(
                    bot,
                    int(group_id),
                    success_users,
                    user_info["reason"] or "",
                    message.chat.title or "Unknown",
                )
                for group_id in groups.keys()
                if group_id != str(chat_id) and success_users
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for group_id, result in zip(groups.keys(), results):
                if isinstance(result, Exception):
                    logger.error(
                        "group_kick_failed", group_id=group_id, error=str(result)
                    )
            return

        target_id = user_info["user_id"]
        target_username = user_info["username"]
        reason = user_info["reason"]

        if not target_id:
            await message.reply("사용자를 지정하세요 (답장, 사용자 ID, 또는 @username 입력).")
            return

        result = await process_kick(message, bot, target_id, target_username, reason or "")
        if result:
            # 단일 강퇴 알림
            reason_text = f"[{reason}]" if reason else ""
            group_text = f"[{message.chat.title or 'Unknown'}]"
            kick_message = (
                f"👟 사용자 강퇴\n"
                f"{result[0]} ({target_id})\n"
                f"{reason_text}\n"
                f"{group_text}"
            )
            try:
                await message.reply(kick_message, parse_mode="HTML")
                logger.info("reply_sent", chat_id=chat_id, message=kick_message)
            except Exception as e:
                logger.error("reply_failed", chat_id=chat_id, error=str(e))

            # 단일 로그 전송
            logger.info("calling_log_kick_single", chat_id=chat_id, target_id=target_id)
            await log_kick(
                bot,
                target_id,
                result[0],
                message.from_user.id,
                message.from_user.username or "Unknown",
                message.chat.title or "Unknown",
                chat_id,
                reason or "",
            )

            # 연동된 그룹에 단일 알림 전송
            groups = await get_groups()
            tasks = [
                kick_in_group(
                    bot,
                    int(group_id),
                    [(result[0], target_id)],
                    reason or "",
                    message.chat.title or "Unknown",
                )
                for group_id in groups.keys()
                if group_id != str(chat_id)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for group_id, result in zip(groups.keys(), results):
                if isinstance(result, Exception):
                    logger.error(
                        "group_kick_failed", group_id=group_id, error=str(result)
                    )
    except ValueError as e:
        logger.error("kick_cmd_value_error", chat_id=message.chat.id, error=str(e))
        await message.reply(f"입력 오류: {str(e)}")
    except Exception as e:
        logger.error("kick_cmd_error", chat_id=message.chat.id, error=str(e))
        await message.reply("내부 오류가 발생했습니다.")


async def process_kick(
    message: types.Message,
    bot: Bot,
    target_id: int,
    target_username: Optional[str],
    reason: str,
) -> Optional[Tuple[str, int]]:
    """사용자 강퇴 처리."""
    chat_id = message.chat.id
    chat_title = message.chat.title or "Unknown"
    logger.info("process_kick_attempt", chat_id=chat_id, target_id=target_id)

    if not message.from_user:
        logger.error("process_kick_error", chat_id=chat_id, error="No user information")
        return None

    if target_id == message.from_user.id or target_id == bot.id:
        logger.error("process_kick_error", chat_id=chat_id, error="Cannot kick self or bot")
        return None

    try:
        chat_member = await bot.get_chat_member(chat_id, target_id)
        if isinstance(chat_member, (types.ChatMemberOwner, types.ChatMemberAdministrator)):
            logger.error("process_kick_error", chat_id=chat_id, error="Cannot kick admin")
            return None

        user = chat_member.user
        target_username = user.username or f"<b>{user.first_name} {user.last_name}</b>".strip() or "<b>Nickname</b>"
        await bot.ban_chat_member(chat_id, target_id)
        await bot.unban_chat_member(chat_id, target_id)
        logger.info("kick_chat_member_success", chat_id=chat_id, target_id=target_id)

        await kick_user(
            target_id,
            target_username,
            message.from_user.id,
            message.from_user.username or "Unknown",
            reason,
            chat_id,
        )

        return (target_username, target_id)  # 성공 시 사용자명과 ID 반환
    except Exception as e:
        logger.error("process_kick_error", chat_id=chat_id, target_id=target_id, error=str(e))
        raise
