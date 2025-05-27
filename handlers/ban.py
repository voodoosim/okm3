import asyncio
import logging
from typing import List, Optional, Set, Tuple

from aiogram import Bot, Router, types
from aiogram.filters import Command

from database.groups import get_groups, get_notification_status
from database.users import ban_user, is_banned, unban_user
from handlers.sync_ban import ban_in_group
from utils.common import extract_user_info
from utils.logger import log_ban, log_unban
from utils.permissions import is_admin, is_group_admin

# 로깅 설정
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(Command(commands=["ban", "벤"], prefix="."))
async def ban_user_cmd(message: types.Message, bot: Bot):
    if not message.from_user:
        await message.reply("Invalid user")
        return

    try:
        if not (
            await is_admin(message.from_user.id)
            or await is_group_admin(bot, message.chat.id, message.from_user.id)
        ):
            await message.reply("No permission")
            return

        if message.chat.type == "private":
            await message.reply("Groups only")
            return

        user_info = await extract_user_info(message, bot)
        chat_id = message.chat.id
        chat_title = message.chat.title or "Unknown"
        reason = user_info["reason"] or ""
        target_ids = (
            user_info.get("user_ids", [user_info["user_id"]])
            if user_info.get("user_id")
            else []
        )

        if not target_ids:
            await message.reply("Specify user ID(s)")
            return

        results = await asyncio.gather(
            *[
                process_ban(message, bot, target_id, reason, set())
                for target_id in target_ids
            ],
            return_exceptions=True,
        )

        success = []
        failed = []
        for target_id, result in zip(target_ids, results):
            if isinstance(result, Exception) or not result:
                failed.append(f"{target_id}")
            else:
                success.append(result)

        message_text = ["🚷 Ban"]
        if success:
            message_text.append(
                "\n".join(f"{u or 'Unknown'} ({i})" for u, i in success)
            )
        if failed:
            message_text.append(f"Failed: {', '.join(failed)}")

        await message.reply(
            "\n".join(message_text) + f"\n[{reason}][{chat_title}]", parse_mode="HTML"
        )

        if success:
            await log_ban(
                bot,
                success,
                message.from_user.id,
                message.from_user.username or "Unknown",
                chat_title,
                chat_id,
                reason,
            )

            # FIX: Added await since get_groups() appears to be async
            groups = await get_groups()  # 비동기 호출로 변경 (줄 95)
            await asyncio.gather(
                *[
                    ban_in_group(
                        bot, int(g), success, reason, chat_title, {str(chat_id)}
                    )
                    for g in groups.keys()
                    if g != str(chat_id)
                ],
                return_exceptions=True,
            )

    except Exception as e:
        logger.error(f"ban_error: chat_id={message.chat.id}, error={e}")
        await message.reply("Error occurred")


async def process_ban(
    message: types.Message,
    bot: Bot,
    target_id: int,
    reason: str,
    processed_groups: Set[str],
) -> Optional[Tuple[Optional[str], int]]:
    chat_id = message.chat.id
    if (
        str(chat_id) in processed_groups
        or not message.from_user
        or target_id in (message.from_user.id, bot.id)
    ):
        return None

    processed_groups.add(str(chat_id))

    try:
        chat_member = await bot.get_chat_member(chat_id, target_id)
        if isinstance(
            chat_member, (types.ChatMemberOwner, types.ChatMemberAdministrator)
        ):
            return None

        user = chat_member.user
        username = (
            user.username or f"{user.first_name} {user.last_name}".strip() or "Nickname"
        )
        await bot.ban_chat_member(chat_id, target_id)

        await ban_user(
            target_id,
            username,
            message.from_user.id,
            message.from_user.username or "Unknown",
            reason,
            chat_id,
        )
        return (username, target_id)
    except Exception as e:
        logger.error(
            f"process_ban_error: chat_id={chat_id}, target_id={target_id}, error={e}"
        )
        return None


@router.message(Command(commands=["unban", "언벤"], prefix="."))
async def unban_user_cmd(message: types.Message, bot: Bot):
    if not message.from_user:
        await message.reply("Invalid user")
        return

    try:
        if not (
            await is_admin(message.from_user.id)
            or await is_group_admin(bot, message.chat.id, message.from_user.id)
        ):
            await message.reply("No permission")
            return

        if message.chat.type == "private":
            await message.reply("Groups only")
            return

        user_info = await extract_user_info(message, bot)
        chat_id = message.chat.id
        chat_title = message.chat.title or "Unknown"
        reason = user_info["reason"] or ""
        target_ids = (
            user_info.get("user_ids", [user_info["user_id"]])
            if user_info.get("user_id")
            else []
        )

        if not target_ids:
            await message.reply("Specify user ID(s)")
            return

        results = await asyncio.gather(
            *[
                process_unban(message, bot, target_id, reason)
                for target_id in target_ids
            ],
            return_exceptions=True,
        )

        success = []
        failed = []
        for target_id, result in zip(target_ids, results):
            if isinstance(result, Exception) or not result:
                failed.append(f"{target_id}")
            else:
                success.append(result)

        message_text = ["✅ Unban"]
        if success:
            message_text.append(
                "\n".join(f"{u or 'Unknown'} ({i})" for u, i in success)
            )
        if failed:
            message_text.append(f"Failed: {', '.join(failed)}")

        await message.reply(
            "\n".join(message_text) + f"\n[{reason}][{chat_title}]", parse_mode="HTML"
        )

        if success:
            for username, target_id in success:
                await log_unban(
                    bot,
                    target_id,
                    username,
                    message.from_user.id,
                    message.from_user.username or "Unknown",
                    chat_title,
                    chat_id,
                )

            # FIX: Added await since get_groups() appears to be async
            groups = await get_groups()  # 비동기 호출로 변경 (줄 225)
            for group_id in groups.keys():
                if group_id != str(chat_id) and get_notification_status(int(group_id)):
                    try:
                        for _, target_id in success:
                            await bot.unban_chat_member(int(group_id), target_id)
                        notification = (
                            "✅ Unban\n"
                            + "\n".join(f"{u or 'Unknown'} ({i})" for u, i in success)
                            + f"\n[{chat_title}][{reason}]"
                        )
                        await bot.send_message(
                            int(group_id), notification, parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(
                            f"group_unban_failed: group_id={group_id}, error={e}"
                        )

    except Exception as e:
        logger.error(f"unban_error: chat_id={message.chat.id}, error={e}")
        await message.reply("Error occurred")


async def process_unban(
    message: types.Message, bot: Bot, target_id: int, reason: str
) -> Optional[Tuple[Optional[str], int]]:
    chat_id = message.chat.id
    if not message.from_user:
        return None

    try:
        chat_member = await bot.get_chat_member(chat_id, target_id)
        user = chat_member.user
        username = (
            user.username or f"{user.first_name} {user.last_name}".strip() or "Nickname"
        )
        if not await is_banned(target_id):
            return None

        await bot.unban_chat_member(chat_id, target_id)
        await unban_user(target_id)
        return (username, target_id)
    except Exception as e:
        logger.error(
            f"process_unban_error: chat_id={chat_id}, target_id={target_id}, error={e}"
        )
        return None
