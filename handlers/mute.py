from aiogram import Bot, Router, types
from aiogram.filters import Command
from config import logger
from database.groups import set_mute_status
from utils.permissions import is_admin, is_group_admin

router = Router()

@router.message(Command(commands=["mute"], prefix="."))
async def mute_chat(message: types.Message, bot: Bot) -> None:
    """그룹 알림 음소거 명령어 (.mute)."""
    logger.info(
        "mute_cmd_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id
    )

    try:
        if not message.from_user:
            logger.error("mute_cmd_error", error="No user information")
            await message.reply("사용자 정보를 확인할 수 없습니다.")
            return

        is_admin_user = await is_admin(message.from_user.id)
        is_group_admin_user = await is_group_admin(bot, message.chat.id, message.from_user.id)
        if not (is_admin_user or is_group_admin_user):
            logger.warning("permission_denied", user_id=message.from_user.id, chat_id=message.chat.id)
            await message.reply("권한이 없습니다.")
            return

        if message.chat.type == "private":
            logger.warning("private_chat", user_id=message.from_user.id, chat_id=message.chat.id)
            await message.reply("그룹에서만 사용 가능합니다.")
            return

        await set_mute_status(message.chat.id, True)
        await message.reply("이 그룹의 알림이 음소거되었습니다. 동작은 계속 수행됩니다.")
        logger.info("mute_enabled", chat_id=message.chat.id)
    except Exception as e:
        logger.error("mute_cmd_error", chat_id=message.chat.id, error=str(e))
        await message.reply("내부 오류가 발생했습니다.")

@router.message(Command(commands=["unmute"], prefix="."))
async def unmute_chat(message: types.Message, bot: Bot) -> None:
    """그룹 알림 음소거 해제 명령어 (.unmute)."""
    logger.info(
        "unmute_cmd_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id
    )

    try:
        if not message.from_user:
            logger.error("unmute_cmd_error", error="No user information")
            await message.reply("사용자 정보를 확인할 수 없습니다.")
            return

        is_admin_user = await is_admin(message.from_user.id)
        is_group_admin_user = await is_group_admin(bot, message.chat.id, message.from_user.id)
        if not (is_admin_user or is_group_admin_user):
            logger.warning("permission_denied", user_id=message.from_user.id, chat_id=message.chat.id)
            await message.reply("권한이 없습니다.")
            return

        if message.chat.type == "private":
            logger.warning("private_chat", user_id=message.from_user.id, chat_id=message.chat.id)
            await message.reply("그룹에서만 사용 가능합니다.")
            return

        await set_mute_status(message.chat.id, False)
        await message.reply("이 그룹의 알림 음소거가 해제되었습니다.")
        logger.info("mute_disabled", chat_id=message.chat.id)
    except Exception as e:
        logger.error("unmute_cmd_error", chat_id=message.chat.id, error=str(e))
        await message.reply("내부 오류가 발생했습니다.")
